# Redditor Club Website

### About

The serving layer consists of a Mysql server and a Django web server. I chose to compress time series and store them in a key-value format in Mysql where name is the primary key and series is a long text field:

    --------------------------------------------------------------------------------------------------------------------------------------------+
    | name                                  | series                                                                                            |
    +---------------------------------------+---------------------------------------------------------------------------------------------------+
    | http://hyperboleandahalf.blogspot.com | 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,34,49,52,62,94,116,77,138,126,175,123...............................|
    +---------------------------------------+---------------------------------------------------------------------------------------------------+

### Setup
A script for setting up virtualenv is included. It will install the dependencies in `requirements.txt`

    ./setup-virtualenv.sh
    dev-python/bin/python manage.py migrate
    dev-python/bin/python manage.py runserver


