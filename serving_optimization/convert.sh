#!/usr/bin/env bash
# export data from sqlite development database to csv
sqlite3 ../project/db.sqlite3 <<EOF
.mode csv
.headers on
.out subreddit.csv
select * from reddit_subreddit;
EOF
# read csv in Spark and output in two column [domain, timeseries] format
spark-submit --executor-memory 2g --driver-memory 2g --packages com.databricks:spark-csv_2.10:1.4.0 optimize_timeseries.py subreddit.csv
cat converted.csv.files/* > subreddit.opt.csv
rm -rf converted.csv.files

sqlite3 ../project/db.sqlite3 <<EOF
.mode csv
.headers on
.out domain.csv
select * from reddit_domain;
EOF
spark-submit --executor-memory 2g --driver-memory 2g --packages com.databricks:spark-csv_2.10:1.4.0 optimize_timeseries.py domain.csv
cat converted.csv.files/* > domain.opt.csv
rm -rf converted.csv.files
