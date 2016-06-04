#!/usr/bin/env bash
rsync -rav -e ssh --exclude='*.pyc' --exclude='*.csv' --exclude='*.sqlite3*' --exclude='dev-python/*' --exclude='static/*' --exclude='*local_settings.py' . yuguang:/home/yuguang/reddit/project
rsync -rav -e ssh ./reddit/static/ yuguang:/home/yuguang/public_html/redditor.club/static