# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-15 00:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reddit', '0004_auto_20160511_0150'),
    ]

    operations = [
        migrations.CreateModel(
            name='DomainTimeseries',
            fields=[
                ('name', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('series', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='SubredditTimeseries',
            fields=[
                ('name', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('series', models.TextField()),
            ],
        ),
        migrations.DeleteModel(
            name='Ngram',
        ),
    ]
