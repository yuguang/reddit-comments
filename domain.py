import json, time
from pyspark import SparkContext, SparkConf, StorageLevel
import boto
import boto.s3
from utils import findUrlDomain
from storage import Mysql
from download import *

S3_WAIT = 100
PARTITIONS = 500

if __name__ == "__main__":
    conf = SparkConf().setAppName("reddit")
    conf.set('spark.serializer', 'org.apache.spark.serializer.KryoSerializer')
    sc = SparkContext(conf=conf, pyFiles=['utils.py', 'storage.py', 'download.py'])
    conn = boto.s3.connect_to_region('us-west-2')
    bucket = conn.get_bucket('reddit-comments')

    folders = bucket.list("","/*/")
    folders = filter(lambda x: len(x) > 1 and len(x[1]) > 0, map(lambda x: x.name.split('/'), folders))

    db = Mysql()
    THRESHOLD = 10
    # loop through the s3 key for each month
    for year, month in folders:
        path = download_archive(year, month)
        data_rdd = sc.textFile("file://{}".format(path))
        comments = data_rdd.filter(lambda x: len(x) > 0).map(lambda x: json.loads(x.encode('utf8')))

        # find the popularity of domains shared on reddit
        domainCounts = comments.flatMap(lambda x: findUrlDomain(x['body'])).map(lambda x: (x, 1)).reduceByKey(lambda x, y: x + y, PARTITIONS)

        # filter out domains that have only a few visits and save
        domainCounts.filter(lambda x: x[1] > THRESHOLD).foreachPartition(lambda x: db.saveDomains(month, x))

        # filter out reddit.com comments and count comments in other subreddits
        subredditCounts = comments.filter(lambda x: x['subreddit'] != 'reddit.com') \
            .map(lambda x: (x['subreddit'], 1)) \
            .reduceByKey(lambda x, y: x + y, PARTITIONS)

        # filter out subreddits that only have a few comments and save
        subredditCounts.filter(lambda x: x[1] > THRESHOLD).foreachPartition(lambda x: db.saveSubredditCounts(month, x))
        remove_archive(year, month)