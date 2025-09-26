'''
Created on 26 juil. 2017

@author: worm
'''

import pytz
import os
import datetime

from django.urls.base import reverse
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import Permission

from commonsServer.tests.test_api import TestApi
from snapshotServer.controllers.diff_computer import DiffComputer
from snapshotServer.models import TestSession, TestStep, Snapshot,\
    TestCaseInSession, StepResult, Version, TestEnvironment, TestCase
from django.contrib.contenttypes.models import ContentType

from variableServer.models import Application


class TestRecomputeDiffView(TestApi):
    
    fixtures = ['snapshotServer.yaml']
    dataDir = 'snapshotServer/tests/data/'
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()
        
        # prepare data
        self.testCase = TestCase.objects.get(id=1)
        self.initialRefSnapshot = Snapshot.objects.get(id=1)
        self.step1 = TestStep.objects.get(id=1)
        
        self.session1 = TestSession(sessionId="1237", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session1.save()
        self.tcs1 = TestCaseInSession(testCase=self.testCase, session=self.session1)
        self.tcs1.save()
        self.sr1 = StepResult(step=self.step1, testCase=self.tcs1, result=True)
        self.sr1.save()
        
        self.session_same_env = TestSession(sessionId="1238", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session_same_env.save()
        self.tcs_same_env = TestCaseInSession(testCase=self.testCase, session=self.session_same_env)
        self.tcs_same_env.save()
        self.step_result_same_env = StepResult(step=self.step1, testCase=self.tcs_same_env, result=True)
        self.step_result_same_env.save()
        
        # session with other env (AUT instead of DEV), other characteristics remain the same as session1
        self.session_other_env = TestSession.objects.get(pk=10)
        self.tcs_other_env = TestCaseInSession.objects.get(pk=9)
        self.step_result_other_env = StepResult.objects.get(pk=11)
        
        # session with other browser (chrome instead of firefox), other characteristics remain the same as session1
        self.session_other_browser = TestSession.objects.get(pk=11)
        self.tcs_other_browser = TestCaseInSession.objects.get(pk=10)
        self.step_result_other_browser = StepResult.objects.get(pk=12)
        
        self.content_type_application = ContentType.objects.get_for_model(Application, for_concrete_model=False)
        
    
    def tearDown(self):
        """
        Remove generated files*
        """
        
        super().tearDown()
        for f in os.listdir(self.media_dir):
            if f.startswith('img_'):
                os.remove(self.media_dir + os.sep + f)

        DiffComputer.stopThread()

    def test_recompute_diff_no_security_not_authenticated(self):
        """
        Check that with security disabled, we  access view without authentication
        """
        with self.settings(SECURITY_WEB_ENABLED=''):
            
            response = self.client.post(reverse('recompute', args=[2]))
            self.assertEqual(response.status_code, 200, "Reference exists for the snapshot, do computing")
        
    def test_recompute_diff_security_not_authenticated(self):
        """
        Check that with security enabled, we cannot access view without authentication
        """
        response = self.client.post(reverse('recompute', args=[2]))
        self.assertEqual(response.status_code, 401, "Reference exists for the snapshot, do computing")
        
    def test_recompute_diff_security_authenticated_no_permission(self):
        """
        Check that with 
        - security enabled
        - no permission on requested application
        We cannot post recompute
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2', content_type=self.content_type_application)))
            
            response = self.client.post(reverse('recompute', args=[2]))
            self.assertEqual(response.status_code, 403, "Reference exists for the snapshot, do computing")
        
    def test_recompute_diff_security_authenticated_with_permission(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We can post recompute
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)))
            
            response = self.client.post(reverse('recompute', args=[2]))
            self.assertEqual(response.status_code, 200, "Reference exists for the snapshot, do computing")
            
            
    def test_recompute_diff_security_authenticated_with_permission_object_not_found(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We get 404 error
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)))
            
            response = self.client.post(reverse('recompute', args=[222]))
            self.assertEqual(response.status_code, 403)
   
    def test_recompute_diff_snapshot_exist_no_ref(self):
        """
        Send recompute request whereas no ref exists. Nothing should be done
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)))
              
            response = self.client.post(reverse('recompute', args=[1]))
            self.assertEqual(response.status_code, 304, "No ref for this snapshot, 304 should be returned")
          
    def test_recompute_diff_snapshot_exist_with_ref(self):
        """
        Reference exists for the snapshot, do computing
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)))
            
            response = self.client.post(reverse('recompute', args=[2]))
            self.assertEqual(response.status_code, 200, "Reference exists for the snapshot, do computing")
          