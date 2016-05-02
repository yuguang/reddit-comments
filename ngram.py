import json
import datetime
import time
import argparse
import os
from pyspark.ml.feature import StopWordsRemover
from pyspark.ml.feature import NGram

dateformat = '%Y-%m-%d'
def ConvertToYearDate(x):
    return time.strftime(dateformat, time.gmtime(int(x)))

# read and parse reddit data
data_rdd = sc.textFile("s3n://reddit-comments/2015/*")
jsonformat = data_rdd.filter(lambda x: len(x) > 0).map(lambda x: json.loads(x.encode('utf8')))
etlDataMain = jsonformat.map(lambda x: [x['body'].split(' '), ConvertToYearDate(x['created_utc']), x['subreddit']])
etlDataMain.persist(StorageLevel.MEMORY_AND_DISK_SER)

sentenceData = sqlContext.createDataFrame(etlDataMain, ["body", "date","subreddit"])

# remove words that occur frequently such as "a", "the"
remover = StopWordsRemover(inputCol="body", outputCol="filtered")
remover.transform(sentenceData).show(truncate=False)

# generate all 3-grams
ngram = NGram(n=3, inputCol="filtered", outputCol="ngrams")
ngramDataFrame = ngram.transform(remover.transform(sentenceData))
for ngrams_label in ngramDataFrame.select("ngrams", "filtered").take(3):
    print(ngrams_label)