from django.db import IntegrityError

class Mysql():
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

    def saveSubredditCounts(self, month, rdd):
        self.connect()
        from reddit.models import Subreddit
        for line in rdd:
            d = Subreddit(month=month.replace('RC_', ''), count=line[1], name=line[0])
            try:
                d.save()
            except IntegrityError:
                pass # month and domain name should be unique

    def saveDomains(self, month, rdd):
        self.connect()
        from reddit.models import Domain
        for line in rdd:
            d = Domain(month=month.replace('RC_', ''), count=line[1], name=line[0])
            try:
                d.save()
            except IntegrityError:
                pass

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

if __name__ == '__main__':
    unittest.main()