'''
Created on 4 mai 2017

@author: bhecquet
'''
from snapshotServer.serializers import SnapshotSerializer, TestStepSerializer, \
    TestSessionSerializer, ExcludeZoneSerializer, TestCaseInSessionSerializer,\
    StepResultSerializer
from rest_framework import viewsets
from snapshotServer.models import Snapshot, TestStep, TestSession, ExcludeZone, TestCaseInSession, StepResult
from commonsServer.views.viewsets import BaseViewSet

class TestSessionViewSet(BaseViewSet):
    queryset = TestSession.objects.all()
    serializer_class = TestSessionSerializer

class TestCaseInSessionViewSet(BaseViewSet):
    queryset = TestCaseInSession.objects.all()
    serializer_class = TestCaseInSessionSerializer
    
class TestStepViewSet(BaseViewSet):
    queryset = TestStep.objects.all()
    serializer_class = TestStepSerializer
    
class SnapshotViewSet(viewsets.ModelViewSet):
    queryset = Snapshot.objects.all()
    serializer_class = SnapshotSerializer
    
class StepResultViewSet(viewsets.ModelViewSet):
    queryset = StepResult.objects.all()
    serializer_class = StepResultSerializer
    
class ExcludeZoneViewSet(BaseViewSet):
    queryset = ExcludeZone.objects.all()
    serializer_class = ExcludeZoneSerializer
