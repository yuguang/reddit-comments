# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-03 15:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reddit', '0006_auto_20160516_1555'),
    ]

    operations = [
        migrations.CreateModel(
            name='Term',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('subreddit', models.CharField(max_length=200)),
                ('count', models.BigIntegerField(default=0)),
            ],
            options={
                'ordering': ['-count'],
            },
        ),
        migrations.AlterModelOptions(
            name='domaintimeseries',
            options={'ordering': ['-total']},
        ),
        migrations.AlterModelOptions(
            name='subreddittimeseries',
            options={'ordering': ['-total']},
        ),
        migrations.AlterUniqueTogether(
            name='term',
            unique_together=set([('subreddit', 'name')]),
        ),
    ]
