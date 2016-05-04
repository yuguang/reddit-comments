
class Mysql():
    def connect(self):
        # workers must each connect individually
        import sys, os, django
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "project"))
        os.environ["DJANGO_SETTINGS_MODULE"] = "project.settings"
        django.setup()

    def saveSubredditCounts(self):
        self.connect()
        from reddit.models import Subreddit
        for line in rdd:
            d = Subreddit(month=month.replace('RC_', ''), count=line[1], name=line[0])
            d.save()

    def saveDomains(self, month, rdd):
        self.connect()
        from reddit.models import Domain
        for line in rdd:
            d = Domain(month=month.replace('RC_', ''), count=line[1], name=line[0])
            d.save()

import unittest

class TestDatabases(unittest.TestCase):
    def test_connect(self):
        db = Mysql()
        db.connect()

if __name__ == '__main__':
    unittest.main()