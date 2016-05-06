import json, time
from pyspark import SparkContext, SparkConf, StorageLevel
import boto
import boto.s3
from utils import findUrlDomain
from storage import Mysql

S3_WAIT = 100
PARTITIONS = 500

if __name__ == "__main__":
    conf = SparkConf().setAppName("reddit")
    sc = SparkContext(conf=conf, pyFiles=['utils.py'])
    conn = boto.s3.connect_to_region('us-west-2')
    bucket = conn.get_bucket('reddit-comments')

    folders = bucket.list("","/*/")
    folders = filter(lambda x: len(x) > 1 and len(x[1]) > 0, map(lambda x: x.name.split('/'), folders))

    db = Mysql()
    THRESHOLD = 10
    # loop through the s3 key for each month
    for year, month in folders:
        success = False
        # try to reconnect if connection is reset
        while not success:
            try:
                data_rdd = sc.textFile("s3n://reddit-comments/{}/{}".format(year, month))
                success = True
            except:
                success = False
                time.sleep(S3_WAIT)
        comments = data_rdd.filter(lambda x: len(x) > 0).map(lambda x: json.loads(x.encode('utf8')))
        comments.repartition(PARTITIONS)
        comments.persist(StorageLevel.MEMORY_AND_DISK_SER)

        # find the popularity of domains shared on reddit
        domainCounts = comments.flatMap(lambda x: findUrlDomain(x['body'])).map(lambda x: (x, 1)).reduceByKey(lambda x, y: x + y, PARTITIONS)

        domainCounts.filter(lambda x: x[1] > THRESHOLD).foreachPartition(lambda x: db.saveDomains(month, x))

        # filter out reddit.com comments and count comments in other subreddits
        subredditCounts = comments.filter(lambda x: x['subreddit'] != 'reddit.com') \
            .map(lambda x: (x['subreddit'], 1)) \
            .reduceByKey(lambda x, y: x + y, PARTITIONS)
        subredditCounts.filter(lambda x: x[1] > THRESHOLD).foreachPartition(lambda x: db.saveSubredditCounts(month, x))
        comments.unpersist()