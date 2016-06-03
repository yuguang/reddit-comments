import time

MYSQL_SLEEP = 5

class Sqlite():
    def connect(self):
        # workers must each connect individually
        import sys, os, django
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "project"))
        os.environ["DJANGO_SETTINGS_MODULE"] = "project.settings"
        django.setup()
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('PRAGMA temp_store = MEMORY;')
        cursor.execute('PRAGMA synchronous=OFF')
        cursor.execute('PRAGMA default_cache_size = 10000')

    def saveNgramCounts(self, ngram_length, rdd, test=False):
        self.connect()
        from reddit.models import Ngram
        from django.db import IntegrityError
        entries = []
        for line in rdd:
            date, ngram, count, total = line
            percentage = float(int(count) / float(total))
            d = Ngram(day=date, phrase=ngram, percentage=percentage)
            entries.append(d)
            try:
                Ngram.objects.bulk_create(entries)
            except IntegrityError:
                pass

    def saveSubredditWords(self, df):
        self.connect()
        from reddit.models import Term
        for line in df:
            Term.objects.update_or_create(subreddit=line['subreddit'], count=line['count'], name=line['term'])

class Mysql(Sqlite):
    def connect(self):
        # workers must each connect individually
        import sys, os, django
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "project"))
        # sys.path.append(os.path.join("/home/ubuntu/reddit-comments", "project"))
        os.environ["DJANGO_SETTINGS_MODULE"] = "project.settings"
        django.setup()

    def saveSubredditCounts(self, month, rdd):
        self.connect()
        from reddit.models import Subreddit
        for line in rdd:
            Subreddit.objects.update_or_create(month=month.replace('RC_', ''), count=line[1], name=line[0])

    def saveDomains(self, month, rdd):
        self.connect()
        from reddit.models import Domain
        for line in rdd:
            Domain.objects.update_or_create(month=month.replace('RC_', ''), count=line[1], name=line[0])

class ElasticSearch():
    def __init__(self, key):
        self.key = key
    def connect(self):
        from porc import Client
        self.client = Client(self.key)

    def saveNgramCounts(self, ngram_length, rdd, test=False):
        self.connect()
        collection = 'subreddit_ngram_count'
        if test:
            collection = collection + '-test'
        with self.client.async() as c:
            futures = []
            for line in rdd:
                date, subreddit, ngram, count, total = line
                percentage = float(int(count) / float(total))
                futures.append(c.post(collection, {
                    "length": ngram_length,
                    "date": date,
                    "ngram": ngram,
                    "count": count,
                    "percentage": percentage,
                }))
            # block until they complete
            responses = [future.result() for future in futures]
            # ensure they succeeded
            [response.raise_for_status() for response in responses]

    def saveTotalCounts(self, ngram_length, rdd, test=False):
        self.connect()
        collection = 'ngram_total'
        if test:
            collection = collection + '-test'
        for line in rdd:
            date, count = line
            key = '-'.join(map(lambda x: str(x), [ngram_length, date]))
            response = self.client.put(collection, key, {
              "count": count,
            })

class Cassandra():
    def __init__(self, keyspace='reddit'):
        self.nodes = ['ec2-52-38-240-73.us-west-2.compute.amazonaws.com',
                      'ec2-52-10-219-45.us-west-2.compute.amazonaws.com',
                      'ec2-52-36-44-251.us-west-2.compute.amazonaws.com',
                      'ec2-52-27-44-212.us-west-2.compute.amazonaws.com']
        self.keyspace = keyspace
        self.table = 'ngram'

    def set_table(self, table):
        self.table = table

    def saveNgramCounts(self, ngramcount, rdditer, async=True, debug=False):
        if debug:
            for datatuple in rdditer:
                print datatuple
            return
        from cassandra.cluster import Cluster
        from timeconverter import TimeConverter
        import time
        CASSANDRA_WAIT = 5
        QUERY_WAIT = 0.001
        CassandraCluster = Cluster(self.nodes)

        success = False
        #try to reconnect if connection is down
        while not success:
            try:
                session = CassandraCluster.connect(self.keyspace)
                session.default_timeout = 60
                success = True
            except:
                success = False
                time.sleep(CASSANDRA_WAIT)

        query = "INSERT INTO %s (phrase, time_bucket, date, absolute_count, percentage) VALUES (?, ?, ?, ?, ?)" % (self.table,)
        prepared = session.prepare(query)

        timeConverter = TimeConverter()
        for line in rdditer:
            date, ngram, count, total = line
            percentage = float(int(count) / float(total))
            time_bucket = timeConverter.toTimebucket(date)

            bound = prepared.bind((ngram, timeConverter.toDatetime(time_bucket), timeConverter.toDatetime(date), count, percentage))
            if async:
                session.execute_async(bound)
                time.sleep(QUERY_WAIT)
            else:
                session.execute(bound)

        session.shutdown()


import unittest, os


class TestDatabases(unittest.TestCase):
    def test_connect(self):
        db = Mysql()
        db.connect()
    def test_save(self):
        from reddit.models import Domain
        d = Domain(month='2007-01', count=1, name='none')
        d.using('production').save()
        d.delete()

class TestElastic(unittest.TestCase):
    def test_save(self):
        rdd = [('2007-10-29', 'reddit.com', '&gt; science disproves', 1, 100),
            ('2007-10-16', 'reddit.com', 'reddit well-equipped handle', 1, 100),
            ('2007-10-28', 'reddit.com', 'aside removing context', 1, 100),
            ('2007-10-23', 'politics', 'term terrorism clearly', 1, 100)]
        db = ElasticSearch(os.environ['ORC_API_KEY'])
        db.saveNgramCounts(3, rdd, True)
        db.client.delete('subreddit_ngram_count-test')
    def test_save_datetime(self):
        from datetime import datetime
        rdd = [(datetime(1988, 8, 16), 'reddit.com', '&gt; science disproves', 1, 100),]
        db = ElasticSearch(os.environ['ORC_API_KEY'])
        db.saveNgramCounts(3, rdd, True)
        db.client.delete('subreddit_ngram_count-test')

class TestCassandra(unittest.TestCase):
    def test_save(self):
        rdd = [('2007-10-23', 'term terrorism clearly', 1, 10000000)]
        db = Cassandra()
        db.saveNgramCounts(3, rdd)
        import sys, os, django, datetime
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "project"))
        os.environ["DJANGO_SETTINGS_MODULE"] = "project.settings"
        django.setup()
        from reddit.models import Ngram
        self.assertEqual(Ngram.objects.get(phrase='term terrorism clearly', date=datetime.date(2007, 10, 23), time_bucket=datetime.date(2007, 1, 1)).absolute_count, 1)

if __name__ == '__main__':
    unittest.main()