'''
Created on 31 mai 2024

@author: S047432
'''
import django.test
import django.core.files
from django.conf import settings
import os
import shutil
from pathlib import Path
from snapshotServer.utils import clean
from snapshotServer.models import TestSession, TestCaseInSession, StepReference,\
    StepResult, File, Snapshot
from django.utils import timezone
from datetime import timedelta

class TestClean(django.test.TestCase):
    
    fixtures = ['snasphotserver_commons.yaml', 'scheduler_test_ok']
    data_dir = Path('snapshotServer/tests/data/')
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    
    def tearDown(self):
        """
        Remove generated files
        """
        
        super().tearDown()
        Path(self.media_dir, 'replaced.txt').unlink(True)
        Path(self.media_dir, 'replaced_video.txt').unlink(True)
        
    
    def test_replace_video(self):
        """
        video is replaced if test session is older than 15 days and test case is OK
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=15, minutes=1)
        session.save()

        video_path = self.data_dir / 'videoCapture.avi'
        shutil.copy(video_path, self.media_dir)
        clean.replace_video()
        
        # check original file has been deleted and replaced in reference
        self.assertFalse(Path(self.media_dir, 'videoCapture.avi').exists())
        self.assertTrue(Path(self.media_dir, 'replaced_video.txt').exists())
        self.assertEquals(File.objects.get(pk=3).file.name, 'documents/replaced_video.txt')
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 30)
    
    def test_do_not_replace_video_for_failed_test(self):
        """
        video is not replaced if test case is failed
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=15, minutes=1)
        session.save()
        
        test_case_in_session = TestCaseInSession.objects.get(pk=1)
        test_case_in_session.status = "FAILURE"
        test_case_in_session.save()
    
        video_path = self.data_dir / 'videoCapture.avi'
        shutil.copy(video_path, self.media_dir)
        clean.replace_video()

        # check original file has not been deleted
        self.assertTrue(Path(self.media_dir, 'videoCapture.avi').exists())
        self.assertFalse(Path(self.media_dir, 'replaced_video.txt').exists())
        self.assertEquals(File.objects.get(pk=3).file.name, 'documents/videoCapture.avi')
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 0)
        
    def test_do_not_replace_video(self):
        """
        HTML is not replaced if test session is younger than 15 days
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=14, hours=23, minutes=59)
        session.save()
        
        video_path = self.data_dir / 'videoCapture.avi'
        shutil.copy(video_path, self.media_dir)
        clean.replace_video()
        
        # check original file has not been deleted
        self.assertTrue(Path(self.media_dir, 'videoCapture.avi').exists())
        self.assertFalse(Path(self.media_dir, 'replaced_video.txt').exists())
        self.assertEquals(File.objects.get(pk=3).file.name, 'documents/videoCapture.avi')
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 0)
        

    
    def test_replace_html(self):
        """
        HTML is replaced if test session is older than 5 days
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=5, minutes=1)
        session.save()
        
        file = File.objects.get(pk=2)
        file.file = 'documents/test.html'
        file.save()
        
        image_path = self.data_dir / 'test.html'
        shutil.copy(image_path, self.media_dir)
        clean.replace_html()
        
        # check original file has been deleted and replaced in reference
        self.assertFalse(Path(self.media_dir, 'test.html').exists())
        self.assertTrue(Path(self.media_dir, 'replaced.txt').exists())
        self.assertEquals(File.objects.get(pk=2).file.name, 'documents/replaced.txt')
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 10)
    
    def test_replace_html_for_failed_test(self):
        """
        HTML is replaced if test session is older than 10 days and test is failed
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=10, minutes=1)
        session.save()
        
        test_case_in_session = TestCaseInSession.objects.get(pk=1)
        test_case_in_session.status = "FAILURE"
        test_case_in_session.save()
    
        image_path = self.data_dir / 'test.html.zip'
        shutil.copy(image_path, self.media_dir)
        clean.replace_html()

        # check original file has been deleted and replaced in reference
        self.assertFalse(Path(self.media_dir, 'test.html.zip').exists())
        self.assertTrue(Path(self.media_dir, 'replaced.txt').exists())
        self.assertEquals(File.objects.get(pk=2).file.name, 'documents/replaced.txt')
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 10)
        
    def test_do_not_replace_html(self):
        """
        HTML is not replaced if test session is younger than 5 days
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=4, hours=23, minutes=59)
        session.save()
        
        image_path = self.data_dir / 'test.html.zip'
        shutil.copy(image_path, self.media_dir)
        clean.replace_html()
        
        self.assertTrue(Path(self.media_dir, 'test.html.zip').exists())
        self.assertEquals(File.objects.get(pk=2).file.name, 'documents/test.html.zip')
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 0)
        
    def test_do_not_replace_non_html(self):
        """
        Only delete HTML files and zipped HTML files
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=5, minutes=1)
        session.save()
        
        file = File.objects.get(pk=2)
        file.file = 'documents/engie.png'
        file.save()
        
        file_path = self.data_dir / 'engie.png'
        shutil.copy(file_path, self.media_dir)
        clean.replace_html()
        
        self.assertEquals(File.objects.get(pk=2).file.name, 'documents/engie.png')
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 10)
            
    def test_do_not_replace_html_for_failed_test(self):
        """
        HTML is not replaced if test session is younger than 10 days and test is failed
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=9, hours=23, minutes=59) 
        session.save()
        
        test_case_in_session = TestCaseInSession.objects.get(pk=1)
        test_case_in_session.status = "FAILURE"
        test_case_in_session.save()
        
        image_path = self.data_dir / 'test.html.zip'
        shutil.copy(image_path, self.media_dir)
        clean.replace_html()
        
        self.assertTrue(Path(self.media_dir, 'test.html.zip').exists())
        self.assertEquals(File.objects.get(pk=2).file.name, 'documents/test.html.zip')
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 0)
        
    def test_compress_image(self):
        """
        Image is compressed if test session is older than 5 days
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=5, minutes=1)
        session.save()
        
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        initial_size = image_path.stat().st_size
        clean.compress_images()
        final_size = Path(self.media_dir, 'engie.png').stat().st_size
        self.assertTrue(final_size < initial_size, f"initial size {initial_size} bytes - final size {final_size} bytes")
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 20)
    
    def test_compress_image_for_failed_test(self):
        """
        Image is compressed if test session is older than 10 days and test is failed
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=10, minutes=1)
        session.save()
        
        test_case_in_session = TestCaseInSession.objects.get(pk=1)
        test_case_in_session.status = "FAILURE"
        test_case_in_session.save()
        
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        initial_size = image_path.stat().st_size
        clean.compress_images()
        final_size = Path(self.media_dir, 'engie.png').stat().st_size
        self.assertTrue(final_size < initial_size, f"initial size {initial_size} bytes - final size {final_size} bytes")
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 20)
        
    def test_do_not_compress_image(self):
        """
        Image is not compressed if test session is younger than 5 days
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=4, hours=23, minutes=59)
        session.save()
        
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        initial_size = image_path.stat().st_size
        clean.compress_images()
        final_size = Path(self.media_dir, 'engie.png').stat().st_size
        self.assertTrue(final_size == initial_size, f"initial size {initial_size} bytes - final size {final_size} bytes")
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 0)
        
    def test_do_not_compress_non_image(self):
        """
        Only compress images
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=5, minutes=1)
        session.save()
        
        file = File.objects.get(pk=1)
        file.file = 'documents/test.html'
        file.save()
        
        file_path = self.data_dir / 'test.html'
        shutil.copy(file_path, self.media_dir)
        initial_size = file_path.stat().st_size
        clean.compress_images()
        final_size = Path(self.media_dir, 'test.html').stat().st_size
        self.assertTrue(final_size == initial_size, f"initial size {initial_size} bytes - final size {final_size} bytes")
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 20)
            
    def test_do_not_compress_image_for_failed_test(self):
        """
        Image is not compressed if test session is younger than 10 days and test is failed
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=9, hours=23, minutes=59) 
        session.save()
        
        test_case_in_session = TestCaseInSession.objects.get(pk=1)
        test_case_in_session.status = "FAILURE"
        test_case_in_session.save()
        
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        initial_size = image_path.stat().st_size
        clean.compress_images()
        final_size = Path(self.media_dir, 'engie.png').stat().st_size
        self.assertTrue(final_size == initial_size, f"initial size {initial_size} bytes - final size {final_size} bytes")
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 0)
        
            
    def test_do_not_compress_image_already_optimized(self):
        """
        Image is not compressed if it has already been optimized
        """
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=4, hours=23, minutes=59)
        session.save()
        
        test_case_in_session = TestCaseInSession.objects.get(pk=1)
        test_case_in_session.optimized = 20
        test_case_in_session.save()
        
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        initial_size = image_path.stat().st_size
        clean.compress_images()
        final_size = Path(self.media_dir, 'engie.png').stat().st_size
        self.assertTrue(final_size == initial_size, f"initial size {initial_size} bytes - final size {final_size} bytes")
        
        self.assertEquals(TestCaseInSession.objects.get(pk=1).optimized, 20)
        
    def test_clean_old_references(self):
        """
        Check old step references are removed if they are older that DELETE_STEP_REFERENCE_AFTER_DAYS setting
        """
        # add file for reference
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        
        StepReference.objects.filter(id=1).update(date = timezone.now() - timedelta(days=30, minutes=1))

        clean.clean_old_references()
            
        # check old step reference has been deleted
        self.assertEqual(len(StepReference.objects.filter(pk=1)), 0)
        
        # check file has also been deleted
        self.assertFalse(Path(self.media_dir, 'engie.png').exists())
        
    def test_do_not_clean_old_references(self):
        """
        Check old step references are NOT removed if they are younger that DELETE_STEP_REFERENCE_AFTER_DAYS setting
        """
        # add file for reference
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        
        StepReference.objects.filter(id=1).update(date = timezone.now() - timedelta(days=29, hours=23, minutes=59))

        clean.clean_old_references()
            
        # check old step reference has been deleted
        self.assertEqual(len(StepReference.objects.filter(pk=1)), 1)
        
        # check file has also been deleted
        self.assertTrue(Path(self.media_dir, 'engie.png').exists())
        
    def test_clean_old_sessions(self):
        """
        Check old sessions are cleaned if they are older than their defined TTL
        """    
        # add file for image file
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=5, minutes=1)
        session.ttl = timedelta(days=5)
        session.save()
        
        clean.clean_old_sessions()
        
        # check session has been deleted (and also all related objects)
        self.assertEqual(len(TestSession.objects.filter(pk=1)), 0)
        self.assertEqual(len(TestCaseInSession.objects.filter(pk=1)), 0)
        self.assertEqual(len(StepResult.objects.filter(pk=1)), 0)
        self.assertEqual(len(File.objects.filter(pk=1)), 0)
        self.assertEqual(len(StepReference.objects.filter(pk=1)), 1) # not deleted because not attached to session
        
        # check file has also been deleted
        self.assertFalse(Path(self.media_dir, 'engie.png').exists())
        
    def test_do_not_clean_old_sessions(self):
        """
        Check old sessions are NOT cleaned if they are younger than their defined TTL
        """    
        # add file for image file
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=4, hours=23, minutes=59)
        session.ttl = timedelta(days=5)
        session.save()
        
        clean.clean_old_sessions()
        
        # check session has not been deleted (and also all related objects)
        self.assertEqual(len(TestSession.objects.filter(pk=1)), 1)
        self.assertEqual(len(TestCaseInSession.objects.filter(pk=1)), 1)
        self.assertEqual(len(StepResult.objects.filter(pk=1)), 1)
        self.assertEqual(len(File.objects.filter(pk=1)), 1)
        self.assertEqual(len(StepReference.objects.filter(pk=1)), 1) # not deleted because not attached to session
        
        # check file has also not been deleted
        self.assertTrue(Path(self.media_dir, 'engie.png').exists())
        
    def test_do_not_clean_old_sessions_with_ttl_0(self):
        """
        Check old sessions are NOT cleaned if their TTL is 0
        """    
        # add file for image file
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=4, hours=23, minutes=59)
        session.ttl = timedelta(days=0)
        session.save()
        
        clean.clean_old_sessions()
        
        # check session has not been deleted (and also all related objects)
        self.assertEqual(len(TestSession.objects.filter(pk=1)), 1)
        self.assertEqual(len(TestCaseInSession.objects.filter(pk=1)), 1)
        self.assertEqual(len(StepResult.objects.filter(pk=1)), 1)
        self.assertEqual(len(File.objects.filter(pk=1)), 1)
        self.assertEqual(len(StepReference.objects.filter(pk=1)), 1) # not deleted because not attached to session
        
        # check file has also not been deleted
        self.assertTrue(Path(self.media_dir, 'engie.png').exists())
        
          
    def test_do_not_clean_old_sessions_with_reference_snapshot(self):
        """
        Check old sessions are NOT cleaned if they hold at least one reference snapshot
        """    
        # add file for image file
        image_path = self.data_dir / 'engie.png'
        shutil.copy(image_path, self.media_dir)
        
        session = TestSession.objects.get(pk=1)
        session.date = timezone.now() - timedelta(days=4, hours=23, minutes=59)
        session.ttl = timedelta(days=0)
        session.save()
        
        with open(image_path, 'rb') as image:
            snapshot = Snapshot(stepResult=StepResult.objects.get(pk=1),
                                image=django.core.files.File(image))
            snapshot.save()
            
        clean.clean_old_sessions()
        
        # check session has not been deleted 
        self.assertEqual(len(TestSession.objects.filter(pk=1)), 1)
        self.assertEqual(len(Snapshot.objects.filter(pk=snapshot.id)), 1)

    