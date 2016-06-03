from pyspark import SparkContext, SparkConf, StorageLevel
from pyspark.ml.feature import StopWordsRemover
from pyspark.ml.feature import Tokenizer
from pyspark.sql import SQLContext
from pyspark.sql.functions import desc, explode
from pyspark.sql.types import *
from utils import saveWordCloud
from storage import Sqlite

PARTITIONS = 500
THRESHOLD = 50

if __name__ == "__main__":
    conf = SparkConf().setAppName("reddit")
    conf.set('spark.serializer', 'org.apache.spark.serializer.KryoSerializer')
    conf.set('spark.local.dir', '/mnt/work')
    conf.set('spark.driver.maxResultSize', '12g')
    sc = SparkContext(conf=conf)
    sqlContext = SQLContext(sc)
    fields = [StructField("subreddit", StringType(), True),
          StructField("body", StringType(), True)]
    rawDF = sqlContext.read.json("file:///mnt/s3/2015/*", StructType(fields))
    # split comments into words
    tokenizer = Tokenizer(inputCol="body", outputCol="words")
    wordsDataFrame = tokenizer.transform(rawDF)

    remover = StopWordsRemover(inputCol="words", outputCol="filtered")
    filteredDataFrame = remover.transform(wordsDataFrame)
    # explode terms into individual rows
    termDataFrame = filteredDataFrame.select(['subreddit', explode(filteredDataFrame.filtered).alias("term")])
    # group by subreddit and term, then count occurence of term in subreddits
    countsDataFrame = termDataFrame.groupBy(['subreddit', 'term']).count()

    db =  Sqlite()
    countsDataFrame.select(['subreddit', 'term', 'count']).filter('count > {}'.format(THRESHOLD)).foreachPartition(db.saveSubredditWords)