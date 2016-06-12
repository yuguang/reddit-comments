from models import *
from django.shortcuts import get_object_or_404, get_list_or_404, render
from rest_framework import viewsets
from serializers import *
from rest_framework.decorators import api_view
from jsonresponse import JSONResponse
import os, base64
import boto3
from boto3.dynamodb.conditions import Key, Attr

class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all().order_by('-month')
    serializer_class = DomainSerializer

class SearchModelSerializer():
    def __init__(self, model, serializer):
        self.model = model
        self.serializer = serializer
        name = model.__name__.lower().replace('timeseries', '')
        self.name = name
        self.template = '{}.html'.format(name)
    def unique(self, seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]
    def detail(self, request):
        if request.is_ajax():
            # get suggestions for term
            term = base64.b64decode(request.GET.get('term', ''))
            if term:
                result = []
                for domain in self.model.objects.values_list('name', flat=True).filter(name__icontains=term)[:20]:
                    result.append({'id': domain,'label': domain,'value': domain})
                return JSONResponse(result)
            else:
                # get a time series matching search terms
                domains = base64.b64decode(request.GET['domains']).split(',')
                response_dict = {}
                for domain in domains:
                    timeline = self.model.objects.get(name=domain)
                    if timeline:
                        serializer = self.serializer(timeline)
                        response_dict[domain] = serializer.data
                return JSONResponse(response_dict)
        else:
            return render(request, self.template, {'model': self.name})

@api_view(['GET'])
def domain_detail(request):
    serializer = SearchModelSerializer(DomainTimeseries, DomainSerializer)
    return serializer.detail(request)

@api_view(['GET'])
def subreddit_detail(request):
    serializer = SearchModelSerializer(SubredditTimeseries,  SubredditSerializer)
    return serializer.detail(request)

@api_view(['GET'])
def word_cloud(request):
    serializer = SearchModelSerializer(WordCloud,  WordCloudSerializer)
    return serializer.detail(request)

def get_ngram_series(term):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

    table = dynamodb.Table('ngrams')

    response = table.query(
        KeyConditionExpression=Key('phrase').eq(term)
    )
    return [[item['date'], item['percentage']] for item in  response['Items']]


@api_view(['GET'])
def ngram(request):
    if request.is_ajax():
        terms = request.GET['terms'].split(',')
        terms = map(lambda s: s.strip(), terms)
        response_dict = {}
        for term in terms:
            timeline = get_ngram_series(term)
            if timeline:
                response_dict[term] = timeline
        return JSONResponse(response_dict)
    return render(request, 'ngram.html')

def home(request):
    return render(request, 'home.html')

def top(request):
    return render(request, 'best.html')

def peak_hours(request):
    return render(request, 'hour.html')

def peak_weekdays(request):
    return render(request, 'weekday.html')

def peak_months(request):
    return render(request, 'month.html')