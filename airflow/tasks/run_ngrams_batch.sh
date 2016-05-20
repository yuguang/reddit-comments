#!/usr/bin/env bash
spark-submit --master local[*] --executor-memory 22g --driver-memory 14g ~/reddit-comments/ngram-nltk.py