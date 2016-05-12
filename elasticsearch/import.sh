#!/usr/bin/env bash
spark-submit --packages com.databricks:spark-csv_2.10:1.4.0 s3tocsv.py
cat export-*.csv.files/* > combined.csv
#rm -rf export-*.csv.files
orc-csv -u $ORC_API_KEY -d api.ctl-va1-a.orchestrate.io -f combined.csv -c reddit-comments