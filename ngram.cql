CREATE TABLE ngram (
    phrase text,
    time_bucket timestamp,
    date timestamp,
    absolute_count int,
    percentage float,
    PRIMARY KEY ((phrase, time_bucket), date)
) WITH CLUSTERING ORDER BY (date DESC);