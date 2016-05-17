import json
import boto.s3
from pyspark import SparkContext, SparkConf, StorageLevel
from pyspark.sql import SQLContext
from timeconverter import TimeConverter
from download import *
from storage import Cassandra
from tokenizer import SentenceTokenizer

PARTITIONS = 20
START_YEAR = 2007
START_MONTH = 9

def foreign_list():
    file = open("foreign.txt",'r')
    blacklist = []
    for line in file:
        blacklist.append(line.rstrip().lower())
    file.close()
    return set(blacklist)

def subreddit_list(slice):
    slice = int(slice)
    file = open("subreddits.txt",'r')
    whitelist = []
    for line in file:
        whitelist.append(line.rstrip().lower())
    file.close()
    return set(whitelist[:slice])

if __name__ == "__main__":
    timeConverter = TimeConverter()
    conf = SparkConf().setAppName("reddit")
    conf.set('spark.serializer', 'org.apache.spark.serializer.KryoSerializer')
    sc = SparkContext(conf=conf, pyFiles=['tokenizer.py', 'timeconverter.py', 'storage.py', 'download.py'])
    sqlContext = SQLContext(sc)
    tokenizer = SentenceTokenizer()

    conn = boto.s3.connect_to_region('us-west-2')
    bucket = conn.get_bucket('reddit-comments')

    folders = bucket.list("","/*/")
    folders = filter(lambda x: len(x) > 1 and len(x[1]) > 0, map(lambda x: x.name.split('/'), folders))[::-1]

    foreign_subreddits = foreign_list()
    for year, month in folders:
        y = int(year)
        m = int(month.split('-')[1])
        if y < START_YEAR or (y == START_YEAR and len(month) > 3 and m < START_MONTH):
            continue
        print "=========================================="
        print "reading reddit comments for ", year, month
        print "=========================================="
        # read and parse reddit data
        data_rdd = sc.textFile("s3a://reddit-comments/{}/{}".format(year, month))
        # start with some of the most popular subreddits and add more for each year, since only the percentage counts for ngrams matter
        popular_subreddits = subreddit_list((2015 - y + (12 - m)/float(12))*300 + 300)
        comments = data_rdd.filter(lambda x: len(x) > 0) \
                           .map(lambda x: json.loads(x.encode('utf8'))) \
                           .filter(lambda x: not(x['subreddit'].lower() in foreign_subreddits)) \
                           .filter(lambda x: x['subreddit'].lower() in popular_subreddits) \
                           .map(lambda comment: (timeConverter.toDate(comment['created_utc']), tokenizer.segment_text(comment['body'])))
        comments.repartition(PARTITIONS)
        comments.persist(StorageLevel.MEMORY_ONLY)

        for ngram_length in range(1,3):
            comments_rdd = comments.flatMap(lambda comment: [[comment[0], ngram] for ngram in tokenizer.ngrams(comment[1], ngram_length)])
            # generate all ngrams
            ngramDataFrame =  sqlContext.createDataFrame(comments_rdd, ["date", "ngram"])
            comments_rdd.unpersist()
            ngramDataFrame.persist(StorageLevel.MEMORY_ONLY)

            # count the occurrence of each ngram by date for all of subreddit
            ngramCounts = ngramDataFrame.map(lambda x: ((x['date'], x['ngram']), 1)).reduceByKey(lambda x, y: x + y, PARTITIONS) \
                        .map(lambda x: (x[0][0], [x[0][1], x[1]]))
            ngramCounts.persist(StorageLevel.MEMORY_ONLY)
            # ex. (u'2007-10-28', [u'000 metric', 1])

            # calculate ngram totals by day
            ngramTotals = ngramDataFrame.map(lambda x: (x['date'], 1)).reduceByKey(lambda x, y: x + y, PARTITIONS)
            ngramDataFrame.unpersist()
            ngramTotals.persist(StorageLevel.MEMORY_ONLY)
            # ex. (u'2007-10-22', 68976)

            # find the total for a day
            totalSum = ngramTotals.first()[1]
            db = Cassandra()

            if ngram_length > 1:
                THRESHOLD = 5
            else:
                THRESHOLD = 50

            # add total counts for the day to each ngram row
            resultRDD = ngramTotals.join(ngramCounts.filter(lambda x: x[1][1] > THRESHOLD and x[1][1] > int(1e-6 * totalSum)))\
                .map(lambda x: (x[0], x[1][1][0], x[1][1][1], x[1][0]))
            resultRDD.foreachPartition(lambda x: db.saveNgramCounts(ngram_length, x))

            ngramCounts.unpersist()
            ngramTotals.unpersist()

        comments.unpersist()


