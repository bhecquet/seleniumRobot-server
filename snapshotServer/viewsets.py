'''
Created on 4 mai 2017

@author: bhecquet
'''

from rest_framework.generics import UpdateAPIView, CreateAPIView, \
    RetrieveAPIView, DestroyAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.generic import TemplateView

from commonsServer.views.viewsets import perform_create
from seleniumRobotServer.permissions.permissions import ApplicationSpecificPermissionsResultRecording
from snapshotServer.models import TestSession
from snapshotServer.views.login_required_mixin_conditional import LoginRequiredMixinConditional


class Ping(APIView):

    # allow anyone on this view
    queryset = TestSession.objects.none()
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response("OK")

class Home(LoginRequiredMixinConditional, TemplateView):
    template_name = "snapshotServer/home.html"


class ResultRecordingViewSet(ViewSet,
                             CreateAPIView, # POST
                             RetrieveAPIView, # GET
                             UpdateAPIView, # PATCH
                             DestroyAPIView # DELETE
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





