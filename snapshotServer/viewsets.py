'''
Created on 4 mai 2017

@author: bhecquet
'''
from snapshotServer.serializers import UserSerializer, GroupSerializer, \
    SnapshotSerializer, ApplicationSerializer, TestEnvironmentSerializer, \
    TestCaseSerializer, TestStepSerializer, VersionSerializer, \
    TestSessionSerializer, ExcludeZoneSerializer
from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from rest_framework import viewsets
from snapshotServer.models import Snapshot, Application, TestEnvironment, \
    TestCase, TestStep, Version, TestSession, ExcludeZone
from rest_framework.utils.serializer_helpers import ReturnDict


class BaseViewSet(viewsets.ModelViewSet):
    
    def perform_create(self, serializer):
        """
        Do not create an object if it already exists
        """
        objects = self.serializer_class.Meta.model.objects.all()
        for key, value in serializer.validated_data.items():
            if type(value) == list:
                
                objects = objects.filter(**{key + '__in': value})
            else:
                objects = objects.filter(**{key: value})
    
        if not objects:
            super(BaseViewSet, self).perform_create(serializer)
        else:
            serializer.data.serializer._data.update({'id': objects[0].id})

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    
class ApplicationViewSet(BaseViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    
class VersionViewSet(BaseViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    
class TestEnvironmentViewSet(BaseViewSet):
    queryset = TestEnvironment.objects.all()
    serializer_class = TestEnvironmentSerializer
    
class TestSessionViewSet(BaseViewSet):
    queryset = TestSession.objects.all()
    serializer_class = TestSessionSerializer
    
class TestCaseViewSet(BaseViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    
class TestStepViewSet(BaseViewSet):
    queryset = TestStep.objects.all()
    serializer_class = TestStepSerializer
    
class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer
    
class ExcludeZoneViewSet(BaseViewSet):
    queryset = ExcludeZone.objects.all()
    serializer_class = ExcludeZoneSerializer
