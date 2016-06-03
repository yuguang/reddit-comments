from multiprocessing import Pool
from django.db.models import Q
import time
import argparse, os, sys
sys.path.append(os.path.abspath(os.path.join('.', os.pardir)))
from storage import Sqlite
from os import path
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import urllib2, json, uuid
import requests
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator

DOWNLOADED = 'masked'
RANDOM = 'random'
def save_word_cloud(subreddit, frequencies, id):
    WIDTH = 1200
    HEIGHT = 800
    COLORS = 80
    WAIT = 1000
    if len(frequencies) < 100:
        return
    url = "https://www.reddit.com/r/{}/top/.json?limit=200&t=all".format(subreddit)
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'my_unique_reddit_downloader' + id)]
    response = opener.open(url)
    payload = json.loads(response.read())
    try:
        i = 0
        if not 'preview' in payload['data']['children'][i]['data']:
            i += 1
        url = payload['data']['children'][i]['data']['preview']['images'][0]['source']['url']
        # download and open image
        image_file = opener.open(url)
        # generate random uuid for image filename
        filename = subreddit + '_mask'
        with open(filename, 'wb') as output:
          output.write(image_file.read())
        image = Image.open(filename)
        coloring = np.array(image)
        wc = WordCloud(background_color="white", width=WIDTH, height=HEIGHT, max_words=500, mask=coloring,
                       max_font_size=40)
        # generate word cloud
        print frequencies[:10]
        wc.generate_from_frequencies(frequencies)

        # create coloring from image
        image_colors = ImageColorGenerator(coloring)

        # recolor wordcloud and show
        # we could also give color_func=image_colors directly in the constructor
        plt.imshow(wc.recolor(color_func=image_colors))
        plt.axis("off")
        type = DOWNLOADED
    except:
        # take relative word frequencies into account, lower max_font_size
        wordcloud = WordCloud(background_color="white", width=WIDTH, height=HEIGHT, max_words=500, max_font_size=40)
        wordcloud.generate_from_frequencies(frequencies)
        plt.imshow(wordcloud)
        plt.axis("off")
        type = RANDOM
    fig = plt.gcf()
    # save wordcloud for subreddit
    fig.savefig('{}.png'.format(subreddit), transparent=True, dpi=300)
    return "generated {} image for {}".format(type, subreddit)

def unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("processes", help="Number of processes (best set to number of CPU cores)")
    args = parser.parse_args()

    # start worker processes
    pool = Pool(processes=int(args.processes))
    db = Sqlite()
    db.connect()
    from reddit.models import Term
    multiple_results = []
    subreddits = unique(Term.objects.values_list('subreddit', flat=True).all())
    i = 0
    for subreddit in subreddits:
        try:
            terms = Term.objects.filter(subreddit=subreddit).exclude(Q(name='[deleted]')|Q(name='&gt;')|Q(name=''))
            if terms.count() < 50:
                continue
            frequencies = [(term.name, int(term.count)) for term in terms]
            print "=========================================="
            print "making word cloud for ", subreddit
            print "=========================================="
            result = pool.apply_async(save_word_cloud, (subreddit, frequencies, str(i))) # make word cloud asynchronously
            i += 1
            multiple_results.append(result)
        except Exception,e:
            print str(e)
    for res in multiple_results:
        try:
            print res.get()
        except Exception,e:
            print str(e)
