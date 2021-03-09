'''
Created on 15 mai 2017

@author: bhecquet
'''

import os
import time
from unittest.mock import MagicMock, patch

from django.core.files.images import ImageFile
import django.test

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.models import Snapshot, StepResult, ExcludeZone
from django.conf import settings
from snapshotServer.tests import SnapshotTestCase


class TestDiffComputer(SnapshotTestCase):
    
    fixtures = ['snapshotServer.yaml']
    mediaDir = settings.MEDIA_ROOT + os.sep + 'documents'
 
    def tearDown(self):
        super().tearDown()
         
        for f in os.listdir(self.mediaDir):
            if f.startswith('img_'):
                os.remove(self.mediaDir + os.sep + f)
  
    def test_create_instance(self):
        """
        Check we always have the same instance
        """
        self.assertIsNone(DiffComputer._instance)
        inst = DiffComputer.get_instance()
        self.assertIsNotNone(inst, "an instance should have been created")
        self.assertEqual(DiffComputer.get_instance(), inst, "the same instance should always be returned")
         
    def test_stop_thread(self):
        """
        Thread should be stopped and instance deleted
        """
        inst = DiffComputer.get_instance()
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
            
            self.assertFalse(s1.computed)
            self.assertFalse(s2.computed)
     
            DiffComputer.get_instance().compute_now(s1, s2)
     
            # something has been computed
            self.assertIsNotNone(s2.pixelsDiff)
            self.assertEqual(s2.refSnapshot, s1, "refSnapshot should have been updated")
            
            self.assertFalse(s1.computed) # reference picture, computed flag remains False
            self.assertTrue(s2.computed) # diff computed, flag changed
         
    def test_compute_diff_without_tolerance(self):
        """
        Check difference is found between two different images
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as reference:
            with open("snapshotServer/tests/data/test_Image1Mod.png", 'rb') as step:
                img_reference = ImageFile(reference)
                img_step = ImageFile(step)
                ref_snapshot = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
                ref_snapshot.save()
                ref_snapshot.image.save("img", img_reference)
                ref_snapshot.save()
                step_snapshot = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None)
                step_snapshot.save()
                step_snapshot.image.save("img", img_step)
                step_snapshot.save()
         
                DiffComputer.get_instance().compute_now(ref_snapshot, step_snapshot)
         
                # something has been computed
                self.assertIsNotNone(step_snapshot.pixelsDiff)
                self.assertTrue(step_snapshot.tooManyDiffs)
                self.assertEqual(step_snapshot.refSnapshot, ref_snapshot, "refSnapshot should have been updated")
                
                self.assertTrue(step_snapshot.computed)
                self.assertTrue(step_snapshot.computingError == '')
         
    def test_compute_diff_with_tolerance_higher_than_difference(self):
        """
        Check that even with differences, as tolerance is higher, images are considered the same
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as reference:
            with open("snapshotServer/tests/data/test_Image1Mod.png", 'rb') as step:
                img_reference = ImageFile(reference)
                img_step = ImageFile(step)
                ref_snapshot = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
                ref_snapshot.save()
                ref_snapshot.image.save("img", img_reference)
                ref_snapshot.save()
                step_snapshot = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None, diffTolerance=0.5)
                step_snapshot.save()
                step_snapshot.image.save("img", img_step)
                step_snapshot.save()
         
                DiffComputer.get_instance().compute_now(ref_snapshot, step_snapshot)
         
                # something has been computed
                self.assertIsNotNone(step_snapshot.pixelsDiff)
                self.assertFalse(step_snapshot.tooManyDiffs)
         
    def test_compute_diff_with_tolerance_lower_than_difference(self):
        """
        Check that tooManyDiffs is True as % of differences is higher than tolerance
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as reference:
            with open("snapshotServer/tests/data/test_Image1Mod.png", 'rb') as step:
                img_reference = ImageFile(reference)
                img_step = ImageFile(step)
                ref_snapshot = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
                ref_snapshot.save()
                ref_snapshot.image.save("img", img_reference)
                ref_snapshot.save()
                step_snapshot = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None, diffTolerance=0.005)
                step_snapshot.save()
                step_snapshot.image.save("img", img_step)
                step_snapshot.save()
         
                DiffComputer.get_instance().compute_now(ref_snapshot, step_snapshot)
         
                # something has been computed
                self.assertIsNotNone(step_snapshot.pixelsDiff)
                self.assertTrue(step_snapshot.tooManyDiffs)

         
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
     
            DiffComputer.get_instance().compute_now(None, s2)
     
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
     
            DiffComputer.get_instance().compute_now(s1, s2)
     
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
     
            diff_computer = DiffComputer.get_instance()
            diff_computer.add_jobs(s1, s2, check_test_mode=False)
            diff_computer.add_jobs(s1, s3, check_test_mode=False)
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
        diff_computer = DiffComputer.get_instance()
        diff_computer._compute_diff = MagicMock(side_effect=Exception("error while computing"))
        diff_computer.add_jobs(s1, s2, check_test_mode=False)
        time.sleep(0.7)
        self.assertIsNotNone(DiffComputer._instance, "thread should still be running")
         
    def test_error_while_computing_computed_flag_set(self):
        """
        Check that if an error occurs during _compute_diff() method, 'computed' flag is still set to 'True' whatever the result is, and computingError is filled  
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as reference:
            with open("snapshotServer/tests/data/test_Image1Mod.png", 'rb') as step:
                img_reference = ImageFile(reference)
                img_step = ImageFile(step)
                ref_snapshot = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
                ref_snapshot.save()
                ref_snapshot.image.save("img", img_reference)
                ref_snapshot.save()
                step_snapshot = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None)
                step_snapshot.save()
                step_snapshot.image.save("img", img_step)
                step_snapshot.save()

                diff_computer = DiffComputer.get_instance()
                diff_computer.mark_diff = MagicMock(side_effect=Exception("error while computing"))
                diff_computer.add_jobs(ref_snapshot, step_snapshot, check_test_mode=True)
                time.sleep(2)
                self.assertIsNotNone(DiffComputer._instance, "thread should still be running")
                
                # check error has been saved
                self.assertTrue(Snapshot.objects.get(id=step_snapshot.id).computed)
                self.assertEqual(Snapshot.objects.get(id=step_snapshot.id).computingError, "error while computing")
         
    def test_error_message_reset(self):
        """
        Check that if an error occurs during _compute_diff() method, 'computed' flag is still set to 'True' whatever the result is, and 'computingError' is filled  
        If an other computing is done, and no error occurs, then, 'computingError' is reset to an empty string
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as reference:
            with open("snapshotServer/tests/data/test_Image1Mod.png", 'rb') as step:
                img_reference = ImageFile(reference)
                img_step = ImageFile(step)
                ref_snapshot = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
                ref_snapshot.save()
                ref_snapshot.image.save("img", img_reference)
                ref_snapshot.save()
                step_snapshot = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None)
                step_snapshot.save()
                step_snapshot.image.save("img", img_step)
                step_snapshot.save()

                diff_computer = DiffComputer.get_instance()
                diff_computer.mark_diff = MagicMock(side_effect=Exception("error while computing"))
                diff_computer.add_jobs(ref_snapshot, step_snapshot, check_test_mode=True)
                time.sleep(1)
                self.assertIsNotNone(DiffComputer._instance, "thread should still be running")
                
                # check error has been saved
                self.assertTrue(Snapshot.objects.get(id=step_snapshot.id).computed)
                self.assertEqual(Snapshot.objects.get(id=step_snapshot.id).computingError, "error while computing")
                
                # check error has been removed as computing is ok
                DiffComputer.stopThread() # reset DiffComputer instance
                diff_computer_ok = DiffComputer.get_instance()
                diff_computer_ok.add_jobs(ref_snapshot, step_snapshot, check_test_mode=True)
                time.sleep(1)
                self.assertTrue(Snapshot.objects.get(id=step_snapshot.id).computed)
                self.assertEqual(Snapshot.objects.get(id=step_snapshot.id).computingError, "")
     

    def test_compute_using_exclude_zones_from_ref(self):
        """
        Check that computing takes into account exclude zone from reference snapshot
        """
        
        with patch.object(DiffComputer.picture_comparator, 'getChangedPixels', wraps=DiffComputer.picture_comparator.getChangedPixels) as wrapped_get_changed_pixels:
            with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:
                img = ImageFile(imgFile)
                ref_snapshot = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
                ref_snapshot.save()
                ref_snapshot.image.save("img", img)
                ref_snapshot.save()
                step_snapshot = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None)
                step_snapshot.save()
                step_snapshot.image.save("img", img)
                step_snapshot.save()
                
                exclusion1 = ExcludeZone(x=0, y=0, width=10, height=10, snapshot=ref_snapshot)
                exclusion1.save()
            
                DiffComputer.get_instance().compute_now(ref_snapshot, step_snapshot)
                
                # check exclude zone has been used for comparison
                wrapped_get_changed_pixels.assert_called_with(ref_snapshot.image.path, step_snapshot.image.path, [exclusion1.toRectangle()])             

    def test_compute_using_exclude_zones_from_step(self):
        """
        issue #57: Check that computing takes into account exclude zone from step snapshot that could be added by seleniumRobot
        """
        
        with patch.object(DiffComputer.picture_comparator, 'getChangedPixels', wraps=DiffComputer.picture_comparator.getChangedPixels) as wrapped_get_changed_pixels:
            with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:
                img = ImageFile(imgFile)
                ref_snapshot = Snapshot(stepResult=StepResult.objects.get(id=1), refSnapshot=None, pixelsDiff=None)
                ref_snapshot.save()
                ref_snapshot.image.save("img", img)
                ref_snapshot.save()
                step_snapshot = Snapshot(stepResult=StepResult.objects.get(id=2), refSnapshot=None, pixelsDiff=None)
                step_snapshot.save()
                step_snapshot.image.save("img", img)
                step_snapshot.save()
                
                exclusion1 = ExcludeZone(x=0, y=0, width=10, height=10, snapshot=step_snapshot)
                exclusion1.save()
            
                DiffComputer.get_instance().compute_now(ref_snapshot, step_snapshot)
                
                # check exclude zone has been used for comparison
                wrapped_get_changed_pixels.assert_called_with(ref_snapshot.image.path, step_snapshot.image.path, [exclusion1.toRectangle()])             