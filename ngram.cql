CREATE TABLE ngrams (
    ngram text,
    subreddit text,
    time_bucket timestamp,
    date timestamp,
    count int,
    percentage decimal,
    PRIMARY KEY ((ngram, subreddit, time_bucket), date)
) WITH CLUSTERING ORDER BY (date DESC);