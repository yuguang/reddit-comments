from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import urllib2, json, uuid
import requests
from redditdownload.redditdownload import download_images
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import subprocess, os, glob, string, shutil, random
from colors import num_colors

WIDTH = 540
HEIGHT = 540
DPI = 300
COLORS = 1
MIN_SCORE = str(300)
NUM_PHOTOS = str(250)
FONT_SIZE_MAX = 62
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

def ext_files(subreddit, ext):
    return glob.glob(os.path.join(BASE_DIR, subreddit) + '/*.' + ext)

def get_gif_coloring(subreddit):
    url = "https://www.reddit.com/r/{}/top/.json?limit=200&t=all".format(subreddit)
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'my_unique_reddit_downloader' + str(random.randrange(0, 1000)))]
    response = opener.open(url)
    payload = json.loads(response.read())
    for i in range(0,len(payload['data']['children'])):
        if 'preview' not in payload['data']['children'][i]['data']:
            continue
        url = payload['data']['children'][i]['data']['preview']['images'][0]['source']['url']
        # download and open image
        image_file = opener.open(url)
        # generate random uuid for image filename
        filename = subreddit + '_mask'
        with open(filename, 'wb') as output:
            output.write(image_file.read())
        image = Image.open(filename)
        w, h = image.size
        if w > WIDTH and h > HEIGHT and num_colors(filename) > COLORS:
            coloring = np.array(image)
            return coloring

def save_word_cloud(subreddit, frequencies, stopwords=STOPWORDS):
    try:
        # download images for subreddit
        download_images(['--score', MIN_SCORE, '--num', NUM_PHOTOS, '--sort-type', 'topall', subreddit, subreddit])
        # get a list of downloaded file names
        coloring = []
        for file in ext_files(subreddit, 'jpg') + ext_files(subreddit, 'png'):
            base_file = os.path.basename(file)
            # get the number of colors in the image and compare
            image = Image.open(os.path.join(BASE_DIR, subreddit, base_file))
            w, h = image.size
            if w > WIDTH and h > HEIGHT and num_colors(os.path.join(BASE_DIR, subreddit, base_file)) > COLORS:
                coloring = np.array(image)
                break
        shutil.rmtree(subreddit)
        if not len(coloring):
            # get previews for gifs
            coloring = get_gif_coloring(subreddit)
        if not len(coloring):
            raise Exception('No suitable image found')
        wc = WordCloud(font_path=os.path.join(BASE_DIR, 'fonts', 'Viga-Regular.otf'), background_color="white", width=WIDTH, height=HEIGHT, max_words=500, mask=coloring, min_font_size=10, max_font_size=FONT_SIZE_MAX, stopwords=stopwords)
        # generate word cloud
        wc.generate_from_frequencies(frequencies)

        # create coloring from image
        image_colors = ImageColorGenerator(coloring)

        # recolor wordcloud and show
        # we could also give color_func=image_colors directly in the constructor
        plt.imshow(wc.recolor(color_func=image_colors))
        plt.axis("off")
        fig = plt.gcf()
        # save wordcloud for subreddit
        fig.savefig('{}.png'.format(subreddit), transparent=True)
        return "generated image for {}".format(subreddit)
    except Exception,e:
        print str(e)


import unittest

class TestDownload(unittest.TestCase):
    def test_sub(self):
        save_word_cloud('cats', [('a',1),('b',2)])
        self.assertTrue(os.path.exists('cats.png'))
    def test_gif(self):
        save_word_cloud('gifs', [('a',1),('b',2)])
        self.assertTrue(os.path.exists('gifs.png'))

class TestColors(unittest.TestCase):
    def test_sub(self):
        subreddit = 'cats'
        download_images(['--num', '1', '--sort-type', 'topall', subreddit, subreddit])
        # get a list of downloaded file names
        for file in ext_files(subreddit, 'jpg') + ext_files(subreddit, 'png') + ext_files(subreddit, 'gif'):
            base_file = os.path.basename(file)
            print base_file
            # get the number of colors in the image and compare
            image = Image.open(os.path.join(BASE_DIR, subreddit, base_file))
            w, h = image.size
            self.assertGreater(num_colors(image.convert('RGB').getcolors(w*h)), COLORS)
    def test_get_gif(self):
        self.assertGreater(len(get_gif_coloring('gifs')), 0)

if __name__ == '__main__':
    unittest.main()