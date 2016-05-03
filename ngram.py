import json
import time
import argparse
import os
import nltk, re
from pyspark.sql import Row
from pyspark.ml.feature import StopWordsRemover
from pyspark.ml.feature import NGram
from pyspark.ml.feature import Tokenizer, RegexTokenizer
from timeconverter import *

CASSANDRA_WAIT = 5
QUERY_WAIT = 0.001

nodes = []

keyspace = "reddit"

def cleanSentence(s):    
    Url = '(hf=)?[\(\[]?(http?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)*\/?[\)\]]'
    ShortUrl = '[\(\[]?(http://(bit\.ly|t\.co|lnkd\.in|tcrn\.ch)\S*)\b[\)\]]'
    Number = '^[0-9]+([,.][0-9]+)?$'
    Image = '<img([^>]*[^/])>'
    TagsLt = '&gt;'
    TagsGt = '&gt;'
    TagsAmps = '&amp;'
    TagsQuote = '&quot;'
    TagsTilde = '&tilde;'
    TagsDash = '&mdash;'
    TagsHtml = '&\w;'
    pattern = '|'.join([Url,ShortUrl,Number,Image,TagsLt,TagsGt,TagsAmps,TagsQuote,TagsTilde,TagsDash,TagsHtml])
    text = re.sub(re.compile(pattern), '*', s.lower())
    return text.rstrip('.')
    
def saveNgrams(ngramcount, rdditer, table, async=True):
    from cassandra.cluster import Cluster
    CassandraCluster = Cluster(nodes)

    success = False
    #try to reconnect if connection is down
    while not success:
        try:
            session = CassandraCluster.connect(keyspace)
            session.default_timeout = 60
            success = True
        except:
            success = False
            time.sleep(CASSANDRA_WAIT)

    query = "INSERT INTO %s (ngram, subreddit, time_bucket, date, count, percentage) VALUES (?, ?, ?, ?, ? ,?)" %(table,)
    prepared = session.prepare(query)

    timeConverter = TimeConverter()
    for datatuple in rdditer:
        # ('2007-10-23', (126827, [u'politics', u'term terrorism clearly', 1]))
        date = datatuple[0]
        time_bucket = timeConverter.toTimebucket(date)
        
        total = float(datatuple[1][0])
        subreddit = str(datatuple[1][0][0])
        ngram = str(datatuple[1][0][1])
        count = int(datatuple[1][0][2])
        percentage = float(count) / total

        bound = prepared.bind((ngram, subreddit, time_bucket, date, count, percentage))
        if async:
            session.execute_async(bound)
            time.sleep(QUERY_WAIT)
        else:
            session.execute(bound)

    session.shutdown()

if __name__ == "__main__":
    timeConverter = TimeConverter()
    # read and parse reddit data
    data_rdd = sc.textFile("s3n://reddit-comments/2007/RC_2007-10")
    comments = data_rdd.filter(lambda x: len(x) > 0).map(lambda x: json.loads(x.encode('utf8')))
    comments.persist(StorageLevel.MEMORY_AND_DISK_SER)
    # split comments into sentences
    sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
    rdd = comments.flatMap(lambda comment: [[comment['created_utc'], comment['subreddit'], cleanSentence(sentence)] for sentence in sent_detector.tokenize(comment['body'].strip())])

    sentenceDataFrame = sqlContext.createDataFrame(rdd, ["date","subreddit", "sentence"])
    tokenizer = Tokenizer(inputCol="sentence", outputCol="words")
    wordsDataFrame = tokenizer.transform(sentenceDataFrame)
    #for words_label in wordsDataFrame.select("words").take(3):
    #    print(words_label)

    # remove words that occur frequently such as "a", "the"
    remover = StopWordsRemover(inputCol="words", outputCol="filtered")
    wordsDataFrame = remover.transform(wordsDataFrame)

    for ngram_length in range(1,3):
        # generate all ngrams
        ngram = NGram(n=ngram_length, inputCol="filtered", outputCol="ngrams")
        ngramDataFrame = ngram.transform(wordsDataFrame)
    #    for ngrams_label in ngramDataFrame.select("ngrams", "filtered").take(3):
    #        print(ngrams_label)

        # convert timestamps to dates for each ngram
        ngramRDD = ngramDataFrame.map(lambda comment: Row(date=timeConverter.toDate(comment['date']), subreddit=comment['subreddit'], ngrams=comment['ngrams'])) \
                    .flatMap(lambda comment: [Row(date=comment['date'], subreddit=comment['subreddit'], ngram=ngram) for ngram in comment['ngrams']])

        # count the occurrence of each ngram by date and subreddit
        ngramCounts = ngramRDD.map(lambda x: ((x['date'], x['subreddit'], x['ngram']), 1)).reduceByKey(lambda x, y: x + y) \
                    .map(lambda x: (x[0][0], [x[0][1], x[0][2], x[1]]))
        # calculate ngram totals by day
        ngramTotals = ngramRDD.map(lambda x: (x['date'], 1)).reduceByKey(lambda x, y: x + y)

        ngramTotals.join(ngramCounts.filter(lambda x: x[1][2] > 1)).foreachPartition(lambda x: saveNgrams(ngram_length, 'ngrams', x))

