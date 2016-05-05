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
    timeline = get_list_or_404(Domain, name=request.data['name'])
    serializer = DomainSerializer(timeline, many=True)
    return JSONResponse(serializer.data)