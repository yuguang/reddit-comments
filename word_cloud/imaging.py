from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import urllib2, json, uuid
import requests
from redditdownload.redditdownload import download_images
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import subprocess, os, glob, string, shutil

WIDTH = 800
HEIGHT = 600
DPI = 300
COLORS = int(255*255/6)
MIN_SCORE = str(300)
NUM_PHOTOS = str(250)
FONT_SIZE_MAX = 62
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

def num_colors(color_counts):
    # color_counts: a list of (count, color) tuples or None
    if not color_counts:
        return 0
    return len(filter(lambda t: t[0] > 0, color_counts))

def ext_files(subreddit, ext):
    return glob.glob(os.path.join(BASE_DIR, subreddit) + '/*.' + ext)

def save_word_cloud(subreddit, frequencies, stopwords=STOPWORDS):
    try:
        # download images for subreddit
        download_images(['--score', MIN_SCORE, '--num', NUM_PHOTOS, '--sort-type', 'topall', subreddit, subreddit])
        # get a list of downloaded file names
        coloring = []
        for file in ext_files(subreddit, 'jpg') + ext_files(subreddit, 'png') + ext_files(subreddit, 'gif'):
            base_file = os.path.basename(file)
            # get the number of colors in the image and compare
            image = Image.open(os.path.join(BASE_DIR, subreddit, base_file))
            w, h = image.size
            if num_colors(image.convert('RGB').getcolors(w*h)) > COLORS:
                coloring = np.array(image)
                break
        shutil.rmtree(subreddit)
        if not len(coloring):
            raise Exception
        wc = WordCloud(font_path=os.path.join(BASE_DIR, 'fonts', 'Viga-Regular.otf'), background_color="white", width=WIDTH, height=HEIGHT, max_words=500, mask=coloring, max_font_size=FONT_SIZE_MAX, stopwords=stopwords)
        # generate word cloud
        wc.generate_from_frequencies(frequencies)

        # create coloring from image
        image_colors = ImageColorGenerator(coloring)

        # recolor wordcloud and show
        # we could also give color_func=image_colors directly in the constructor
        plt.imshow(wc.recolor(color_func=image_colors))
        plt.axis("off")
    except Exception,e:
        print str(e)
        # take relative word frequencies into account, lower max_font_size
        wordcloud = WordCloud(font_path=os.path.join(BASE_DIR, 'fonts', 'PassionOne-Regular.otf'), background_color="white", width=WIDTH, height=HEIGHT, max_words=500, max_font_size=(FONT_SIZE_MAX + 20), stopwords=stopwords)
        wordcloud.generate_from_frequencies(frequencies)
        plt.imshow(wordcloud)
        plt.axis("off")
    fig = plt.gcf()
    # save wordcloud for subreddit
    fig.savefig('{}.png'.format(subreddit), transparent=True, dpi=DPI)
    return "generated image for {}".format(subreddit)


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

if __name__ == '__main__':
    unittest.main()