#!/usr/bin/env bash
spark-submit --jars RedshiftJDBC41-1.1.13.1013.jar --packages com.databricks:spark-redshift_2.10:0.6.0 --executor-memory 2g --driver-memory 10g comment_attributes.py
#echo 'author,created_utc,downs,edited,gilded,score,ups,count' > header.csv
#cat header.csv export-*.csv.files/* > combined.csv
#rm -rf export-*.csv.files