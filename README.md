Redditor's Club
=================

[Redditor's Club](http://redditor.club/) is a data pipeline for analysis of [Reddit](https://www.reddit.com/) trends. Reddit is an interest-based social media network popular among young males in North America. 


## Technology Stack
This project currently makes use of the following technologies:
- Apache Cassandra 2.2.6
- Apache Spark 1.6.1 with Hadoop 2.7
- MySQL
- AWS S3
- AWS Redshift
- Django 1.9.6 with the following frameworks: HighCharts, jQuery, Bootstrap

The figure below shows the flow of data through the pipeline:

![Pipeline](/images/pipeline_diagram.png?raw=true "Pipeline")

The data used in this project is the set of Reddit comments published and compiled by reddit user [/u/Stuck_In_the_Matrix](http://www.reddit.com/r/datasets/comments/3bxlg7/i_have_every_publicly_available_reddit_comment/). The total size of all comments from October 2007 to December 2015 is greater than 1TB.