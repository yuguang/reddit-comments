from django.core.management.base import BaseCommand, CommandError
from reddit.models import *
from django.db import IntegrityError

class Command(BaseCommand):

    def handle(self, *args, **options):
        for entry in Domain.objects.all():
            try:
                entry.pk = None
                entry.save(using='development')
            except IntegrityError:
                pass # month and entry name should be unique
        for entry in Subreddit.objects.all():
            try:
                entry.pk = None
                entry.save(using='development')
            except IntegrityError:
                pass