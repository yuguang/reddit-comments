# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-05 16:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reddit', '0007_auto_20160603_1548'),
    ]

    operations = [
        migrations.CreateModel(
            name='WordCloud',
            fields=[
                ('name', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('total', models.BigIntegerField(default=0)),
            ],
            options={
                'ordering': ['-total'],
            },
        ),
    ]
