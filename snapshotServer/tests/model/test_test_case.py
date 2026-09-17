'''
Created on 11 mai 2017

@author: bhecquet
'''
from snapshotServer.models import TestCaseInSession,\
    TestStep, StepResult, Snapshot, TestSession
import pickle
from snapshotServer.tests import SnapshotTestCase


class TestTestCases(SnapshotTestCase):

    fixtures = ['test_test_case.yaml']

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
        st1 = StepResult.objects.get(pk=12)
        st2 = StepResult.objects.get(pk=13)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        s1 = Snapshot(stepResult=st1, refSnapshot=initial_ref_snapshot, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(stepResult=st2, refSnapshot=initial_ref_snapshot, pixelsDiff=None)
        s2.save()
        
        self.assertTrue(tcs.isOkWithSnapshots())
        
    def test_is_ok_with_all_snapshot_ok_and_one_computing_error(self):
        """
        2 snapshots whose one has computing error, other is ok
        Result is undefined, we return None
        """
        tcs = TestCaseInSession.objects.get(pk=10)
        st1 = StepResult.objects.get(pk=12)
        st2 = StepResult.objects.get(pk=13)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        s1 = Snapshot(stepResult=st1, refSnapshot=initial_ref_snapshot, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(stepResult=st2, refSnapshot=initial_ref_snapshot, pixelsDiff=None)
        s2.computingError = 'some error'
        s2.save()
        
        self.assertIsNone(tcs.isOkWithSnapshots())
        
    def test_is_ok_with_all_snapshot_ko_and_one_computing_error(self):
        """
        2 snapshots whose one has computing error, other is ko
        Result is ko, we return False
        """
        tcs = TestCaseInSession.objects.get(pk=10)
        st1 = StepResult.objects.get(pk=12)
        st2 = StepResult.objects.get(pk=13)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        s1 = Snapshot(stepResult=st1, refSnapshot=initial_ref_snapshot, pixelsDiff=pickle.dumps([(1,1)]))
        s1.save()
        s2 = Snapshot(stepResult=st2, refSnapshot=initial_ref_snapshot, pixelsDiff=None)
        s2.computingError = 'some error'
        s2.save()
        
        self.assertFalse(tcs.isOkWithSnapshots())
        
    def test_is_ok_with_all_snapshot_all_computing_error(self):
        """
        2 snapshots, all have computing errors
        Result is undefined, we return None
        """
        tcs = TestCaseInSession.objects.get(pk=10)
        st1 = StepResult.objects.get(pk=12)
        st2 = StepResult.objects.get(pk=13)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        s1 = Snapshot(stepResult=st1, refSnapshot=initial_ref_snapshot, pixelsDiff=None)
        s1.computingError = 'some error'
        s1.save()
        s2 = Snapshot(stepResult=st2, refSnapshot=initial_ref_snapshot, pixelsDiff=None)
        s2.computingError = 'some error'
        s2.save()
        
        self.assertIsNone(tcs.isOkWithSnapshots())
    
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
    
    def test_is_ok_with_all_snapshot_ko(self):
        """
        Test case when at least one snapshot comparison is KO
        """
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
    
    def test_final_status_without_snapshot_comparison(self):
        """
        When snapshot comparison is disabled for the session, final status is the test execution status,
        whatever the snapshot comparison result is
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        tcs.status = 'SUCCESS'
        tcs.save()
        session = TestSession.objects.get(pk=6)
        session.compareSnapshot = False
        session.save()

        s1 = StepResult.objects.get(pk=5)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        Snapshot(stepResult=s1, refSnapshot=initial_ref_snapshot, pixelsDiff=pickle.dumps([(1, 1)])).save()

        self.assertEqual('SUCCESS', tcs.finalStatus())

    def test_final_status_with_snapshot_comparison_display_only(self):
        """
        When snapshot comparison is enabled but behaviour is 'DISPLAY_ONLY', final status is the test execution
        status, even if snapshot comparison is KO
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        tcs.status = 'SUCCESS'
        tcs.save()
        session = TestSession.objects.get(pk=6)
        session.compareSnapshot = True
        session.compareSnapshotBehaviour = 'DISPLAY_ONLY'
        session.save()

        s1 = StepResult.objects.get(pk=5)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        Snapshot(stepResult=s1, refSnapshot=initial_ref_snapshot, pixelsDiff=pickle.dumps([(1, 1)])).save()

        self.assertEqual('SUCCESS', tcs.finalStatus())

    def test_final_status_with_snapshot_comparison_change_test_result_and_snapshot_ok(self):
        """
        When snapshot comparison is enabled with 'CHANGE_TEST_RESULT' behaviour, and snapshot comparison is OK,
        final status is not changed
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        tcs.status = 'SUCCESS'
        tcs.save()
        session = TestSession.objects.get(pk=6)
        session.compareSnapshot = True
        session.compareSnapshotBehaviour = 'CHANGE_TEST_RESULT'
        session.save()

        s1 = StepResult.objects.get(pk=5)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        Snapshot(stepResult=s1, refSnapshot=initial_ref_snapshot, pixelsDiff=pickle.dumps([])).save()

        self.assertEqual('SUCCESS', tcs.finalStatus())

    def test_final_status_with_snapshot_comparison_change_test_result_and_snapshot_ko(self):
        """
        When snapshot comparison is enabled with 'CHANGE_TEST_RESULT' behaviour, and snapshot comparison is KO,
        final status becomes 'FAILURE', even if test execution was successful
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        tcs.status = 'SUCCESS'
        tcs.save()
        session = TestSession.objects.get(pk=6)
        session.compareSnapshot = True
        session.compareSnapshotBehaviour = 'CHANGE_TEST_RESULT'
        session.save()

        s1 = StepResult.objects.get(pk=5)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        Snapshot(stepResult=s1, refSnapshot=initial_ref_snapshot, pixelsDiff=pickle.dumps([(1, 1)])).save()

        self.assertEqual('FAILURE', tcs.finalStatus())

    def test_final_status_with_snapshot_comparison_change_test_result_and_undefined_result(self):
        """
        When snapshot comparison is enabled with 'CHANGE_TEST_RESULT' behaviour, but comparison result is
        undefined (e.g: computing error), final status is not changed
        """
        tcs = TestCaseInSession.objects.get(pk=5)
        tcs.status = 'SUCCESS'
        tcs.save()
        session = TestSession.objects.get(pk=6)
        session.compareSnapshot = True
        session.compareSnapshotBehaviour = 'CHANGE_TEST_RESULT'
        session.save()

        s1 = StepResult.objects.get(pk=5)
        initial_ref_snapshot = Snapshot.objects.get(id=1)
        snapshot = Snapshot(stepResult=s1, refSnapshot=initial_ref_snapshot, pixelsDiff=None)
        snapshot.computingError = 'some error'
        snapshot.save()

        self.assertEqual('SUCCESS', tcs.finalStatus())

    