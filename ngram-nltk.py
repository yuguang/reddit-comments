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
from timeconverter import *
from download import *
from storage import ElasticSearch
from tokenizer import SentenceTokenizer

PARTITIONS = 500
THRESHOLD = 100

nodes = []

keyspace = "reddit"

def foreign_list():
    file = open("foreign.txt",'r')
    blacklist = []
    for line in file:
        blacklist.append(line.rstrip().lower())
    file.close()
    return blacklist

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
    for year, month in folders:
        # download the file to be parsed
        path = download_archive(year, month)
        if not path:
            continue
        # read and parse reddit data
        data_rdd = sc.textFile("file://{}".format(path))
        comments = data_rdd.filter(lambda x: len(x) > 0) \
                           .map(lambda x: json.loads(x.encode('utf8'))) \
                           .filter(lambda x: not(x['subreddit'].lower() in foreign_subreddits)) \
                           .map(lambda comment: (timeConverter.toDate(comment['created_utc']), comment['subreddit'], tokenizer.segment_text(comment['body'])))
        comments.persist(StorageLevel.MEMORY_AND_DISK_SER)

        for ngram_length in range(1,5):
            # generate all ngrams
            ngramDataFrame =  sqlContext.createDataFrame(comments.flatMap(lambda comment: [[comment[0], comment[1], ngram] for ngram in tokenizer.ngrams(comment[2], ngram_length)]), ["date","subreddit", "ngram"])

            # count the occurrence of each ngram by date and subreddit
            ngramCounts = ngramDataFrame.map(lambda x: ((x['date'], x['subreddit'], x['ngram']), 1)).reduceByKey(lambda x, y: x + y, PARTITIONS) \
                        .map(lambda x: (x[0][0], x[0][1], x[0][2], x[1]))
            # for line in ngramCounts.take(3):
            #     print line
            # (u'2007-10-28', u'reddit.com', u'000 metric', 1)

            # calculate ngram totals by day
            ngramTotals = ngramDataFrame.map(lambda x: (x['date'], 1)).reduceByKey(lambda x, y: x + y, PARTITIONS)
            # for line in ngramTotals.take(3):
            #     print line
            # (u'2007-10-22', 68976)

            db = ElasticSearch()
            ngramCounts.filter(lambda x: x[3] > THRESHOLD).foreachPartition(lambda x: db.saveNgramCounts(ngram_length, x))
            ngramCounts.unpersist()
            ngramTotals.filter(lambda x: x[1] > THRESHOLD).foreachPartition(lambda x: db.saveTotalCounts(ngram_length, x))
            ngramTotals.unpersist()

        comments.unpersist()
        remove_archive(year, month)


