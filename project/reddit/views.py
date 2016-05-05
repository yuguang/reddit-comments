from models import *
from rest_framework import viewsets
from serializers import *


class DomainViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Domain.objects.all().order_by('-month')
    serializer_class = DomainSerializer