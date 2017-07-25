'''
Created on 15 mai 2017

@author: bhecquet
'''

import os
import time
from unittest.mock import MagicMock

from django.core.files.images import ImageFile
import django.test

from seleniumRobotServer.settings import MEDIA_ROOT
from snapshotServer.models import Snapshot, TestStep, TestSession, TestCase,\
    TestCaseInSession
from snapshotServer.controllers.DiffComputer import DiffComputer


class TestDiffComputer(django.test.TestCase):
    
    fixtures = ['snapshotServer.yaml']
    mediaDir = MEDIA_ROOT + os.sep + 'documents'

    def tearDown(self):
        DiffComputer.stopThread()
        
        for f in os.listdir(self.mediaDir):
            if f.startswith('img_'):
                os.remove(self.mediaDir + os.sep + f)
 
    def test_createInstance(self):
        """
        Check we always have the same instance
        """
        self.assertIsNone(DiffComputer._instance)
        inst = DiffComputer.getInstance()
        self.assertIsNotNone(inst, "an instance should have been created")
        self.assertEqual(DiffComputer.getInstance(), inst, "the same instance should always be returned")
        
    def test_stopThread(self):
        """
        Thread should be stopped and instance deleted
        """
        inst = DiffComputer.getInstance()
        DiffComputer.stopThread()
        self.assertIsNone(DiffComputer._instance)
        
    def test_computeNow(self):
        """
        Check thread is not started when computing is requested to be done now
        """
        img = ImageFile(open("snapshotServer/tests/data/test_Image1.png", 'rb'))
        s1 = Snapshot(step=TestStep.objects.get(id=1), session=TestSession.objects.get(id=1), testCase=TestCaseInSession.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
        s1.save()
        s1.image.save("img", img)
        s1.save()
        s2 = Snapshot(step=TestStep.objects.get(id=1), session=TestSession.objects.get(id=2), testCase=TestCaseInSession.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
        s2.save()
        s2.image.save("img", img)
        s2.save()

        DiffComputer.getInstance().computeNow(s1, s2)

        # something has been computed
        self.assertIsNotNone(s2.pixelsDiff)
        self.assertEqual(s2.refSnapshot, s1, "refSnapshot should have been updated")
        
    def test_refIsNone(self):
        """
        Check no error is raised when reference is None. Nothing happens for the stepSnapshot
        """
        img = ImageFile(open("snapshotServer/tests/data/test_Image1.png", 'rb'))
        s2 = Snapshot(step=TestStep.objects.get(id=1), session=TestSession.objects.get(id=2), testCase=TestCaseInSession.objects.get(id=1), refSnapshot=None, pixelsDiff=b'')
        s2.save()
        s2.image.save("img", img)
        s2.save()

        DiffComputer.getInstance().computeNow(None, s2)

        # something has been computed
        self.assertIsNone(s2.pixelsDiff)
        self.assertIsNone(s2.refSnapshot, "refSnapshot should have not been updated")
        
    def test_refImageIsNone(self):
        """
        Check no error is raised when image data is missing
        """
        img = ImageFile(open("snapshotServer/tests/data/test_Image1.png", 'rb'))
        s1 = Snapshot(step=TestStep.objects.get(id=1), session=TestSession.objects.get(id=1), testCase=TestCaseInSession.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(step=TestStep.objects.get(id=1), session=TestSession.objects.get(id=2), testCase=TestCaseInSession.objects.get(id=1), refSnapshot=None, pixelsDiff=b'')
        s2.save()
        s2.image.save("img", img)
        s2.save()

        DiffComputer.getInstance().computeNow(s1, s2)

        # something has been computed
        self.assertIsNone(s2.pixelsDiff)
        self.assertEqual(s2.refSnapshot, s1, "refSnapshot should have been updated")
        
    def test_addJobs(self):
        """
        Check we can ass jobs and they get computed
        """
        img = ImageFile(open("snapshotServer/tests/data/test_Image1.png", 'rb'))
        s1 = Snapshot(step=TestStep.objects.get(id=1), session=TestSession.objects.get(id=1), testCase=TestCaseInSession.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
        s1.save()
        s1.image.save("img", img)
        s1.save()
        s2 = Snapshot(step=TestStep.objects.get(id=1), session=TestSession.objects.get(id=2), testCase=TestCaseInSession.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
        s2.save()
        s2.image.save("img", img)
        s2.save()
        s3 = Snapshot(step=TestStep.objects.get(id=1), session=TestSession.objects.get(id=3), testCase=TestCaseInSession.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
        s3.save()
        s3.image.save("img", img)
        s3.save()

        diffComputer = DiffComputer.getInstance()
        diffComputer.addJobs(s1, s2, checkTestMode=False)
        diffComputer.addJobs(s1, s3, checkTestMode=False)
        time.sleep(1)
        diffComputer.stopThread()
        
        # something has been computed
        self.assertIsNotNone(s2.pixelsDiff)
        self.assertIsNotNone(s3.pixelsDiff)
        
    def test_errorWhileComputing(self):
        """
        Check that if an error occurs during computing, 
        """
        s1 = Snapshot(step=TestStep.objects.get(id=1), session=TestSession.objects.get(id=1), testCase=TestCaseInSession.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(step=TestStep.objects.get(id=1), session=TestSession.objects.get(id=2), testCase=TestCaseInSession.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
        s2.save()
        diffComputer = DiffComputer.getInstance()
        diffComputer._computeDiff = MagicMock(side_effect=Exception("error while computing"))
        diffComputer.addJobs(s1, s2, checkTestMode=False)
        time.sleep(0.7)
        self.assertIsNotNone(DiffComputer._instance, "thread should still be running")