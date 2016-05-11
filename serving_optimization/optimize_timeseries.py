from pyspark.sql import SQLContext
from pyspark import SparkContext, SparkConf
from pyspark.sql.types import *
from pyspark.sql.functions import *
from pyspark.ml.feature import Tokenizer, RegexTokenizer
from pyspark.sql.functions import col, when, max
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="A CSV file with header, one datum per line")
    args = parser.parse_args()
    conf = SparkConf().setAppName("comment-csv")
    sc = SparkContext(conf=conf)
    sqlContext = SQLContext(sc)
    fields = [StructField("id", LongType(), True),
              StructField("month", StringType(), True),
              StructField("count", LongType(), True),
              StructField("name", StringType(), True),]

    df = sqlContext.read \
        .format('com.databricks.spark.csv') \
        .options(header='true') \
        .load(args.file, schema=StructType(fields))

    months = sorted(df.select("month")
        .distinct()
        .map(lambda row: row[0])
        .collect())

    cols = [when(col("month") == m, col("count")).otherwise(None).alias(m)
        for m in  months]
    maxs = [max(col(m)).alias(m) for m in months]

    series = (df
        .select(col("name"), *cols)
        .groupBy("name")
        .agg(*maxs)
        .na.fill(0))

    series.select("name", concat_ws(",", *months).alias("timeseries")).write.format('com.databricks.spark.csv').save('domain.files')