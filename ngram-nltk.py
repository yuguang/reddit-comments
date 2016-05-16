import json
import boto.s3
import time
import argparse
import os
import nltk, re
from pyspark.sql import Row
from pyspark.ml.feature import StopWordsRemover
from pyspark.ml.feature import NGram
from pyspark.ml.feature import Tokenizer, RegexTokenizer
from pyspark import SparkContext, SparkConf, StorageLevel
from pyspark.sql import SQLContext
from timeconverter import TimeConverter
from download import *
from storage import ElasticSearch, Sqlite, Mysql, Cassandra
from tokenizer import SentenceTokenizer

PARTITIONS = 100
THRESHOLD = 100
START_YEAR = 2009
START_MONTH = 4

nodes = []

keyspace = "reddit"

def foreign_list():
    file = open("foreign.txt",'r')
    blacklist = []
    for line in file:
        blacklist.append(line.rstrip().lower())
    file.close()
    return set(blacklist)

def subreddit_list():
    file = open("subreddits.txt",'r')
    whitelist = []
    for line in file:
        whitelist.append(line.rstrip().lower())
    file.close()
    return set(whitelist)

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
    folders = filter(lambda x: len(x) > 1 and len(x[1]) > 0, map(lambda x: x.name.split('/'), folders))
    # folders = ['2007/RC_2007-10'.split('/')]

    foreign_subreddits = foreign_list()
    popular_subreddits = subreddit_list()
    for year, month in folders:
        if int(year) < START_YEAR or (int(year) == START_YEAR and len(month) > 3 and int(month.split('-')[1]) < START_MONTH):
            continue
        print "=========================================="
        print "reading reddit comments for ", year, month
        print "=========================================="
        # read and parse reddit data
        data_rdd = sc.textFile("s3a://reddit-comments/{}/{}".format(year, month))
        comments = data_rdd.filter(lambda x: len(x) > 0) \
                           .map(lambda x: json.loads(x.encode('utf8'))) \
                           .filter(lambda x: not(x['subreddit'].lower() in foreign_subreddits)) \
                           .filter(lambda x: x['subreddit'].lower() in popular_subreddits) \
                           .map(lambda comment: (timeConverter.toDate(comment['created_utc']), tokenizer.segment_text(comment['body'])))
        comments.persist(StorageLevel.MEMORY_AND_DISK_SER)

        for ngram_length in range(1,5):
            comments_rdd = comments.flatMap(lambda comment: [[comment[0], comment[1], ngram] for ngram in tokenizer.ngrams(comment[2], ngram_length)])
            # make sure rdd has at least one item
            if comments_rdd.countApprox(60 * 2, .9) < 1:
                continue
            # generate all ngrams
            ngramDataFrame =  sqlContext.createDataFrame(comments_rdd, ["date", "ngram"])

            # count the occurrence of each ngram by date for all of subreddit
            ngramCounts = ngramDataFrame.map(lambda x: ((x['date'], x['ngram']), 1)).reduceByKey(lambda x, y: x + y, PARTITIONS) \
                        .map(lambda x: (x[0][0], [x[0][1], x[1]]))
            # (u'2007-10-28', [u'000 metric', 1])

            # calculate ngram totals by day
            ngramTotals = ngramDataFrame.map(lambda x: (x['date'], 1)).reduceByKey(lambda x, y: x + y, PARTITIONS)
            # (u'2007-10-22', 68976)
            totalSum = ngramTotals.map(lambda x: x[1]).sum()
            db = Cassandra()
            resultRDD = ngramTotals.join(ngramCounts.filter(lambda x: x[1][1] > int(1e-7 * totalSum)))\
                .map(lambda x: (x[0], x[1][1][0], x[1][1][1], x[1][0]))
            resultRDD.foreachPartition(lambda x: db.saveNgramCounts(ngram_length, x))

            ngramCounts.unpersist()
            ngramTotals.unpersist()

        comments.unpersist()


