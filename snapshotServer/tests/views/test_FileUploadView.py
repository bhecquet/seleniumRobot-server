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
    StepResult

from django.conf import settings
import json

class TestFileUploadView(APITestCase):
    fixtures = ['snapshotServer.yaml']
    
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    
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
        
        super().tearDown()
        
        for f in os.listdir(self.media_dir):
            if f.startswith('engie'):
                os.remove(self.media_dir + os.sep + f)
    
    def test_post_snapshot_no_ref(self):
        """
        Check a reference is created when non is found
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            # check returned data: with no ref, no computing error should be raised, but snapshot is considered as computed
            data = json.loads(response.content.decode('UTF-8'), encoding='UTF-8')
            self.assertIsNotNone(data['id']) # ID has been provided
            self.assertTrue(data['computed'])
            self.assertEqual(data['computingError'], '')
            self.assertEqual(data['diffPixelPercentage'], 0.0)
            self.assertFalse(data['tooManyDiffs'])
            
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
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.step_result_same_env.id, 
                                                                               'image': fp, 
                                                                               'name': 'img', 
                                                                               'compare': 'true'})
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
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': sr3.id, 
                                                                               'image': fp, 
                                                                               'name': 'img', 
                                                                               'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot_2 = Snapshot.objects.filter(stepResult__testCase=tcs3, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot_2, "the uploaded snapshot should be recorded")
            self.assertEqual(uploaded_snapshot_2.refSnapshot, uploaded_snapshot_1)
            
        
    def test_post_snapshot_with_comparison_picture_parameter_exclude_zones(self):
        """
        Check that uploaded picture is stored when using the "post" method
        We provide exclude zones to check that they are used for comparison
        """
        
        with open('snapshotServer/tests/data/Ibis_Mulhouse.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'image': fp, 
                                                                               'stepResult': self.sr1.id, 
                                                                               'name': 'img', 
                                                                               'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            uploaded_snapshot1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/Ibis_Mulhouse_diff.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.step_result_same_env.id, 
                                                                                'image': fp, 
                                                                               'name': 'img', 
                                                                               'compare': 'true',
                                                                               'excludeZones': '[{"x": 554, "y": 256, "width": 1, "height": 1}]'})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            
            data = json.loads(response.content.decode('UTF-8'), encoding='UTF-8')
            self.assertIsNotNone(data['id'])           # ID provided, snapshot should be saved in database
            self.assertTrue(data['computed'])
            self.assertEqual(data['computingError'], '')
            self.assertTrue(data['diffPixelPercentage'] < 0.000097) # check computation has been done => 2 pixel difference due to exclude zone (3 pixel diff in original image)
            self.assertTrue(data['tooManyDiffs'])
            
            # check temp file has been deleted
            self.assertFalse(os.path.isfile(os.path.join(settings.MEDIA_ROOT, 'Ibis_Mulhouse_diff.png')))
            
            uploaded_snapshot2 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            self.assertEqual(uploaded_snapshot2, uploaded_snapshot1, "the second uploaded snapshot should not be recorded")
            
             
        
    def test_post_snapshot_no_store_picture_parameter(self):
        """
        Check that uploaded picture is not stored when using the "put" method
        """
        # check no snapshot correspond to this characteristics before the test
        self.assertIsNone(Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last())
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            
            response = self.client.put(reverse('upload', args=['img']), data={'image': fp,  
                                                                               'name': 'img', 
                                                                               'compare': 'true',
                                                                               'versionId': Version.objects.get(pk=1).id,
                                                                               'environmentId': TestEnvironment.objects.get(pk=1).id,
                                                                               'browser': 'firefox',
                                                                               'testCaseName': 'test1',
                                                                               'stepName': 'Step 1'})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            
            data = json.loads(response.content.decode('UTF-8'), encoding='UTF-8')
            self.assertIsNone(data['id'])       # no ID provided, snapshot should not be saved in database
            self.assertTrue(data['computed'])
            self.assertEqual(data['computingError'], '')
            self.assertEqual(data['diffPixelPercentage'], 0.0)
            self.assertFalse(data['tooManyDiffs'])
            
            uploaded_snapshot = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            self.assertIsNone(uploaded_snapshot, "the uploaded snapshot should not be recorded")
        
    def test_post_snapshot_with_comparison_no_store_picture_parameter(self):
        """
        Check that uploaded picture is not stored when using the "put" method
        We expect to get a comparison result
        """
        
        with open('snapshotServer/tests/data/Ibis_Mulhouse.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'image': fp, 
                                                                               'stepResult': self.sr1.id, 
                                                                               'name': 'img', 
                                                                               'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            uploaded_snapshot1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/Ibis_Mulhouse_diff.png', 'rb') as fp:
            response = self.client.put(reverse('upload', args=['img']), data={'image': fp, 
                                                                               'name': 'img', 
                                                                               'compare': 'true',
                                                                               'versionId': Version.objects.get(pk=1).id,
                                                                               'environmentId': TestEnvironment.objects.get(pk=1).id,
                                                                               'browser': 'firefox',
                                                                               'testCaseName': 'test upload',
                                                                               'stepName': 'Step 1'})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            
            data = json.loads(response.content.decode('UTF-8'), encoding='UTF-8')
            self.assertIsNone(data['id'])           # no ID provided, snapshot should not be saved in database
            self.assertTrue(data['computed'])
            self.assertEqual(data['computingError'], '')
            self.assertTrue(data['diffPixelPercentage'] > 0.000144) # check computation has been done
            self.assertTrue(data['tooManyDiffs'])
            
            # check temp file has been deleted
            self.assertFalse(os.path.isfile(os.path.join(settings.MEDIA_ROOT, 'Ibis_Mulhouse_diff.png')))
            
            uploaded_snapshot2 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            self.assertEqual(uploaded_snapshot2, uploaded_snapshot1, "the second uploaded snapshot should not be recorded")
           
        
    def test_post_snapshot_with_comparison_no_store_picture_parameter_exclude_zones(self):
        """
        Check that uploaded picture is not stored when using the "put" method
        We provide exclude zones to check that they are used for comparison
        """
        
        with open('snapshotServer/tests/data/Ibis_Mulhouse.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'image': fp, 
                                                                               'stepResult': self.sr1.id, 
                                                                               'name': 'img', 
                                                                               'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            uploaded_snapshot1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/Ibis_Mulhouse_diff.png', 'rb') as fp:
            response = self.client.put(reverse('upload', args=['img']), data={'image': fp, 
                                                                               'name': 'img', 
                                                                               'compare': 'true',
                                                                               'versionId': Version.objects.get(pk=1).id,
                                                                               'environmentId': TestEnvironment.objects.get(pk=1).id,
                                                                               'browser': 'firefox',
                                                                               'testCaseName': 'test upload',
                                                                               'stepName': 'Step 1',
                                                                               'excludeZones': '[{"x": 554, "y": 256, "width": 1, "height": 1}]'})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            
            data = json.loads(response.content.decode('UTF-8'), encoding='UTF-8')
            self.assertIsNone(data['id'])           # no ID provided, snapshot should not be saved in database
            self.assertTrue(data['computed'])
            self.assertEqual(data['computingError'], '')
            self.assertTrue(data['diffPixelPercentage'] < 0.000097) # check computation has been done => 2 pixel difference due to exclude zone (3 pixel diff in original image)
            self.assertTrue(data['tooManyDiffs'])
            
            # check temp file has been deleted
            self.assertFalse(os.path.isfile(os.path.join(settings.MEDIA_ROOT, 'Ibis_Mulhouse_diff.png')))
            
            uploaded_snapshot2 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            self.assertEqual(uploaded_snapshot2, uploaded_snapshot1, "the second uploaded snapshot should not be recorded")
            
             
        
    def test_post_snapshot_no_store_picture_parameter_missing_version(self):
        """
        Check that an error is raised when version is not provided
        """
        # check no snapshot correspond to this characteristics before the test
        self.assertIsNone(Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last())
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            
            response = self.client.put(reverse('upload', args=['img']), data={'image': fp, 
                                                                               'name': 'img', 
                                                                               'compare': 'true',
                                                                               'environmentId': TestEnvironment.objects.get(pk=1).id,
                                                                               'browser': 'firefox',
                                                                               'testCaseName': 'test1',
                                                                               'stepName': 'Step 1'})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
           
        
    def test_post_snapshot_no_store_picture_parameter_missing_environment(self):
        """
        Check that an error is raised when environment is not provided
        """
        # check no snapshot correspond to this characteristics before the test
        self.assertIsNone(Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last())
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            
            response = self.client.put(reverse('upload', args=['img']), data={'image': fp, 
                                                                               'name': 'img', 
                                                                               'compare': 'true',
                                                                               'versionId': Version.objects.get(pk=1).id,
                                                                               'browser': 'firefox',
                                                                               'testCaseName': 'test1',
                                                                               'stepName': 'Step 1'})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_post_snapshot_no_store_picture_parameter_missing_browser(self):
        """
        Check that an error is raised when browser is not provided
        """
        # check no snapshot correspond to this characteristics before the test
        self.assertIsNone(Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last())
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            
            response = self.client.put(reverse('upload', args=['img']), data={'image': fp, 
                                                                               'name': 'img', 
                                                                               'compare': 'true',
                                                                               'versionId': Version.objects.get(pk=1).id,
                                                                               'environmentId': TestEnvironment.objects.get(pk=1).id,
                                                                               'testCaseName': 'test1',
                                                                               'stepName': 'Step 1'})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_post_snapshot_no_store_picture_parameter_missing_test_name(self):
        """
        Check that an error is raised when test name is not provided
        """
        # check no snapshot correspond to this characteristics before the test
        self.assertIsNone(Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last())
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            
            response = self.client.put(reverse('upload', args=['img']), data={'image': fp, 
                                                                               'name': 'img', 
                                                                               'compare': 'true',
                                                                               'versionId': Version.objects.get(pk=1).id,
                                                                               'environmentId': TestEnvironment.objects.get(pk=1).id,
                                                                               'browser': 'firefox',
                                                                               'stepName': 'Step 1'})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_post_snapshot_no_store_picture_parameter_missing_step_name(self):
        """
        Check that an error is raised when step name is not provided
        """
        # check no snapshot correspond to this characteristics before the test
        self.assertIsNone(Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last())
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            
            response = self.client.put(reverse('upload', args=['img']), data={'image': fp, 
                                                                               'name': 'img', 
                                                                               'compare': 'true',
                                                                               'versionId': Version.objects.get(pk=1).id,
                                                                               'environmentId': TestEnvironment.objects.get(pk=1).id,
                                                                               'browser': 'firefox',
                                                                               'testCaseName': 'test1'})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_post_snapshot_no_store_picture_parameter_missing_image(self):
        """
        Check that an error is raised when imag is not provided
        """
        # check no snapshot correspond to this characteristics before the test
        self.assertIsNone(Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last())
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            
            response = self.client.put(reverse('upload', args=['img']), data={'name': 'img', 
                                                                               'compare': 'true',
                                                                               'versionId': Version.objects.get(pk=1).id,
                                                                               'environmentId': TestEnvironment.objects.get(pk=1).id,
                                                                               'browser': 'firefox',
                                                                               'testCaseName': 'test1',
                                                                               'stepName': 'Step 1'})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
           
        
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
