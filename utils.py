from urlparse import urlparse
import re

def findUrlDomain(s):
    # Anything that isn't a square closing bracket
    name_regex = "[^]]+"
    # http:// or https:// followed by anything but a closing paren
    url_regex = "http[s]?://[^)]+"

    markup_regex = '\[({0})]\(\s*({1})\s*\)'.format(name_regex, url_regex)
    urls = re.findall(markup_regex, s)
    domains = []
    for url in urls:
        try:
            parsed_uri = urlparse(url[1])
            domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        except:
            print url
        else:
            domains.append(domain)
    return domains

import unittest

class TestParsers(unittest.TestCase):
    def test_url(self):
        self.assertEqual(findUrlDomain('[goog](http://google.com) [link](http://i.imgur.com/BaZ.png) [http://www.smashingmagazine.com](http://www.smashingmagazine.com)'), ['http://google.com', 'http://i.imgur.com', 'http://www.smashingmagazine.com'])

if __name__ == '__main__':
    unittest.main()