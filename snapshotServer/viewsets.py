'''
Created on 4 mai 2017

@author: behe
'''
from snapshotServer.serializers import UserSerializer, GroupSerializer, \
    SnapshotSerializer, ApplicationSerializer, TestEnvironmentSerializer, \
    TestCaseSerializer, TestStepSerializer, VersionSerializer, \
    TestSessionSerializer
from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render
from rest_framework import viewsets
from snapshotServer.models import Snapshot, Application, TestEnvironment, \
    TestCase, TestStep, Difference, Version, TestSession


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
    
class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    
class VersionViewSet(viewsets.ModelViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    
class TestEnvironmentViewSet(viewsets.ModelViewSet):
    queryset = TestEnvironment.objects.all()
    serializer_class = TestEnvironmentSerializer
    
class TestSessionViewSet(viewsets.ModelViewSet):
    queryset = TestSession.objects.all()
    serializer_class = TestSessionSerializer
    
class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    
class TestStepViewSet(viewsets.ModelViewSet):
    queryset = TestStep.objects.all()
    serializer_class = TestStepSerializer
    
class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer
