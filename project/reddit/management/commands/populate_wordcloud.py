from django.core.management.base import BaseCommand, CommandError
from reddit.models import *
from django.core.exceptions import ObjectDoesNotExist
import os
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

class Command(BaseCommand):

    def handle(self, *args, **options):
        def png_list():
            file = open(os.path.join(BASE_DIR, "png_list.txt"),'r')
            l = []
            for line in file:
                l.append(line.rstrip())
            file.close()
            return l
        for subreddit_png in png_list():
            name = subreddit_png.replace('.png', '')
            try:
                count = SubredditTimeseries.objects.get(name=name).total
            except ObjectDoesNotExist:
                count = 0
            WordCloud.objects.create(name=name, total=count)