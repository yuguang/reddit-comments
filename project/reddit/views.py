from models import *
from django.shortcuts import get_object_or_404, get_list_or_404, render
from rest_framework import viewsets
from serializers import *
from rest_framework.decorators import api_view
from jsonresponse import JSONResponse

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
    def detail(self, request):
        if request.is_ajax():
            term = request.GET.get('term', '')
            if term:
                result = []
                for domain in self.model.objects.filter(name__icontains=term).distinct('name'):
                    result.append({'id': domain.name,'label': domain.name,'value': domain.name})
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