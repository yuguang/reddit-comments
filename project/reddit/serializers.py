from models import *
from rest_framework import serializers


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = DomainTimeseries
        fields = ('series',)

class SubredditSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubredditTimeseries
        fields = ('series',)
