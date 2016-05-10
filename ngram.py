import json
import boto.s3
import nltk, re
from pyspark.sql import Row
from pyspark.ml.feature import StopWordsRemover
from pyspark.ml.feature import NGram
from pyspark.ml.feature import Tokenizer, RegexTokenizer
from pyspark import SparkContext, SparkConf, StorageLevel
from pyspark.sql import SQLContext
from timeconverter import *
from storage import ElasticSearch

PARTITIONS = 500
THRESHOLD = 100

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
    text = s.lower()
    for pattern in [Url,ShortUrl,Number,Image,TagsLt,TagsGt,TagsAmps,TagsQuote,TagsTilde,TagsDash,TagsHtml]:
        text = re.sub(re.compile(pattern), '*', text)
    return filter(lambda x: not(x in '.,?![]:;\/\\()"{}-$%^&*'), text)

if __name__ == "__main__":
    timeConverter = TimeConverter()
    conf = SparkConf().setAppName("reddit")
    conf.set('spark.serializer', 'org.apache.spark.serializer.KryoSerializer')
    sc = SparkContext(conf=conf, pyFiles=['utils.py', 'timeconverter.py', 'storage.py'])
    sqlContext = SQLContext(sc)
    # read and parse reddit data
    data_rdd = sc.textFile("s3n://reddit-comments/2007/RC_2007-10")
    comments = data_rdd.filter(lambda x: len(x) > 0).map(lambda x: json.loads(x.encode('utf8')))
    # split comments into sentences
    sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')
    rdd = comments.flatMap(lambda comment: [[comment['created_utc'], comment['subreddit'], cleanSentence(sentence)] for sentence in sent_detector.tokenize(comment['body'].strip())])
    # tokenize into words
    sentenceDataFrame = sqlContext.createDataFrame(rdd, ["date","subreddit", "sentence"])
    tokenizer = Tokenizer(inputCol="sentence", outputCol="words")
    wordsDataFrame = tokenizer.transform(sentenceDataFrame)
    rdd.unpersist()
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
        ngramCounts = ngramRDD.map(lambda x: ((x['date'], x['subreddit'], x['ngram']), 1)).reduceByKey(lambda x, y: x + y, PARTITIONS) \
                    .map(lambda x: (x[0][0], [x[0][1], x[0][2], x[1]]))
        # calculate ngram totals by day
        ngramTotals = ngramRDD.map(lambda x: (x['date'], 1)).reduceByKey(lambda x, y: x + y, PARTITIONS)

        db = ElasticSearch()
        ngramCounts.filter(lambda x: x[3] > THRESHOLD).foreachPartition(lambda x: db.saveNgramCounts(ngram_length, x))
        ngramTotals.filter(lambda x: x[1] > THRESHOLD).foreachPartition(lambda x: db.saveTotalCounts(ngram_length, x))

