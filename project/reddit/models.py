from __future__ import unicode_literals

from django.db import models

class Domain(models.Model):
    month = models.CharField(max_length=30)
    count = models.IntegerField() # stores up to 2,147,483,647
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = (('month', 'name'),)

class DomainTimeseries(models.Model):
    name = models.CharField(max_length=200,primary_key=True)
    series = models.TextField()
    total = models.BigIntegerField()

class Subreddit(models.Model):
    month = models.CharField(max_length=30)
    count = models.BigIntegerField() # stores up to 9223372036854775807
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = (('month', 'name'),)

class SubredditTimeseries(models.Model):
    name = models.CharField(max_length=200,primary_key=True)
    series = models.TextField()
    total = models.BigIntegerField()


try:
    from cassandra.cqlengine import columns
    from cassandra.cqlengine.models import Model
except ImportError:
    pass
else:
    class Ngram(Model):
        phrase = columns.Text(primary_key=True)
        time_bucket = columns.DateTime(primary_key=True)
        date = columns.DateTime()
        absolute_count = columns.Integer()
        percentage = columns.Float()
