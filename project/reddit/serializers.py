from models import *
from rest_framework import serializers


class DomainSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Domain
        fields = ('name', 'count', 'month')
