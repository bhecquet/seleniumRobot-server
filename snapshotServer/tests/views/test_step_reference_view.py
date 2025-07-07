'''
Created on 15 mai 2017

@author: behe
'''

import datetime
import io
import os
import time
import pytz

from django.conf import settings
from django.urls.base import reverse
from django.db.models import Q
from django.test.utils import override_settings
from dramatiq.broker import get_broker
from dramatiq.worker import Worker

from pathlib import Path

from snapshotServer.models import TestCase, TestStep, TestSession, \
    TestEnvironment, Version, TestCaseInSession, \
    StepResult, StepReference
from snapshotServer.tests import authenticate_test_client_for_api
from snapshotServer.views.step_reference_view import StepReferenceView
from commonsServer.tests.test_api import TestApi

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

import variableServer
from variableServer.models import Application

@override_settings(FIELD_DETECTOR_ENABLED='True')
class TestStepReferenceView(TestApi):
    fixtures = ['snapshotServer.yaml']
    
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    reference_dir = os.path.join(media_dir, 'references', 'myapp', 'test upload')
    
    def _pre_setup(self):
        super()._pre_setup()

        self.broker = get_broker()
        self.broker.flush_all()

        self.worker = Worker(self.broker, worker_timeout=100)
        self.worker.start()

    def _post_teardown(self):
        self.worker.stop()

        super()._post_teardown()

    
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
        self.sr_ko = StepResult(step=self.step1, testCase=self.tcs1, result=False)
        self.sr_ko.save()
        
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
        
        # set OVERWRITE_REFERENCE_AFTER_SECONDS so that reference is always updated in tests
        StepReferenceView.OVERWRITE_REFERENCE_AFTER_SECONDS = 0
        
        self.content_type_application = ContentType.objects.get_for_model(variableServer.models.Application, for_concrete_model=False)
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()
          
    def tearDown(self):
        """
        Remove generated files
        """
        
        super().tearDown()
        
        for f in os.listdir(self.reference_dir):
            if f.startswith('engie') or f.startswith('replyDetection'):
                os.remove(self.reference_dir + os.sep + f)
                
        for f in Path(settings.MEDIA_ROOT, 'detect').iterdir():
            if f.is_file() and (f.name.startswith('engie') or f.name.startswith('replyDetection')):
                f.unlink(missing_ok=True)
                
        StepReferenceView.OVERWRITE_REFERENCE_AFTER_SECONDS = 60 * 60 * 48
        
    def test_get_snapshot_no_security_not_authenticated(self):
        """
        Check that with security disabled, we  access view without authentication
        """
        with self.settings(SECURITY_API_ENABLED=''):
            
            # upload image to be tested
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
                time.sleep(0.5) # wait field computing
                self.assertEqual(201, response.status_code)
                
            response = self.client.get(reverse('stepReference', kwargs={'step_result_id': self.sr1.id}))
                
            self.assertEqual(200, response.status_code)
        
    def test_get_snapshot_security_not_authenticated(self):
        """
        Check that with security enabled, we cannot access view without authentication
        """
        # upload image to be tested
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
            time.sleep(0.5) # wait field computing
            self.assertEqual(403, response.status_code)
            
        response = self.client.get(reverse('stepReference', kwargs={'step_result_id': self.sr1.id}))
        
        # check we are redirected to login
        self.assertEqual(403, response.status_code)
        
    def test_get_snapshot_security_authenticated_no_permission(self):
        """
        Check that with 
        - security enabled
        - no permission on requested application
        We cannot post/get step reference
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2', content_type=self.content_type_application)))
            
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
                time.sleep(0.5) # wait field computing
                self.assertEqual(403, response.status_code)
                
            response = self.client.get(reverse('stepReference', kwargs={'step_result_id': self.sr1.id}))
            
            # check we have no permission to view the report
            self.assertEqual(403, response.status_code)
        
    def test_get_snapshot_security_authenticated_with_permission(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We can post/get step reference
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
                time.sleep(0.5) # wait field computing
                self.assertEqual(201, response.status_code)
                
            response = self.client.get(reverse('stepReference', kwargs={'step_result_id': self.sr1.id}))
            
            # check we have no permission to view the report
            self.assertEqual(200, response.status_code)
            
            
    def test_get_snapshot_security_authenticated_with_permission_object_not_found(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We get 404 error
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            response = self.client.get(reverse('stepReference', kwargs={'step_result_id': 1234}))
            
            # check we have no permission to view the report
            self.assertEqual(404, response.status_code)

    def test_get_snapshot(self):
        """
        Check we can get reference snapshot if it exists
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            # upload image to be tested
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
                time.sleep(0.5) # wait field computing
                
            response = self.client.get(reverse('stepReference', kwargs={'step_result_id': self.sr1.id}))
            self.assertEqual(response.status_code, 200, 'status code should be 200')
            self.assertEqual(response.headers['Content-Length'], '14378')
            io.BytesIO(response.content).getvalue()
    
    def test_post_snapshot_no_ref(self):
        """
        Check a reference step is created when none is found
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
                self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
                time.sleep(1) # wait field computing
                
                uploaded_reference = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1, version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1)).last()
                self.assertIsNotNone(uploaded_reference, "the uploaded snapshot should be recorded")
                
                # check computing has been done
                self.assertIsNotNone(uploaded_reference.field_detection_data)
                self.assertIsNotNone(uploaded_reference.field_detection_date)
                self.assertEqual(uploaded_reference.field_detection_version, 'afcc45')
                
                self.assertTrue(os.path.isfile(os.path.join(self.reference_dir, 'replyDetection.json.png')))

    def test_post_snapshot_clean_old_reference(self):
        """
        Check old reference information are deleted when reference is updated
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            with open('snapshotServer/tests/data/replyDetection.json.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
                self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
                time.sleep(1) # wait field computing
                
                uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1, version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1)).last()
                uploaded_file1 = Path(uploaded_reference_1.image.path)
                self.assertIsNotNone(uploaded_reference_1, "the uploaded snapshot should be recorded")
    
                self.assertTrue(os.path.isfile(os.path.join(self.reference_dir, 'replyDetection.json.png')))
            
            with open('snapshotServer/tests/data/replyDetection2.json.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.step_result_same_env.id, 'image': fp})
                self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
                time.sleep(0.5) # wait field computing
                
                uploaded_reference_2 = StepReference.objects.filter(testCase=self.tcs_same_env.testCase, testStep__id=1, version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1)).last()
                self.assertIsNotNone(uploaded_reference_2, "the uploaded snapshot should be recorded")
                self.assertEqual(uploaded_reference_2, uploaded_reference_1)
                uploaded_file2 = Path(uploaded_reference_2.image.path)
    
                # old detected files are removed, only files from the second detection are kept
                self.assertFalse(uploaded_file1.exists())
                self.assertFalse(Path(settings.MEDIA_ROOT, 'detect', uploaded_file1.name).exists())
                self.assertFalse(Path(settings.MEDIA_ROOT, 'detect', uploaded_file1.with_suffix('.json').name).exists())
                self.assertTrue(uploaded_file2.exists())
                self.assertTrue(Path(settings.MEDIA_ROOT, 'detect', uploaded_file2.name).exists())
                self.assertTrue(Path(settings.MEDIA_ROOT, 'detect', uploaded_file2.with_suffix('.json').name).exists())
    
    def test_post_snapshot_no_ref_result_ko(self):
        """
        reference should not be recorded if step result is KO
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr_ko.id, 'image': fp})
                self.assertEqual(response.status_code, 200, 'status code should be 201: ' + str(response.content))
                time.sleep(0.5) # wait field computing
                
                uploaded_reference = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1, version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1)).last()
                self.assertIsNone(uploaded_reference, "the uploaded snapshot should not be recorded")
    
                self.assertFalse(os.path.isfile(os.path.join(self.reference_dir, 'engie.png')))
        
            
    def test_post_snapshot_existing_ref(self):
        """
        Check we find the reference step when it exists in the same version / same name
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
                time.sleep(0.5) # wait field computing
                uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
                uploaded_file1 = uploaded_reference_1.image.path
                
            with open('snapshotServer/tests/data/Ibis_Mulhouse.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.step_result_same_env.id, 'image': fp})
                self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
                time.sleep(0.5) # wait field computing
                
                uploaded_reference_2 = StepReference.objects.filter(testCase=self.tcs_same_env.testCase, testStep__id=1, version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1)).last()
                self.assertIsNotNone(uploaded_reference_2, "the uploaded snapshot should be recorded")
                self.assertEqual(uploaded_reference_2, uploaded_reference_1)
                uploaded_file2 = uploaded_reference_2.image.path
                
                # reference has been updated
                self.assertTrue(uploaded_reference_2.date > uploaded_reference_1.date)
                
                # check the previous file has been deleted, so that we do not store old references indefinitely
                self.assertFalse(os.path.isfile(uploaded_file1))
                self.assertTrue(os.path.isfile(uploaded_file2))
            
    def test_post_snapshot_existing_ref_do_not_overwrite(self):
        """
        Check we find the reference step when it exists in the same version / same name
        Check we do not overwrite it as current reference is so young
        """
        
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
        
            # prevent overwriting of step reference
            StepReferenceView.OVERWRITE_REFERENCE_AFTER_SECONDS = 100
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
                time.sleep(0.5) # wait field computing
                uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
                uploaded_file1 = uploaded_reference_1.image.path
                
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.step_result_same_env.id, 'image': fp})
                self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
                time.sleep(0.5) # wait field computing
                
                uploaded_reference_2 = StepReference.objects.filter(testCase=self.tcs_same_env.testCase, testStep__id=1, version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1)).last()
                self.assertIsNotNone(uploaded_reference_2, "the uploaded snapshot should be recorded")
                self.assertEqual(uploaded_reference_2, uploaded_reference_1)
                
                # reference has not been updated
                self.assertEqual(uploaded_reference_2.date, uploaded_reference_1.date)
                
                # check the previous file has NOT been deleted, no update done
                self.assertTrue(os.path.isfile(uploaded_file1))
            
    def test_post_snapshot_existing_ref_other_env(self):
        """
        Check a reference step is created when none is found for the same environment
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
                uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
                time.sleep(0.5) # wait field computing
                
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.step_result_other_env.id, 'image': fp})
                self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
                time.sleep(0.5) # wait field computing
                
                uploaded_reference_2 = StepReference.objects.filter(testCase=self.tcs_other_env.testCase, version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=2), testStep__id=1).last()
                self.assertIsNotNone(uploaded_reference_2, "the uploaded snapshot should be recorded")
                self.assertNotEqual(uploaded_reference_2, uploaded_reference_1)
            
    def test_post_snapshot_existing_ref_other_version(self):
        """
        Check a reference step is created when none is found for the same version
        """
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id, 'image': fp})
                uploaded_reference_1 = StepReference.objects.filter(testCase=self.tcs1.testCase, testStep__id=1).last()
                time.sleep(0.5) # wait field computing
                
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.step_result_other_version.id, 'image': fp})
                self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
                time.sleep(0.5) # wait field computing
                
                uploaded_reference_2 = StepReference.objects.filter(testCase=self.tcs_other_version.testCase, version=Version.objects.get(pk=2), environment=TestEnvironment.objects.get(id=1), testStep__id=1).last()
                self.assertIsNotNone(uploaded_reference_2, "the uploaded snapshot should be recorded")
                self.assertNotEqual(uploaded_reference_2, uploaded_reference_1)
  
    def test_post_snapshot_no_picture(self):
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            response = self.client.post(reverse('uploadStepRef'), data={'stepResult': self.sr1.id})
            self.assertEqual(response.status_code, 400, 'status code should be 500')
        
    def test_post_snapshot_missing_step(self):
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
                response = self.client.post(reverse('uploadStepRef'), data={'image': fp})
                self.assertEqual(response.status_code, 400, 'status code should be 500')
  