from __future__ import unicode_literals

from django.db import models

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