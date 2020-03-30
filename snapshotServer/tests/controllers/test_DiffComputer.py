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
from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.models import Snapshot, StepResult


class TestDiffComputer(django.test.TestCase):
    
    fixtures = ['snapshotServer.yaml']
    mediaDir = MEDIA_ROOT + os.sep + 'documents'
 
    def tearDown(self):
        DiffComputer.stopThread()
         
        for f in os.listdir(self.mediaDir):
            if f.startswith('img_'):
                os.remove(self.mediaDir + os.sep + f)
  
    def test_create_instance(self):
        """
        Check we always have the same instance
        """
        self.assertIsNone(DiffComputer._instance)
        inst = DiffComputer.getInstance()
        self.assertIsNotNone(inst, "an instance should have been created")
        self.assertEqual(DiffComputer.getInstance(), inst, "the same instance should always be returned")
         
    def test_stop_thread(self):
        """
        Thread should be stopped and instance deleted
        """
        inst = DiffComputer.getInstance()
        DiffComputer.stopThread()
        self.assertIsNone(DiffComputer._instance)
         
    def test_compute_now(self):
        """
        Check thread is not started when computing is requested to be done now
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:
            img = ImageFile(imgFile)
            s1 = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
            s1.save()
            s1.image.save("img", img)
            s1.save()
            s2 = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None)
            s2.save()
            s2.image.save("img", img)
            s2.save()
     
            DiffComputer.getInstance().computeNow(s1, s2)
     
            # something has been computed
            self.assertIsNotNone(s2.pixelsDiff)
            self.assertEqual(s2.refSnapshot, s1, "refSnapshot should have been updated")
         
    def test_compute_diff(self):
        """
        Check thread is not started when computing is requested to be done now
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as reference:
            with open("snapshotServer/tests/data/test_Image1Mod.png", 'rb') as step:
                img_reference = ImageFile(reference)
                img_step = ImageFile(step)
                s1 = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
                s1.save()
                s1.image.save("img", img_reference)
                s1.save()
                s2 = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None)
                s2.save()
                s2.image.save("img", img_step)
                s2.save()
         
                DiffComputer.getInstance().computeNow(s1, s2)
         
                # something has been computed
                self.assertIsNotNone(s2.pixelsDiff)
                self.assertTrue(s2.tooManyDiffs)
                self.assertEqual(s2.refSnapshot, s1, "refSnapshot should have been updated")

         
    def test_ref_is_none(self):
        """
        Check no error is raised when reference is None. Nothing happens for the stepSnapshot
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:
            img = ImageFile(imgFile)
            s2 = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=b'')
            s2.save()
            s2.image.save("img", img)
            s2.save()
     
            DiffComputer.getInstance().computeNow(None, s2)
     
            # something has been computed
            self.assertIsNone(s2.pixelsDiff)
            self.assertIsNone(s2.refSnapshot, "refSnapshot should have not been updated")
         
    def test_ref_image_is_none(self):
        """
        Check no error is raised when image data is missing
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:
            img = ImageFile(imgFile)
            s1 = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
            s1.save()
            s2 = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=b'')
            s2.save()
            s2.image.save("img", img)
            s2.save()
     
            DiffComputer.getInstance().computeNow(s1, s2)
     
            # something has been computed
            self.assertIsNone(s2.pixelsDiff)
            self.assertEqual(s2.refSnapshot, s1, "refSnapshot should have been updated")
         
    def test_add_jobs(self):
        """
        Check we can add jobs and they get computed
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:
            img = ImageFile(imgFile)
            s1 = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
            s1.save()
            s1.image.save("img", img)
            s1.save()
            s2 = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None)
            s2.save()
            s2.image.save("img", img)
            s2.save()
            s3 = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
            s3.save()
            s3.image.save("img", img)
            s3.save()
     
            diff_computer = DiffComputer.getInstance()
            diff_computer.addJobs(s1, s2, checkTestMode=False)
            diff_computer.addJobs(s1, s3, checkTestMode=False)
            time.sleep(1)
            diff_computer.stopThread()
             
            # something has been computed
            self.assertIsNotNone(s2.pixelsDiff)
            self.assertIsNotNone(s3.pixelsDiff)
         
    def test_error_while_computing(self):
        """
        Check that if an error occurs during computing, 
        """
        s1 = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
        s1.save()
        s2 = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None)
        s2.save()
        diff_computer = DiffComputer.getInstance()
        diff_computer._computeDiff = MagicMock(side_effect=Exception("error while computing"))
        diff_computer.addJobs(s1, s2, checkTestMode=False)
        time.sleep(0.7)
        self.assertIsNotNone(DiffComputer._instance, "thread should still be running")
         
