'''
Created on 11 mai 2017

@author: bhecquet
'''
from django.test import TestCase
from snapshotServer.models import Version, Application, TestCaseInSession,\
    TestStep, StepResult, Snapshot
import pickle


class TestTestCases(TestCase):

    fixtures = ['snapshotServer.yaml']

    def test_isOkWithAllStepResultOk(self):
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = TestStep.objects.get(pk=2)
        s2 = TestStep.objects.get(pk=3)
        sr1 = StepResult(step=s1, testCase=tcs, result=True)
        sr1.save()
        sr2 = StepResult(step=s2, testCase=tcs, result=True)
        sr2.save()
        
        self.assertTrue(tcs.isOkWithResult())

    def test_isOkWithoutSteps(self):
        tcs = TestCaseInSession.objects.get(pk=5)
        
        self.assertTrue(tcs.isOkWithResult())

    def test_isOkWithOneStepKo(self):
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = TestStep.objects.get(pk=2)
        s2 = TestStep.objects.get(pk=3)
        sr1 = StepResult(step=s1, testCase=tcs, result=False)
        sr1.save()
        sr2 = StepResult(step=s2, testCase=tcs, result=True)
        sr2.save()
        
        self.assertFalse(tcs.isOkWithResult())
        
    
    def test_isOkWithAllSnapshotOk(self):
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = StepResult.objects.get(pk=5)
        s2 = StepResult.objects.get(pk=6)
        initialRefSnapshot = Snapshot.objects.get(id=1)
        s1 = Snapshot(stepResult=s1, refSnapshot=initialRefSnapshot, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(stepResult=s2, refSnapshot=initialRefSnapshot, pixelsDiff=None)
        s2.save()
        
        self.assertTrue(tcs.isOkWithSnapshots())
    
    
    def test_isOkWithAllSnapshotOk2(self):
        """
        Same as above but content of pixelDiffs is an empty list
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = StepResult.objects.get(pk=5)
        s2 = StepResult.objects.get(pk=6)
        initialRefSnapshot = Snapshot.objects.get(id=1)
        s1 = Snapshot(stepResult=s1, refSnapshot=initialRefSnapshot, pixelsDiff=pickle.dumps([]))
        s1.save()
        s2 = Snapshot(stepResult=s2, refSnapshot=initialRefSnapshot, pixelsDiff=pickle.dumps([]))
        s2.save()
        
        self.assertTrue(tcs.isOkWithSnapshots())
    
    def test_isOkWithAllASnapshotKo(self):
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = StepResult.objects.get(pk=5)
        s2 = StepResult.objects.get(pk=6)
        initialRefSnapshot = Snapshot.objects.get(id=1)
        
        # some diffs for first picture
        s1 = Snapshot(stepResult=s1, refSnapshot=initialRefSnapshot, pixelsDiff=pickle.dumps([(1,1)]))
        s1.save()
        s2 = Snapshot(stepResult=s2, refSnapshot=initialRefSnapshot, pixelsDiff=pickle.dumps([]))
        s2.save()
        
        self.assertFalse(tcs.isOkWithSnapshots())
