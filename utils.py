from urlparse import urlparse
import re

from os import path
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import urllib2, json, uuid
import requests
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

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

def saveWordCloud(subreddit, frequencies):
    WIDTH = 800
    HEIGHT = 600
    url = "https://www.reddit.com/r/{}/top/.json?limit=5&t=all".format(subreddit)
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'my_unique_downloader')]
    response = opener.open(url)
    payload = json.loads(response.read())
    try:
        url = payload['data']['children'][0]['data']['preview']['images'][0]['source']['url']
            # download and open image
        image_file = opener.open(url)
        # generate random uuid for image filename
        filename = str(uuid.uuid4())
        with open(filename, 'wb') as output:
          output.write(image_file.read())
        image = Image.open(filename)
        if len(image.histogram()) < 500:
            raise Exception
        coloring = np.array(image)
        wc = WordCloud(background_color="white", width=WIDTH, height=HEIGHT, max_words=500, mask=coloring, stopwords=STOPWORDS,
                       max_font_size=40, scale=1.5)
        # generate word cloud
        wc.generate_from_frequencies(frequencies)
    
        # create coloring from image
        image_colors = ImageColorGenerator(coloring)
    
        # recolor wordcloud and show
        # we could also give color_func=image_colors directly in the constructor
        plt.imshow(wc.recolor(color_func=image_colors))
        plt.axis("off")
    except:
        # take relative word frequencies into account, lower max_font_size
        wordcloud = WordCloud(background_color="white", width=WIDTH, height=HEIGHT, max_words=500, stopwords=STOPWORDS, max_font_size=40)
        wordcloud.generate_from_frequencies(frequencies)
        plt.imshow(wordcloud)
        plt.axis("off")
    fig = plt.gcf()
    # save wordcloud for subreddit
    fig.savefig('{}.png'.format(subreddit), transparent=True, dpi=300)


import unittest

class TestParsers(unittest.TestCase):
    def test_url(self):
        self.assertEqual(findUrlDomain('[goog](http://google.com) [link](http://i.imgur.com/BaZ.png) [http://www.smashingmagazine.com](http://www.smashingmagazine.com)'), ['http://google.com', 'http://i.imgur.com', 'http://www.smashingmagazine.com'])

if __name__ == '__main__':
    unittest.main()