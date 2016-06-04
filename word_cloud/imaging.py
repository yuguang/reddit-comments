from os import path
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import urllib2, json, uuid
import requests
from redditdownload.redditdownload import download_images
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import subprocess, os, glob, string, shutil

def save_word_cloud(subreddit, frequencies, stopwords=STOPWORDS):
    WIDTH = 800
    HEIGHT = 600
    COLORS = 255 * 2
    MIN_SCORE = str(300)
    NUM_PHOTOS = str(15)
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))

    try:
        # download images for subreddit
        download_images(['--score', MIN_SCORE, '--num', NUM_PHOTOS, '--sort-type', 'topall', subreddit, subreddit])
        # get a list of downloaded file names
        coloring = []
        def ext_files(subreddit, ext):
            return glob.glob(os.path.join(BASE_DIR, subreddit) + '/*.' + ext)
        for file in ext_files(subreddit, 'jpg') + ext_files(subreddit, 'png') + ext_files(subreddit, 'gif'):
            base_file = os.path.basename(file)
            # get the number of colors in the image and compare
            image = Image.open(os.path.join(BASE_DIR, subreddit, base_file))
            if len(image.histogram()) > COLORS:
                coloring = np.array(image)
                break
        shutil.rmtree(subreddit)
        if not len(coloring):
            raise Exception
        wc = WordCloud(background_color="white", width=WIDTH, height=HEIGHT, max_words=500, mask=coloring, max_font_size=40, stopwords=stopwords)
        # generate word cloud
        print frequencies[:10]
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
        wordcloud = WordCloud(background_color="white", width=WIDTH, height=HEIGHT, max_words=500, max_font_size=40, stopwords=stopwords)
        wordcloud.generate_from_frequencies(frequencies)
        plt.imshow(wordcloud)
        plt.axis("off")
    fig = plt.gcf()
    # save wordcloud for subreddit
    fig.savefig('{}.png'.format(subreddit), transparent=True, dpi=300)
    return "generated image for {}".format(subreddit)


import unittest

class TestDownload(unittest.TestCase):
    def test_sub(self):
        save_word_cloud('cats', [('a',1),('b',2)])
        self.assertTrue(os.path.exists('cats.png'))
    def test_gif(self):
        save_word_cloud('gifs', [('a',1),('b',2)])
        self.assertTrue(os.path.exists('gifs.png'))

if __name__ == '__main__':
    unittest.main()