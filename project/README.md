Development Notes
=================
To export data from the sqlite3 development database, start the sqlite shell with `sqlite3 db.sqlite3` and run
 
    .mode csv 
    .headers on 
    .out subreddit.csv 
    select * from reddit_subreddit;
    .mode csv 
    .headers on 
    .out domain.csv 
    select * from reddit_domain;
    .exit