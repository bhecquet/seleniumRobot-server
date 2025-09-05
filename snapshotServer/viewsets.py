'''
Created on 4 mai 2017

@author: bhecquet
'''
import datetime
import io
import json
import zipfile

from django.utils import timezone

from rest_framework import viewsets, renderers, serializers
from rest_framework.decorators import action
from rest_framework.generics import UpdateAPIView, CreateAPIView, \
    RetrieveAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from commonsServer.views.viewsets import BaseViewSet, perform_create
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording, \
    ApplicationPermissionChecker
from snapshotServer.models import TestStep, TestSession, ExcludeZone, TestCaseInSession, StepResult, \
    File, ExecutionLogs, TestInfo, Error, Version, Application

class Ping(APIView):

    # allow anyone on this view
    queryset = TestSession.objects.none()
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response("OK")

class ResultRecordingViewSet(ViewSet,
                             CreateAPIView, # POST
                             RetrieveAPIView, # GET
                             UpdateAPIView # PATCH
                             ):
    permission_classes = [ApplicationSpecificPermissionsResultRecording]
    recreate_existing_instance = True 
    
    def perform_create(self, serializer):
        """
        Check if we need to recreate or not the object
        """
        if self.recreate_existing_instance:
            super().perform_create(serializer)
            return
        
        # Do not create an object if it already exists
        perform_create(ResultRecordingViewSet, self, serializer)




class ExcludeZoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExcludeZone
        fields = ('id', 'x', 'y', 'width', 'height', 'snapshot')
    
class ExcludeZoneViewSet(BaseViewSet): # post
    queryset = ExcludeZone.objects.all()
    serializer_class = ExcludeZoneSerializer
