import boto
import sys, os
from boto.s3.key import Key

LOCAL_PATH = '/mnt/s3/'

bucket_name = 'reddit-comments'
# connect to the bucket
conn = boto.connect_s3(os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'])
bucket = conn.get_bucket(bucket_name)
# go through the list of files
bucket_list = bucket.list()
for l in bucket_list:
    keyString = str(l.key)
    year, month = keyString.split('/')
    if not os.path.exists(LOCAL_PATH + year):
        os.mkdir(LOCAL_PATH + year)
    # check if file exists locally, if not: download it
    if not os.path.exists(LOCAL_PATH + keyString):
        l.get_contents_to_filename(LOCAL_PATH + keyString)
