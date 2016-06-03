from pyspark import SparkContext, SparkConf, StorageLevel
from pyspark.ml.feature import StopWordsRemover
from pyspark.ml.feature import Tokenizer
from pyspark.sql import SQLContext
from pyspark.sql.functions import desc, explode
from pyspark.sql.types import *
from utils import saveWordCloud
from storage import Sqlite

PARTITIONS = 500
THRESHOLD = 1000

if __name__ == "__main__":
    conf = SparkConf().setAppName("reddit")
    conf.set('spark.serializer', 'org.apache.spark.serializer.KryoSerializer')
    conf.set('spark.local.dir', '/mnt/work')
    conf.set('spark.driver.maxResultSize', '12g')
    sc = SparkContext(conf=conf)
    sqlContext = SQLContext(sc)
    fields = [StructField("subreddit", StringType(), True),
          StructField("body", StringType(), True)]
    rawDF = sqlContext.read.json("file:///mnt/s3/2015/RC_2015-01", StructType(fields))
    # split comments into words
    tokenizer = Tokenizer(inputCol="body", outputCol="words")
    wordsDataFrame = tokenizer.transform(rawDF)

    remover = StopWordsRemover(inputCol="words", outputCol="filtered")
    filteredDataFrame = remover.transform(wordsDataFrame)
    # explode terms into individual rows
    termDataFrame = filteredDataFrame.select(['subreddit', explode(filteredDataFrame.filtered).alias("term")])
    # group by subreddit and term, then count occurence of term in subreddits
    countsDataFrame = termDataFrame.groupBy(['subreddit', 'term']).count()

    # get the subreddits that have more than 1000 terms
    subreddits = set(termDataFrame.groupBy('subreddit').count().filter(lambda x: x['count'] > THRESHOLD)\
        .flatmap(lambda x: x['subreddit']).collect())

    db =  Sqlite()
    countsDataFrame.select(['subreddit', 'term', 'count']).filter(lambda x: x['subreddit'] in subreddits).foreachPartiton(db.saveSubredditWords)