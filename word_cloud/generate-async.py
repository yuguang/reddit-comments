from multiprocessing import Pool
from django.db.models import Q
import time
import argparse, os, sys
sys.path.append(os.path.abspath(os.path.join('.', os.pardir)))
from storage import Sqlite
from imaging import save_word_cloud
from django.db.models import Sum

def unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

if __name__ == '__main__':
    MAX_TERMS = 1024*2
    MIN_TERMS = 200
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
    # common words that appear in all subreddits are considered stopwords
    stopwords = set(Term.objects.exclude(Q(name='[deleted]')|Q(name='&gt;')|Q(name='')).annotate(total=Sum('count')).order_by('-total').values_list('name', flat=True)[:100])
    for subreddit in subreddits:
        try:
            terms = Term.objects.filter(subreddit=subreddit).exclude(Q(name='[deleted]')|Q(name='&gt;')|Q(name=''))
            if terms.count() < MIN_TERMS:
                continue
            frequencies = [(term.name, int(term.count)) for term in terms[:MAX_TERMS]]
            print "=========================================="
            print "making word cloud for ", subreddit
            print "=========================================="
            result = pool.apply_async(save_word_cloud, (subreddit, frequencies, stopwords)) # make word cloud asynchronously
            multiple_results.append(result)
        except Exception,e:
            print str(e)
    for res in multiple_results:
        try:
            print res.get()
        except Exception,e:
            print str(e)
