'''
Created on 11 mai 2017

@author: bhecquet
'''
import django.test

from snapshotServer.models import Snapshot, Application, Version, TestStep, \
    TestSession, TestEnvironment, TestCase


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
        self.session1 = TestSession(sessionId="1234", date="2017-05-05", browser="firefox", environment=env)
        self.session1.save()
        self.session2 = TestSession(sessionId="1235", date="2017-05-05", browser="firefox", environment=env)
        self.session2.save()
        self.session3 = TestSession(sessionId="1236", date="2017-05-05", browser="firefox", environment=env)
        self.session3.save()
        self.session4 = TestSession(sessionId="1237", date="2017-05-05", browser="firefox", environment=env)
        self.session4.save()
        self.step = TestStep(name="step1")
        self.step.save()
        self.tc1 = TestCase(name="case1", version=self.v1)
        self.tc1.save()
        self.tc2 = TestCase(name="case1", version=self.v2)
        self.tc2.save()
        self.tc1.testSteps = [self.step]
        self.tc1.save()
        self.tc2.testSteps = [self.step]
        self.tc2.save()
    
    def test_noNextSnapshots(self):
        s1 = Snapshot(step=self.step, image=None, session=self.session1, testCase=self.tc1, refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(step=self.step, image=None, session=self.session2, testCase=self.tc1, refSnapshot=s1, pixelsDiff=None)
        s2.save()
        self.assertEqual(s2.snapshotsUntilNextRef(), [], "No next snapshot should be found")
    
    def test_nextSnapshotsWithNoRef(self):
        s1 = Snapshot(step=self.step, image=None, session=self.session1, testCase=self.tc1, refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(step=self.step, image=None, session=self.session2, testCase=self.tc1, refSnapshot=s1, pixelsDiff=None)
        s2.save()
        self.assertEqual(s1.snapshotsUntilNextRef(), [s2], "One snapshot should be found")
    
    def test_nextSnapshotsWithRef(self):
        s1 = Snapshot(step=self.step, image=None, session=self.session1, testCase=self.tc1, refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(step=self.step, image=None, session=self.session2, testCase=self.tc1, refSnapshot=s1, pixelsDiff=None)
        s2.save()
        s3 = Snapshot(step=self.step, image=None, session=self.session3, testCase=self.tc2, refSnapshot=s1, pixelsDiff=None)
        s3.save()
        s4 = Snapshot(step=self.step, image=None, session=self.session4, testCase=self.tc2, refSnapshot=None, pixelsDiff=None)
        s4.save()
        self.assertEqual(s1.snapshotsUntilNextRef(), [s2, s3], "One snapshot should be found")
    
    def test_nextSnapshotsWithLowerVersion(self):
        """
        We should not give snapshots from a lower version
        """
        s0 = Snapshot(step=self.step, image=None, session=self.session3, testCase=self.tc1, refSnapshot=None, pixelsDiff=None)
        s0.save()
        s1 = Snapshot(step=self.step, image=None, session=self.session1, testCase=self.tc2, refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(step=self.step, image=None, session=self.session2, testCase=self.tc2, refSnapshot=s1, pixelsDiff=None)
        s2.save()
        s3 = Snapshot(step=self.step, image=None, session=self.session3, testCase=self.tc1, refSnapshot=s0, pixelsDiff=None)
        s3.save()

        self.assertEqual(s1.snapshotsUntilNextRef(), [s2], "One snapshot should be found")