
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

class Mysql():
    def connect(self):
        # workers must each connect individually
        import sys, os, django
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "project"))
        os.environ["DJANGO_SETTINGS_MODULE"] = "project.settings"
        django.setup()

    def saveSubredditCounts(self, month, rdd):
        self.connect()
        from reddit.models import Subreddit
        from django.db import IntegrityError
        entries = []
        for line in rdd:
            d = Subreddit(month=month.replace('RC_', ''), count=line[1], name=line[0])
            entries.append(d)
            try:
                Subreddit.objects.bulk_create(entries)
            except IntegrityError:
                pass # month and domain name should be unique

    def saveDomains(self, month, rdd):
        self.connect()
        from reddit.models import Domain
        from django.db import IntegrityError
        entries = []
        for line in rdd:
            d = Domain(month=month.replace('RC_', ''), count=line[1], name=line[0])
            entries.append(d)
            try:
                Domain.objects.bulk_create(entries)
            except IntegrityError:
                pass

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
                date, ngram, count, total = line
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
    def saveNgrams(ngramcount, rdditer, table, async=True, debug=False):
        if debug:
            for datatuple in rdditer:
                print datatuple
            return
        from cassandra.cluster import Cluster
        import time
        CASSANDRA_WAIT = 5
        QUERY_WAIT = 0.001
        NODES = []
        CassandraCluster = Cluster(NODES)

        success = False
        #try to reconnect if connection is down
        while not success:
            try:
                session = CassandraCluster.connect(keyspace)
                session.default_timeout = 60
                success = True
            except:
                success = False
                time.sleep(CASSANDRA_WAIT)

        query = "INSERT INTO %s (ngram, subreddit, time_bucket, date, count, percentage) VALUES (?, ?, ?, ?, ? ,?)" %(table,)
        prepared = session.prepare(query)

        timeConverter = TimeConverter()
        for datatuple in rdditer:
            # ('2007-10-23', (126827, [u'politics', u'term terrorism clearly', 1]))
            date = datatuple[0]
            time_bucket = timeConverter.toTimebucket(date)

            total = float(datatuple[1][0])
            subreddit = str(datatuple[1][0][0])
            ngram = str(datatuple[1][0][1])
            count = int(datatuple[1][0][2])
            percentage = float(count) / total

            bound = prepared.bind((ngram, subreddit, time_bucket, date, count, percentage))
            if async:
                session.execute_async(bound)
                time.sleep(QUERY_WAIT)
            else:
                session.execute(bound)

        session.shutdown()


import unittest

class TestDatabases(unittest.TestCase):
    def test_connect(self):
        db = Mysql()
        db.connect()
    def test_save(self):
        from reddit.models import Domain
        d = Domain(month='2007-01', count=1, name='none')
        d.save()
        d.delete()

class TestElastic(unittest.TestCase):
    def test_save(self):
        rdd = [('2007-10-29', 'reddit.com', '&gt; science disproves', 1, 100),
            ('2007-10-16', 'reddit.com', 'reddit well-equipped handle', 1, 100),
            ('2007-10-28', 'reddit.com', 'aside removing context', 1, 100),
            ('2007-10-23', 'politics', 'term terrorism clearly', 1, 100)]
        db = ElasticSearch()
        db.saveNgramCounts(3, rdd)
        db.client.delete('subreddit_ngram_count-test')
    def test_save_datetime(self):
        from datetime import datetime
        rdd = [(datetime(1988, 8, 16), 'reddit.com', '&gt; science disproves', 1, 100),]
        db = ElasticSearch()
        db.saveNgramCounts(3, rdd)
        db.client.delete('subreddit_ngram_count-test')

if __name__ == '__main__':
    unittest.main()