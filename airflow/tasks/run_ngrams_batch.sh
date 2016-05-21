#!/usr/bin/env bash
cd ~/reddit-comments/
spark-submit --master local[*] --executor-memory 22g --driver-memory 14g ngram-nltk.py