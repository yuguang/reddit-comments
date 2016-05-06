from models import *
from django.shortcuts import get_object_or_404, get_list_or_404, render
from rest_framework import viewsets
from serializers import *
from rest_framework.decorators import api_view
from jsonresponse import JSONResponse

class DomainViewSet(viewsets.ModelViewSet):
    queryset = Domain.objects.all().order_by('-month')
    serializer_class = DomainSerializer

@api_view(['GET'])
def domain_detail(request):
    if request.is_ajax():
        term = request.GET.get('term', '')
        if term:
            result = []
            # get the last domain after comma
            term = term.split(' ')[-1]
            # TODO: add .distinct('name') after merging with main branch
            for domain in Domain.objects.filter(name__icontains=term):
                result.append({'id': domain.name,'label': domain.name,'value': domain.name})
            return JSONResponse(result)
        else:
            domains = request.GET['domains'].split(',')
            response_dict = {}
            for domain in domains:
                timeline = Domain.objects.filter(name=domain)
                if timeline:
                    serializer = DomainSerializer(timeline, many=True)
                    response_dict[domain] = serializer.data
            return JSONResponse(response_dict)
    else:
        return render(request, 'domains.html')
