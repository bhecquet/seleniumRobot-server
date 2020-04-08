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

    def test_is_ok_with_all_step_result_ok(self):
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = TestStep.objects.get(pk=2)
        s2 = TestStep.objects.get(pk=3)
        sr1 = StepResult(step=s1, testCase=tcs, result=True)
        sr1.save()
        sr2 = StepResult(step=s2, testCase=tcs, result=True)
        sr2.save()
        
        self.assertTrue(tcs.isOkWithResult())

    def test_is_ok_without_steps(self):
        tcs = TestCaseInSession.objects.get(pk=5)
        
        self.assertTrue(tcs.isOkWithResult())

    def test_is_ok_with_one_step_ko(self):
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = TestStep.objects.get(pk=2)
        s2 = TestStep.objects.get(pk=3)
        sr1 = StepResult(step=s1, testCase=tcs, result=False)
        sr1.save()
        sr2 = StepResult(step=s2, testCase=tcs, result=True)
        sr2.save()
        
        self.assertFalse(tcs.isOkWithResult())
        
    
    def test_is_ok_with_all_snapshot_ok(self):
        tcs = TestCaseInSession.objects.get(pk=10)
        s1 = StepResult.objects.get(pk=5)
        s2 = StepResult.objects.get(pk=6)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        s1 = Snapshot(stepResult=s1, refSnapshot=initial_ref_snapshot, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(stepResult=s2, refSnapshot=initial_ref_snapshot, pixelsDiff=None)
        s2.save()
        
        self.assertTrue(tcs.isOkWithSnapshots())
        
    
    def test_is_not_computed(self):
        """
        When at least one snapshot is not computed, 'isComputed' is False
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = Snapshot.objects.get(pk=5)
        s2 = Snapshot.objects.get(pk=6)
        s3 = Snapshot.objects.get(pk=7)
        s1.computed = True
        s1.save()
        s2.computed = True
        s2.save()
        
        self.assertFalse(tcs.computed())
    
    def test_is_computed(self):
        """
        When all snapshots are computed, 'isComputed' is True
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = Snapshot.objects.get(pk=5)
        s2 = Snapshot.objects.get(pk=6)
        s3 = Snapshot.objects.get(pk=7)
        s1.computed = True
        s1.save()
        s2.computed = True
        s2.save()
        s3.computed = True
        s3.save()
        
        self.assertTrue(tcs.computed())
    
    def test_is_computed_no_snapshots(self):
        """
        When no snpashots are present, 'isComputed' is True
        """
        tcs = TestCaseInSession.objects.get(pk=10)

        self.assertTrue(tcs.computed())
    
    
    def test_is_ok_with_all_snapshot_ok_2(self):
        """
        Same as above but content of pixelDiffs is an empty list
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = StepResult.objects.get(pk=5)
        s2 = StepResult.objects.get(pk=6)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        s1 = Snapshot(stepResult=s1, refSnapshot=initial_ref_snapshot, pixelsDiff=pickle.dumps([]))
        s1.save()
        s2 = Snapshot(stepResult=s2, refSnapshot=initial_ref_snapshot, pixelsDiff=pickle.dumps([]))
        s2.save()
        
        self.assertTrue(tcs.isOkWithSnapshots())
    
    def test_is_ok_with_all_asnapshot_ko(self):
        tcs = TestCaseInSession.objects.get(pk=5)
        s1 = StepResult.objects.get(pk=5)
        s2 = StepResult.objects.get(pk=6)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        
        # some diffs for first picture
        s1 = Snapshot(stepResult=s1, refSnapshot=initial_ref_snapshot, pixelsDiff=pickle.dumps([(1,1)]))
        s1.save()
        s2 = Snapshot(stepResult=s2, refSnapshot=initial_ref_snapshot, pixelsDiff=pickle.dumps([]))
        s2.save()
        
        self.assertFalse(tcs.isOkWithSnapshots())
