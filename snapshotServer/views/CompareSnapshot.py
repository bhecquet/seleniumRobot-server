'''
Created on 4 mai 2017

@author: behe
'''

from django.views.generic import ListView
from snapshotServer.models import TestSession, TestCase
from django.shortcuts import get_object_or_404

class SessionList(ListView):
    model = TestSession
    template_name = "snapshotServer/compare.html"
    
class TestList(ListView):
    template_name = "snapshotServer/testList.html"
    
    def get_queryset(self):
        return TestCase.objects.filter(testsession=self.args[0])
    
class StepList(ListView):
    template_name = "snapshotServer/stepList.html"
    
    def get_queryset(self):
        try:
            return TestCase.objects.get(id=self.args[0]).testSteps.all()
        except:
            return []