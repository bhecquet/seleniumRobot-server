'''
Created on 15 mai 2017

@author: behe
'''

import datetime
import os

from django.urls.base import reverse
import pytz
from rest_framework.test import APITestCase

from seleniumRobotServer.settings import MEDIA_ROOT
from snapshotServer.tests import authenticate_test_client_for_api
from snapshotServer.models import TestCase, TestStep, TestSession, \
    TestEnvironment, Version, Snapshot, TestCaseInSession, Application, \
    StepResult


class TestFileUploadView(APITestCase):
    fixtures = ['snapshotServer.yaml']
    
    mediaDir = MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        authenticate_test_client_for_api(self.client)
        
        # test in a version
        self.testCase = TestCase(name='test upload', application=Application.objects.get(id=1))
        self.testCase.save()
        self.step1 = TestStep.objects.get(id=1)
        
        self.session1 = TestSession(sessionId="8888", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session1.save()
        self.tcs1 = TestCaseInSession(testCase=self.testCase, session=self.session1)
        self.tcs1.save()
        self.sr1 = StepResult(step=self.step1, testCase=self.tcs1, result=True)
        self.sr1.save()
        
        self.session_same_env = TestSession(sessionId="8889", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session_same_env.save()
        self.tcs_same_env = TestCaseInSession(testCase=self.testCase, session=self.session_same_env)
        self.tcs_same_env.save()
        self.step_result_same_env = StepResult(step=self.step1, testCase=self.tcs_same_env, result=True)
        self.step_result_same_env.save()
        
        self.session_other_env = TestSession(sessionId="8890", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=2), ttl=datetime.timedelta(0))
        self.session_other_env.save()
        self.tcs_other_env = TestCaseInSession(testCase=self.testCase, session=self.session_other_env)
        self.tcs_other_env.save()
        self.step_result_other_env = StepResult(step=self.step1, testCase=self.tcs_other_env, result=True)
        self.step_result_other_env.save()
        
        self.session_other_browser = TestSession(sessionId="8891", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="chrome", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session_other_browser.save()
        self.tcs_other_browser = TestCaseInSession(testCase=self.testCase, session=self.session_other_browser)
        self.tcs_other_browser.save()
        self.step_result_other_browser = StepResult(step=self.step1, testCase=self.tcs_other_browser, result=True)
        self.step_result_other_browser.save()
        
        
    def tearDown(self):
        """
        Remove generated files
        """
        
        for f in os.listdir(self.mediaDir):
            if f.startswith('engie'):
                os.remove(self.mediaDir + os.sep + f)
    
    def test_post_snapshot_no_ref(self):
        """
        Check a reference is created when non is found
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot, "the uploaded snapshot should be recorded")
            self.assertTrue(uploaded_snapshot.computed)
            self.assertEqual(uploaded_snapshot.diffTolerance, 0.0)
    
    def test_post_snapshot_no_ref_with_threshold(self):
        """
        Check a reference is created when non is found
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true', 'diffTolerance': 1.5})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot, "the uploaded snapshot should be recorded")
            self.assertTrue(uploaded_snapshot.computed)
            self.assertEqual(uploaded_snapshot.diffTolerance, 1.5)
            
    def test_post_snapshot_existing_ref(self):
        """
        Check we find the reference snapshot when it exists in the same version / same name
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            uploaded_snapshot_1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.step_result_same_env.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot_2 = Snapshot.objects.filter(stepResult__testCase=self.tcs_same_env, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot_2, "the uploaded snapshot should be recorded")
            self.assertEqual(uploaded_snapshot_2.refSnapshot, uploaded_snapshot_1)
            
            # both snapshots are marked as computed as they have been uploaded
            self.assertTrue(uploaded_snapshot_1.computed)
            self.assertTrue(uploaded_snapshot_2.computed)
            
    def test_post_snapshot_multiple_existing_ref(self):
        """
        issue #61: Check that when multiple references exist for the same version / name / env / ..., we take the last one.
        """
        # upload first ref
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            uploaded_snapshot_1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
        
        # upload second snapshot and make it a reference
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            uploaded_snapshot_2 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            uploaded_snapshot_2.refSnapshot = None
            uploaded_snapshot_2.save()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.step_result_same_env.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot_3 = Snapshot.objects.filter(stepResult__testCase=self.tcs_same_env, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot_3, "the uploaded snapshot should be recorded")
            self.assertEqual(uploaded_snapshot_3.refSnapshot, uploaded_snapshot_2, "last snapshot should take the most recent reference snapshot available")
            
            
    def test_post_snapshot_existing_ref_other_env(self):
        """
        Check we cannot find the reference snapshot when it exists in the same version / same browser / same name but for a different environment
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            uploaded_snapshot_1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.step_result_other_env.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot_2 = Snapshot.objects.filter(stepResult__testCase=self.tcs_other_env, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot_2, "the uploaded snapshot should be recorded")
            
            # the uploaded snapshot should not have been associated to 'uploaded_snapshot_1' as environment is different
            self.assertIsNone(uploaded_snapshot_2.refSnapshot)
            
    def test_post_snapshot_existing_ref_other_browser(self):
        """
        Check we cannot find the reference snapshot when it exists in the same version / same environment / same name but for a different browser
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            uploaded_snapshot_1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.step_result_other_browser.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot_2 = Snapshot.objects.filter(stepResult__testCase=self.tcs_other_browser, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot_2, "the uploaded snapshot should be recorded")
            
            # the uploaded snapshot should not have been associated to 'uploaded_snapshot_1' as browser is different
            self.assertIsNone(uploaded_snapshot_2.refSnapshot)
            
    def test_post_snapshot_existing_ref_in_previous_version(self):
        """
        Check that we search for a reference in a previous version if none is found in the current one
        """
        
        # same as self.testCase in a greater version
        session3 = TestSession(sessionId="8890", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=2), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        session3.save()
        tcs3 = TestCaseInSession(testCase=self.testCase, session=session3)
        tcs3.save()
        tcs3.testSteps.set([TestStep.objects.get(id=1)])
        tcs3.save()
        sr3 = StepResult(step=TestStep.objects.get(id=1), testCase=tcs3, result=True)
        sr3.save()
        
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            uploaded_snapshot_1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': sr3.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot_2 = Snapshot.objects.filter(stepResult__testCase=tcs3, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot_2, "the uploaded snapshot should be recorded")
            self.assertEqual(uploaded_snapshot_2.refSnapshot, uploaded_snapshot_1)
        
    def test_post_snapshot_no_picture(self):
        response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'name': 'img', 'compare': 'true'})
        self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_post_snapshot_missing_step(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_post_snapshot_missing_name(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'compare': 'true'})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
