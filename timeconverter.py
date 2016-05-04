import time
from datetime import datetime

class TimeConverter:
    # cassandra accepts yyyy-mm-dd format
    def __init__(self):
        self.dateformat = '%Y-%m-%d'
    def toDate(self, x):
        return time.strftime(self.dateformat, time.gmtime(int(x)))
    def toTimebucket(self, time_string):
        parts = time_string.split('-')
        return '-'.join(parts[:1] + ['01', '01'])
            
import unittest

class TestTimeConverterMethods(unittest.TestCase):
    def test_date(self):
        c = TimeConverter()
        self.assertEqual(c.toDate(1462238456), '2016-05-03')
    def test_timebucket(self):
        c = TimeConverter()
        self.assertEqual(c.toTimebucket('2016-05-03'), '2016-01-01')
                         
if __name__ == '__main__':
    unittest.main()