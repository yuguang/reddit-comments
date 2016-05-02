import json
import datetime
import time
import argparse
import os
import nltk
from pyspark.sql import Row
from pyspark.ml.feature import StopWordsRemover
from pyspark.ml.feature import NGram
from pyspark.ml.feature import Tokenizer, RegexTokenizer

dateformat = '%Y-%m-%d'
def ConvertToDate(x):
    return time.strftime(dateformat, time.gmtime(int(x)))

# read and parse reddit data
data_rdd = sc.textFile("s3n://reddit-comments/2007/RC_2007-10")
comments = data_rdd.filter(lambda x: len(x) > 0).map(lambda x: json.loads(x.encode('utf8')))
comments.persist(StorageLevel.MEMORY_AND_DISK_SER)
# split comments into sentences
sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
rdd = comments.flatMap(lambda comment: [[comment['created_utc'], comment['subreddit'], sentence] for sentence in sent_detector.tokenize(comment['body'].strip())])

sentenceDataFrame = sqlContext.createDataFrame(rdd, ["date","subreddit", "sentence"])
tokenizer = Tokenizer(inputCol="sentence", outputCol="words")
wordsDataFrame = tokenizer.transform(sentenceDataFrame)
for words_label in wordsDataFrame.select("words").take(3):
    print(words_label)

# remove words that occur frequently such as "a", "the"
remover = StopWordsRemover(inputCol="words", outputCol="filtered")
wordsDataFrame = remover.transform(wordsDataFrame)

for ngram_length in range(1,3):
    # generate all ngrams
    ngram = NGram(n=ngram_length, inputCol="filtered", outputCol="ngrams")
    ngramDataFrame = ngram.transform(wordsDataFrame)
    for ngrams_label in ngramDataFrame.select("ngrams", "filtered").take(3):
        print(ngrams_label)
        
    # convert timestamps to dates for each ngram
    ngramRDD = ngramDataFrame.map(lambda comment: Row(date=ConvertToDate(comment['date']), subreddit=comment['subreddit'], ngrams=comment['ngrams'])) \
                .flatMap(lambda comment: [Row(date=comment['date'], subreddit=comment['subreddit'], ngram=ngram) for ngram in comment['ngrams']])

    # count the occurrence of each ngram by date and subreddit
    ngramCounts = ngramRDD.map(lambda x: ('{}::{}'.format(x['date'], x['subreddit']), 1)).reduceByKey(lambda x, y: x + y)
    print ngramCounts.first()
    # calculate ngram totals by day
    ngramTotals = ngramRDD.map(lambda x: (x['date'], 1)).reduceByKey(lambda x, y: x + y)
    print ngramTotals.first()
