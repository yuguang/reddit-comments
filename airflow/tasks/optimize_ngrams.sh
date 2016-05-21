#!/usr/bin/env bash
cd ~/reddit-comments/serving_optimization
cat /mnt/work/20*/*/*/* > ngram.raw.csv
spark-submit --executor-memory 2g --driver-memory 2g --packages com.databricks:spark-csv_2.10:1.4.0 optimize_ngrams.py ngram.raw.csv
cat converted.csv.files/* > ngram.opt.csv
rm -rf converted.csv.files
