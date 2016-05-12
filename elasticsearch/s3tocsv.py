from pyspark.sql import SQLContext
from pyspark import SparkContext, SparkConf
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.ml.feature import Tokenizer, RegexTokenizer

if __name__ == "__main__":
    conf = SparkConf().setAppName("comment-csv")
    sc = SparkContext(conf=conf)
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

    for i in range(8):
        year = 2008 + i
        rawDF = sqlContext.read.json("s3n://reddit-comments/{}/*".format(year), StructType(fields))
        tokenizer = Tokenizer(inputCol="body", outputCol="words")
        wordsDataFrame = tokenizer.transform(rawDF)

        commentDF = wordsDataFrame.select('author', 'created_utc', 'downs', 'edited', 'gilded', 'score', 'ups', 'body', explode(wordsDataFrame.words).alias("words")) \
                .groupBy(['author', 'created_utc', 'downs', 'edited', 'gilded', 'score', 'ups', 'body']) \
                .count()
        commentDF.select('author', 'created_utc', 'downs', 'edited', 'gilded', 'score', 'ups', 'count').write.format('com.databricks.spark.csv').save('export-{}.csv.files'.format(i))