import json
from pyspark import SparkContext, SparkConf, StorageLevel
import boto
import boto.s3
from utils import findUrlDomain

if __name__ == "__main__":
    conf = SparkConf().setAppName("reddit")
    sc = SparkContext(conf=conf, pyFiles=['utils.py'])
    conn = boto.s3.connect_to_region('us-west-2')
    bucket = conn.get_bucket('reddit-comments')

    folders = bucket.list("","/*/")
    folders = filter(lambda x: len(x) > 1 and len(x[1]) > 0, map(lambda x: x.name.split('/'), folders))

    THRESHOLD = 10
    # loop through the s3 key for each month
    for year, month in folders:
        data_rdd = sc.textFile("s3n://reddit-comments/{}/{}".format(year, month))
        comments = data_rdd.filter(lambda x: len(x) > 0).map(lambda x: json.loads(x.encode('utf8')))
        comments.persist(StorageLevel.MEMORY_AND_DISK_SER)

        # find the popularity of domains shared on reddit
        domainCounts = comments.flatMap(lambda x: findUrlDomain(x['body'])).map(lambda x: (x, 1)).reduceByKey(lambda x, y: x + y)

        def saveDomains(month, rdd):
            # connect to database from each worker
            from models import Domain, db
            db.connect()
            for line in rdd:
                d = Domain(month=month.replace('RC_', ''), count=line[1], name=line[0])
                d.save()

        domainCounts.filter(lambda x: x[1] > THRESHOLD).foreachPartition(lambda x: saveDomains(month, x))

        # filter out reddit.com comments and count comments in other subreddits
        subredditCounts = comments.filter(lambda x: x['subreddit'] != 'reddit.com') \
            .map(lambda x: (x['subreddit'], 1)) \
            .reduceByKey(lambda x, y: x + y)
        #subredditCounts.filter(lambda x: x[1] > THRESHOLD).foreachPartition(lambda x: saveSubredditCounts(month, 'subreddits', x))
        comments.unpersist()