from models import *
from rest_framework import serializers


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ('name', 'count', 'month')

class SubredditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subreddit
        fields = ('name', 'count', 'month')
