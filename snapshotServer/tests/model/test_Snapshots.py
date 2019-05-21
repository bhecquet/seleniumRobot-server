'''
Created on 11 mai 2017

@author: bhecquet
'''
import django.test

from snapshotServer.models import Snapshot, Application, Version, TestStep, \
    TestSession, TestEnvironment, TestCase, TestCaseInSession, StepResult


class TestSnapshots(django.test.TestCase):
    
    def setUp(self):
        super(TestSnapshots, self).setUp()
        self.app = Application(name="test")
        self.app.save()
        self.v1 = Version(application=self.app, name='1.0')
        self.v1.save()
        self.v2 = Version(application=self.app, name='2.0')
        self.v2.save()
        env = TestEnvironment(name='DEV')
        env.save()
        self.session1 = TestSession(sessionId="1234", date="2017-05-05", browser="firefox", environment=env, version=self.v1)
        self.session1.save()
        self.session2 = TestSession(sessionId="1235", date="2017-05-05", browser="firefox", environment=env, version=self.v1)
        self.session2.save()
        self.session3 = TestSession(sessionId="1236", date="2017-05-05", browser="firefox", environment=env, version=self.v2)
        self.session3.save()
        self.session4 = TestSession(sessionId="1237", date="2017-05-05", browser="firefox", environment=env, version=self.v2)
        self.session4.save()
        self.step = TestStep(name="step1")
        self.step.save()
        self.tc1 = TestCase(name="case1", application=self.app)
        self.tc1.save()
        self.tcs1 = TestCaseInSession(testCase=self.tc1, session=self.session1)
        self.tcs1.save()
        self.tcs2 = TestCaseInSession(testCase=self.tc1, session=self.session2)
        self.tcs2.save()
        self.tcs3 = TestCaseInSession(testCase=self.tc1, session=self.session3)
        self.tcs3.save()
        self.tcs4 = TestCaseInSession(testCase=self.tc1, session=self.session4)
        self.tcs4.save()
        self.tcs1.testSteps.set([self.step])
        self.tcs1.save()
        self.tcs2.testSteps.set([self.step])
        self.tcs2.save()
        self.tsr1 = StepResult(step=self.step, testCase=self.tcs1, result=True)
        self.tsr1.save()
        self.tsr2 = StepResult(step=self.step, testCase=self.tcs2, result=True)
        self.tsr2.save()
        self.tsr3 = StepResult(step=self.step, testCase=self.tcs3, result=True)
        self.tsr3.save()
        self.tsr4 = StepResult(step=self.step, testCase=self.tcs4, result=True)
        self.tsr4.save()
    
    def test_noNextSnapshots(self):
        """
        check that we do not look at ourself when searching next snapshots
        """
        s1 = Snapshot(stepResult=self.tsr1, image=None, refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(stepResult=self.tsr2, image=None, refSnapshot=s1, pixelsDiff=None)
        s2.save()
        self.assertEqual(s2.snapshotsUntilNextRef(s2.refSnapshot), [], "No next snapshot should be found")
    
    def test_nextSnapshotsWithNoRef(self):
        s1 = Snapshot(stepResult=self.tsr1, image=None, refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(stepResult=self.tsr2, image=None, refSnapshot=s1, pixelsDiff=None)
        s2.save()
        self.assertEqual(s1.snapshotsUntilNextRef(s1), [s2], "One snapshot should be found")
    
    def test_nextSnapshotsWithRef(self):
        """
        Check that the next reference snapshot (s4) is not rendered but pictures from the next version are
        """
        s1 = Snapshot(stepResult=self.tsr1, image=None, refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(stepResult=self.tsr2, image=None, refSnapshot=s1, pixelsDiff=None)
        s2.save()
        s3 = Snapshot(stepResult=self.tsr3, image=None, refSnapshot=s1, pixelsDiff=None)
        s3.save()
        s4 = Snapshot(stepResult=self.tsr4, image=None, refSnapshot=None, pixelsDiff=None)
        s4.save()
        self.assertEqual(s1.snapshotsUntilNextRef(s1), [s2, s3], "2 snapshots should be found")
    
    def test_nextSnapshotsWithLowerVersion(self):
        """
        We should not give snapshots from a lower version
        """
        s0 = Snapshot(stepResult=self.tsr3, image=None, refSnapshot=None, pixelsDiff=None)
        s0.save()
        s1 = Snapshot(stepResult=self.tsr1, image=None, refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(stepResult=self.tsr2, image=None, refSnapshot=s1, pixelsDiff=None)
        s2.save()
        s3 = Snapshot(stepResult=self.tsr3, image=None, refSnapshot=s0, pixelsDiff=None)
        s3.save()

        self.assertEqual(s1.snapshotsUntilNextRef(s1), [s2], "One snapshot should be found")