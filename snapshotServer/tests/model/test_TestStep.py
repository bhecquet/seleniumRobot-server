'''
Created on 11 mai 2017

@author: bhecquet
'''
from django.test import TestCase
from snapshotServer.models import Version, Application, TestCaseInSession,\
    TestStep, StepResult, Snapshot
import pickle


class TestTestStep(TestCase):

    fixtures = ['snapshotServer.yaml']

    def test_is_ok_with_all_snapshots_ok_and_result_ok(self):
        """
        Step is OK when all snapshot are OK and step result is OK
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        step = TestStep.objects.get(pk=2)
        step_result = StepResult.objects.get(pk=5) # result of this step is True and associated snapshot have no pixelDiff
        
        self.assertTrue(step.isOkWithSnapshots(tcs))

    def test_is_ok_without_snapshots_ok_and_result_ok(self):
        """
        Step is OK when no snapshot is present and step result is OK
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        step = TestStep.objects.get(pk=2)
        step_result = StepResult(step=step, testCase=tcs, result=True) # step without snapshots
        step_result.save()
        
        self.assertTrue(step.isOkWithSnapshots(tcs))

    def test_is_ko_with_snapshots_ko_and_result_ok(self):
        """
        Step is KO when at least one snapshot is KO even if step result is OK
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        step = TestStep.objects.get(pk=2)
        step_result = StepResult(step=step, testCase=tcs, result=True) # step without snapshots
        step_result.save()
        
        # one snapshot with comparison error
        snapshot1 = Snapshot(stepResult=step_result, image=None, refSnapshot=None, pixelsDiff=b"12345", tooManyDiffs=True)
        snapshot1.save()
        
        # one snapshot without comparison error
        snapshot2 = Snapshot(stepResult=step_result, image=None, refSnapshot=None, pixelsDiff=None, tooManyDiffs=False)
        snapshot2.save()
        
        # Step is KO because one snapshot has comparison error
        self.assertFalse(step.isOkWithSnapshots(tcs))

    def test_is_ko_with_snapshots_ok_and_result_ko(self):
        """
        Step is KO when snapshot is OK even if step result is KO
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        step = TestStep.objects.get(pk=2)
        step_result = StepResult(step=step, testCase=tcs, result=False) # step without snapshots
        step_result.save()
        
        # one snapshot without comparison error
        snapshot1 = Snapshot(stepResult=step_result, image=None, refSnapshot=None, pixelsDiff=None, tooManyDiffs=False)
        snapshot1.save()
        
        # Step is KO because one snapshot has comparison error
        self.assertFalse(step.isOkWithSnapshots(tcs))

    def test_is_ko_without_snapshots_and_result_ko(self):
        """
        Step is OK when no snapshot is present and step result is OK
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        step = TestStep.objects.get(pk=2)
        step_result = StepResult(step=step, testCase=tcs, result=False) # step without snapshots
        step_result.save()
        
        self.assertFalse(step.isOkWithSnapshots(tcs))

    