from pyspark.sql import SQLContext
from pyspark import SparkContext, SparkConf
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.ml.feature import Tokenizer, RegexTokenizer
import argparse, os

if __name__ == "__main__":
    conf = SparkConf().setAppName("comment-csv")
    sc = SparkContext(conf=conf)
    sc._jsc.hadoopConfiguration().set("fs.s3n.awsAccessKeyId", os.environ['AWS_ACCESS_KEY_ID'])
    sc._jsc.hadoopConfiguration().set("fs.s3n.awsSecretAccessKey", os.environ['AWS_SECRET_ACCESS_KEY'])
    sqlContext = SQLContext(sc)
    parser = argparse.ArgumentParser()
    parser.add_argument("year")
    parser.add_argument("month")
    args = parser.parse_args()
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

    year = args.year
    month = args.month
    rawDF = sqlContext.read.json("s3n://reddit-comments/{}/{}".format(year, month), StructType(fields))
    # filter out comment entries that don't have author names
    filteredDF = rawDF.filter(rawDF.author != '[deleted]')
    # tokenize comment into words
    tokenizer = Tokenizer(inputCol="body", outputCol="words")
    wordsDataFrame = tokenizer.transform(filteredDF)

    # count the number of words in comments
    commentDF = wordsDataFrame.select('author', 'created_utc', 'downs', 'edited', 'gilded', 'score', 'ups', 'body', explode(wordsDataFrame.words).alias("words")) \
            .groupBy(['author', 'created_utc', 'downs', 'edited', 'gilded', 'score', 'ups', 'body']) \
            .count()
    # write back to a redshift table
    commentDF.select('author', 'created_utc', 'downs', 'edited', 'gilded', 'score', 'ups', 'count')\
      .write \
      .format("com.databricks.spark.redshift") \
      .option("url", "jdbc:redshift://52.39.253.90:5439/redditcluster?user={}&password={}".format(os.environ['REDSHIFT_USERNAME'], os.environ['REDSHIFT_PASSWORD'])) \
      .option("dbtable", "reddit-comments") \
      .option("tempdir", "s3n://yuguang-reddit") \
      .mode("error") \
      .save()