from pyspark.sql import SQLContext
from pyspark import SparkContext, SparkConf
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.ml.feature import Tokenizer, RegexTokenizer
import argparse, os

if __name__ == "__main__":
    conf = SparkConf().setAppName("comment-csv")
    sc = SparkContext(conf=conf)
    sc._jsc.hadoopConfiguration().set("fs.s3a.awsAccessKeyId", os.environ['AWS_ACCESS_KEY_ID'])
    sc._jsc.hadoopConfiguration().set("fs.s3a.awsSecretAccessKey", os.environ['AWS_SECRET_ACCESS_KEY'])
    sqlContext = SQLContext(sc)
    fields = [StructField("archived", BooleanType(), True),
              StructField("author", StringType(), True),
              StructField("author_flair_css_class", StringType(), True),
              StructField("body", StringType(), True),
              StructField("controversiality", LongType(), True),
              StructField("created_utc", StringType(), True),
              StructField("distinguished", StringType(), True),
              StructField("downs", LongType(), True),
              StructField("edited", StringType(), True),
              StructField("gilded", LongType(), True),
              StructField("id", StringType(), True),
              StructField("link_id", StringType(), True),
              StructField("name", StringType(), True),
              StructField("parent_id", StringType(), True),
              StructField("retrieved_on", LongType(), True),
              StructField("score", LongType(), True),
              StructField("score_hidden", BooleanType(), True),
              StructField("subreddit", StringType(), True),
              StructField("subreddit_id", StringType(), True),
              StructField("ups", LongType(), True)]

    rawDF = sqlContext.read.json("s3a://reddit-comments/*", StructType(fields))
    # filter out comment entries that don't have author names
    filteredDF = rawDF.filter(rawDF.author != '[deleted]')
    # tokenize comment into words
    tokenizer = Tokenizer(inputCol="body", outputCol="words")
    wordsDataFrame = tokenizer.transform(filteredDF)

    # count the number of words in comments
    commentDF = wordsDataFrame.select('author', 'subreddit', 'created_utc', 'downs', 'gilded', 'score', 'ups', 'body', explode(wordsDataFrame.words).alias("words")) \
            .groupBy(['author', 'subreddit', 'created_utc', 'downs', 'gilded', 'score', 'ups', 'body']) \
            .count()
    # write back to a redshift table
    commentDF.select('author', 'subreddit', 'created_utc', 'downs', 'gilded', 'score', 'ups', 'count')\
      .write \
      .format("com.databricks.spark.redshift") \
      .option("url", "jdbc:redshift://{}/dev?user={}&password={}".format(os.environ['REDSHIFT_ENDPOINT'], os.environ['REDSHIFT_USERNAME'], os.environ['REDSHIFT_PASSWORD'])) \
      .option("dbtable", "reddit_comments") \
      .option("tempdir", "s3a://yuguang-reddit") \
      .mode("error") \
      .save()