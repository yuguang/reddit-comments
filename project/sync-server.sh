#!/usr/bin/env bash
rsync -rav -e ssh --exclude='*.pyc' --exclude='*.csv' --exclude='*.sqlite3*' --exclude='dev-python/*' --exclude='*local_settings.py' . yuguang:/home/yuguang/reddit/project