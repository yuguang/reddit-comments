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
    fields = [StructField("date", StringType(), True),
              StructField("name", StringType(), True),
              StructField("count", LongType(), True),
              StructField("total", LongType(), True),
              StructField("length", IntegerType(), True),
              StructField("percentage", FloatType(), True),]

    df = sqlContext.read \
        .format('com.databricks.spark.csv') \
        .options(header='false') \
        .load(args.file, schema=StructType(fields))

    # calculate the totals summed across all dates
    countDF = df.groupBy('name').agg({"count": "sum"}).withColumnRenamed('sum(count)', 'total')

    # read from the column dates
    dates = sorted(df.select("date")
        .distinct()
        .map(lambda row: row[0])
        .collect())

    # find the counts for each date
    cols = [when(col("date") == m, col("percentage")).otherwise(None).alias(m)
        for m in  dates]
    maxs = [max(col(m)).alias(m) for m in dates]

    # reformat dataframe
    series = (df
        .select(col("name"), *cols)
        .groupBy("name")
        .agg(*maxs)
        .na.fill(0))

    compressedTimeseries = series.select("name", concat_ws(",", *dates).alias("timeseries"))

    # add totals to timeseries table
    resultDF = compressedTimeseries.join(countDF, 'name', 'inner')

    resultDF.write.format('com.databricks.spark.csv').save('converted.csv.files')