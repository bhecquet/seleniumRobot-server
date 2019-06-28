'''
Created on 4 mai 2017

@author: bhecquet
'''


from elementInfoServer.models import ElementInfo
from elementInfoServer.views.serializers import ElementInfoSerializer

from commonsServer.views.viewsets import BaseViewSet


class ElementInfoViewSet(BaseViewSet):
    queryset = ElementInfo.objects.all()
    serializer_class = ElementInfoSerializer
    
