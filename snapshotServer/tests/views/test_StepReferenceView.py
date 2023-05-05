'''
Created on 15 mai 2017

@author: behe
'''

import datetime
import os

from django.urls.base import reverse
import pytz
from rest_framework.test import APITestCase

from snapshotServer.tests import authenticate_test_client_for_api
from snapshotServer.models import TestCase, TestStep, TestSession, \
    TestEnvironment, Version, Snapshot, TestCaseInSession, Application, \
    StepResult, StepReference

from django.conf import settings
import io

class TestStepReferenceView(APITestCase):
    fixtures = ['snapshotServer.yaml']
    
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    reference_dir = os.path.join(media_dir, 'references', 'infotel', 'test upload')
    
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
         
        self.session_other_version = TestSession(sessionId="8892", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=2), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session_other_version.save()
        self.tcs_other_version = TestCaseInSession(testCase=self.testCase, session=self.session_other_version)
        self.tcs_other_version.save()
        self.step_result_other_version = StepResult(step=self.step1, testCase=self.tcs_other_version, result=True)
        self.step_result_other_version.save()
        
        
    def tearDown(self):
        """
        Remove generated files
        """
        
        super().tearDown()
        
        for f in os.listdir(self.reference_dir):
            if f.startswith('engie'):
                os.remove(self.reference_dir + os.sep + f)
    
    def test_get_snapshot(self):
        """
        Check we can get reference snapshot if it exists
        """
        
        # upload image to be tested
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
            
        response = self.client.get(reverse('stepReference', kwargs={'step_result_id': self.sr1.id}))
        self.assertEqual(response.status_code, 200, 'status code should be 200')
        self.assertEqual(response.headers['Content-Length'], '14378')
        io.BytesIO(response.content).getvalue()
           
            
    
    def test_post_snapshot_no_ref(self):
        """
        Check a reference step is created when none is found
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_reference = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1, version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1)).last()
            self.assertIsNotNone(uploaded_reference, "the uploaded snapshot should be recorded")
            
            self.assertTrue(os.path.isfile(os.path.join(self.reference_dir, 'engie.png')))
            
    def test_post_snapshot_existing_ref(self):
        """
        Check we find the reference step when it exists in the same version / same name
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
            uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
            uploaded_file1 = uploaded_reference_1.image.path
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.step_result_same_env.id, 'image': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_reference_2 = StepReference.objects.filter(testCase=self.tcs_same_env.testCase, testStep__id=1, version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1)).last()
            self.assertIsNotNone(uploaded_reference_2, "the uploaded snapshot should be recorded")
            self.assertEqual(uploaded_reference_2, uploaded_reference_1)
            uploaded_file2 = uploaded_reference_2.image.path
            
            # check the previous file has been deleted, so that we do not store old references indefinitely
            self.assertFalse(os.path.isfile(uploaded_file1))
            self.assertTrue(os.path.isfile(uploaded_file2))
            
    def test_post_snapshot_existing_ref_other_env(self):
        """
        Check a reference step is created when none is found for the same environment
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
            uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.step_result_other_env.id, 'image': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_reference_2 = StepReference.objects.filter(testCase=self.tcs_other_env.testCase, version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=2), testStep__id=1).last()
            self.assertIsNotNone(uploaded_reference_2, "the uploaded snapshot should be recorded")
            self.assertNotEqual(uploaded_reference_2, uploaded_reference_1)
            
    def test_post_snapshot_existing_ref_other_version(self):
        """
        Check a reference step is created when none is found for the same version
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
            uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.step_result_other_version.id, 'image': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_reference_2 = StepReference.objects.filter(testCase=self.tcs_other_version.testCase, version=Version.objects.get(pk=2), environment=TestEnvironment.objects.get(id=1), testStep__id=1).last()
            self.assertIsNotNone(uploaded_reference_2, "the uploaded snapshot should be recorded")
            self.assertNotEqual(uploaded_reference_2, uploaded_reference_1)
  
    def test_post_snapshot_no_picture(self):
        response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id})
        self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_post_snapshot_missing_step(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('uploadStepRef'), data={'image': fp})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
  