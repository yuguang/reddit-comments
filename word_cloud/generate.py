from django.db.models import Q
import argparse, os, sys
sys.path.append(os.path.abspath(os.path.join('.', os.pardir)))
from storage import Sqlite
from imaging import *

def unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

if __name__ == '__main__':
    # start worker processes
    db = Sqlite()
    db.connect()
    from reddit.models import Term
    subreddits = unique(Term.objects.values_list('subreddit', flat=True).all())
    i = 0
    for subreddit in subreddits:
        terms = Term.objects.filter(subreddit=subreddit).exclude(Q(name='[deleted]')|Q(name='&gt;')|Q(name=''))
        if terms.count() < 50:
            continue
        frequencies = [(term.name, int(term.count)) for term in terms]
        print "=========================================="
        print "making word cloud for ", subreddit
        print "=========================================="
        save_word_cloud(subreddit, frequencies, str(i))
        i += 1
