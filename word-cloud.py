from pyspark import SparkContext, SparkConf, StorageLevel
import json
import re
from stemming.porter2 import stem
import numpy as np
from pyspark.sql import SQLContext
from pyspark.sql.functions import desc
from pyspark.sql.types import *
from utils import saveWordCloud

if __name__ == "__main__":
    conf = SparkConf().setAppName("reddit")
    conf.set('spark.serializer', 'org.apache.spark.serializer.KryoSerializer')
    sc = SparkContext(conf=conf)
    sqlContext = SQLContext(sc)
    data_rdd = sc.textFile("s3n://reddit-comments/2015/*")
    # randomly sample from the set of 2015 comments and decode json
    comments = data_rdd.filter(lambda x: len(x) > 0).sample(False, 0.2).map(lambda x: json.loads(x.encode('utf8')))

    # function to remove stems and clean words
    def clean_word(w):
        return re.sub("\,|\.|\;|\:|\;|\?|\!|\[|\]|\}|\{", "", stem(w.lower()))

    # produce a mapping of subreddits to comments
    document_bodies = comments.map(lambda x: (x['subreddit'], " ".join(map(lambda y: clean_word(y), x['body'].split()))))
    # split comments into terms
    all_terms = document_bodies.map(lambda x: (x[0], list(set(x[1].split()))))
    term_document_count = all_terms.flatMap(lambda x: [(i, x[0]) for i in x[1]]).countByKey()

    # find the term frequencies in documents
    document_tf = document_bodies.map(lambda x: (x[0], x[1].split())).flatMapValues(lambda x: x).countByValue()
    # find the total number of documents
    total_documents = 1.0 * document_bodies.count()
    # find the total number of words in each document/subreddit
    total_words_per_subreddit = document_bodies.map(lambda x: (x[0], x[1].split())).flatMapValues(lambda x: x).countByKey()

    distinct_words_per_subreddit = document_bodies.map(lambda x: (x[0], x[1].split())).flatMapValues(lambda x: x).distinct()

    word_occurences_across_subreddits = distinct_words_per_subreddit.map(lambda x: (x[1], x[0])).countByKey()

    # compute TF-IDF for each document
    def subreddit_tf_idf(subreddit_total, words_per_subreddit, tf_per_subreddit, occ_across_subreddits):
        result = []
        for key, value in tf_per_subreddit.items():
            subreddit = key[0]
            term = key[1]
            wpm = words_per_subreddit[subreddit]
            ocm = occ_across_subreddits[term]
            tf_idf = float((float(value)/wpm) * np.log(subreddit_total/ocm))
            result.append({"subreddit":subreddit, "term":term, "score":tf_idf})
        return result
    subreddit_word_importance = subreddit_tf_idf(total_documents, total_words_per_subreddit, document_tf, word_occurences_across_subreddits)

    # get the top 500 words per subreddit
    fields = [StructField("subreddit", StringType(), True),
                  StructField("score", FloatType(), True),
                  StructField("term", StringType(), True),]
    rdd = sc.parallelize(subreddit_word_importance)
    df = sqlContext.createDataFrame(rdd, schema=StructType(fields))

    for row in df.select('subreddit').distinct():
        rows = df.filter(df['subreddit'] == row['subreddit']).orderBy(desc('score'))
        if rows.count() > 50:
            # map to term frequency tuples
            frequencies = rows.select(['term', 'score']).map(lambda x: (x['term'], x['score'])).collect()
            saveWordCloud(row['subreddit'], frequencies)