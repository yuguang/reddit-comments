import boto
import sys, os
from boto.s3.key import Key

LOCAL_PATH = '/mnt/s3/'
START_YEAR = 2014
START_MONTH = 6

bucket_name = 'reddit-comments'

def s3_connect():
    # connect to the bucket
    conn = boto.connect_s3(os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'])
    bucket = conn.get_bucket(bucket_name)
    return bucket

def download_archive(year, month):
    if int(year) < START_YEAR or (int(year) == START_YEAR and len(month) > 3 and int(month.split('-')[1]) < START_MONTH):
        return False
    if not os.path.exists(LOCAL_PATH + year):
        os.mkdir(LOCAL_PATH + year)
    # check if file exists locally, if not: download it
    bucket = s3_connect()
    key = year + '/' + month
    results = list(bucket.list(key))
    if not len(results):
        return False
    l = results[0]
    path = LOCAL_PATH + key
    if not os.path.exists(path):
        print "=========================================="
        print "downloading to ", path
        print "=========================================="
        l.get_contents_to_filename(path)
        return path

def remove_archive(year, month):
    path = LOCAL_PATH + year + '/' + month
    os.remove(path)

if __name__ == "__main__":
    bucket = s3_connect()
    # go through the list of files
    bucket_list = bucket.list()
    for l in bucket_list:
        keyString = str(l.key)
        year, month = keyString.split('/')
        download_archive(year, month)
