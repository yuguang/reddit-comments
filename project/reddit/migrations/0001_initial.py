# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-04 16:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.CharField(max_length=30)),
                ('count', models.IntegerField()),
                ('name', models.CharField(max_length=200)),
            ],
        ),
    ]
