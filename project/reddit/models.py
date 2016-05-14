from __future__ import unicode_literals

from django.db import models
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model

class Domain(models.Model):
    month = models.CharField(max_length=30)
    count = models.IntegerField() # stores up to 2,147,483,647
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = (('month', 'name'),)

class Subreddit(models.Model):
    month = models.CharField(max_length=30)
    count = models.BigIntegerField() # stores up to 9223372036854775807
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = (('month', 'name'),)

class Ngram(Model):
    phrase = columns.Text(primary_key=True)
    time_bucket = columns.DateTime(primary_key=True)
    date = columns.DateTime()
    absolute_count = columns.Integer()
    percentage = columns.Float()
