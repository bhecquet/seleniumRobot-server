'''
Created on 28 juin 2019

@author: s047432
'''
from rest_framework import generics
from elementInfoServer.views.serializers import ElementInfoSerializer
from elementInfoServer.models import ElementInfo
import datetime
from django.utils import timezone

class ElementInfoList(generics.ListAPIView):
    serializer_class = ElementInfoSerializer

    def get_queryset(self):
        return ElementInfo.objects.all()
    
    def filter_queryset(self, queryset):
       
        application = self.request.query_params.get('application', None)
        ids = [i for i in self.request.query_params.get('ids', "").split(',') if i]
        
        # delete elementInfo older than 30 days
        for ei in ElementInfo.objects.all():
            if timezone.now() - datetime.timedelta(days=30) > ei.lastUpdate:
                ei.delete()
        
        if ids:
            return queryset.filter(application__id=application, id__in=ids)
        else:
            return queryset.filter(application__id=application)