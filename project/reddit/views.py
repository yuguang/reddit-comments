from models import *
from django.shortcuts import get_object_or_404, get_list_or_404, render
from rest_framework import viewsets
from serializers import *
from rest_framework.decorators import api_view
from jsonresponse import JSONResponse
from porc import Client, Search
import os

class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all().order_by('-month')
    serializer_class = DomainSerializer

class SearchModelSerializer():
    def __init__(self, model, serializer):
        self.model = model
        self.serializer = serializer
        name = model.__name__.lower()
        self.name = name
        self.template = '{}.html'.format(name)
    def unique(self, seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]
    def detail(self, request):
        if request.is_ajax():
            term = request.GET.get('term', '')
            if term:
                result = []
                for domain in self.unique(self.model.objects.values_list('name', flat=True).filter(name__icontains=term))[:20]:
                    result.append({'id': domain,'label': domain,'value': domain})
                return JSONResponse(result)
            else:
                domains = request.GET['domains'].split(',')
                response_dict = {}
                for domain in domains:
                    timeline = self.model.objects.filter(name=domain)
                    if timeline:
                        serializer = self.serializer(timeline, many=True)
                        response_dict[domain] = serializer.data
                return JSONResponse(response_dict)
        else:
            return render(request, self.template, {'model': self.name})

@api_view(['GET'])
def domain_detail(request):
    serializer = SearchModelSerializer(Domain, DomainSerializer)
    return serializer.detail(request)

@api_view(['GET'])
def subreddit_detail(request):
    serializer = SearchModelSerializer(Subreddit,  SubredditSerializer)
    return serializer.detail(request)

@api_view(['GET'])
def ngram(request):
    if request.is_ajax():
        terms = request.GET['terms'].split(',')
        client = Client(os.environ['ORC_API_KEY'])
        search = Search().query('')
        return JSONResponse(client.search('subreddit_ngram_count', search).all())
    return render(request, 'ngram.html')
