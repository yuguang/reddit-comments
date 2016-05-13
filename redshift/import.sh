#!/usr/bin/env bash
#arn:aws:iam::632503203419:role/myRedshiftRole
spark-submit --packages com.databricks:spark-redshift_2.10:0.6.0 s3tocsv.py 2008 RC_2008-01
echo 'author,created_utc,downs,edited,gilded,score,ups,count' > header.csv
cat header.csv export-*.csv.files/* > combined.csv
#rm -rf export-*.csv.files