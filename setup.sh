#!/usr/bin/env bash
sudo pip install -r requirements.txt
# gentoo
emerge -aN '>=dev-python/numpy-1.6'
# ubuntu
sudo apt-get install python-numpy
python -m nltk.downloader punkt
python -m nltk.downloader treebank
python -m nltk.downloader stopwords