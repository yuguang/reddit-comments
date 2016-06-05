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
    total = models.BigIntegerField(default=0)

    class Meta:
        ordering = ['-total']

class Subreddit(models.Model):
    month = models.CharField(max_length=30)
    count = models.BigIntegerField() # stores up to 9223372036854775807
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = (('month', 'name'),)

class SubredditTimeseries(models.Model):
    name = models.CharField(max_length=200,primary_key=True)
    series = models.TextField()
    total = models.BigIntegerField(default=0)

    class Meta:
        ordering = ['-total']

class Term(models.Model):
    name = models.CharField(max_length=200)
    subreddit = models.CharField(max_length=200)
    count = models.BigIntegerField(default=0)

    class Meta:
        unique_together = (('subreddit', 'name'),)
        ordering = ['-count']

class WordCloud(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    total = models.BigIntegerField(default=0)

    class Meta:
        ordering = ['-total']
