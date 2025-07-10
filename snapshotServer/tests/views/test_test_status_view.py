'''
Created on 26 juil. 2017

@author: worm
'''

import json
import pickle

from django.urls.base import reverse
from django.db.models import Q
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from snapshotServer.tests.views.test_views import TestViews
from snapshotServer.models import Snapshot
from snapshotServer.controllers.picture_comparator import Pixel
from snapshotServer.tests import authenticate_test_client_for_web_view_with_permissions
from variableServer.models import Application
import variableServer


class TestTestStatusView(TestViews):
    
    def setUp(self):
        super().setUp()
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()
        
        self.content_type_application = ContentType.objects.get_for_model(variableServer.models.Application, for_concrete_model=False)        
        

    def test_session_status_no_security_not_authenticated(self):
        """
        Check that with security disabled, we  access view without authentication
        """
        with self.settings(SECURITY_API_ENABLED=''):
            response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 5}))
            self.assertEqual(200, response.status_code)
        
    def test_session_status_security_not_authenticated(self):
        """
        Check that with security enabled, we cannot access view without authentication
        """
        response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 5}))
        
        # check we are redirected to login
        self.assertEqual(401, response.status_code)
        
    def test_session_status_security_authenticated_no_permission(self):
        """
        Check that with 
        - security enabled
        - no permission on requested application
        We cannot view status => error page displayed
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp2', content_type=self.content_type_application)))
            response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 5}))
            
            # check we have no permission to view the report
            self.assertEqual(403, response.status_code)
           
        
    def test_session_status_security_authenticated_with_permission(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We can view status
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 5}))
            
            # check we have no permission to view the report
            self.assertEqual(200, response.status_code)
            
            
    def test_session_status_security_authenticated_with_permission_object_not_found(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We get 404 error
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 568}))
            
            # check we have no permission to get status as test_case_in_session is unkown
            self.assertEqual(403, response.status_code)
    
    def test_session_status_ok_on_reference(self):
        """
        Test the result of a test session status when looking for reference
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 5}))
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content.decode('UTF-8'))
            self.assertTrue(data['5'])
          
    def test_session_status_ok_on_non_reference(self):
        """
        Test the result of a test session status when snapshot are not reference
        """
        # no diff for snapshots
        s1 = Snapshot.objects.get(pk=8)
        s1.pixelsDiff = pickle.dumps([])
        s1.save()
        s2 = Snapshot.objects.get(pk=9)
        s2.pixelsDiff = pickle.dumps([])
        s2.save()
        s3 = Snapshot.objects.get(pk=10)
        s3.pixelsDiff = pickle.dumps([])
        s3.save()
        
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
          
            response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 6}))
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content.decode('UTF-8'))
            self.assertTrue(data['8'])
          
    def test_session_status_ko(self):
        """
        Test the result of a test session status when snapshot are not reference
        """
        # diff for last snapshots
        s1 = Snapshot.objects.get(pk=8)
        s1.pixelsDiff = pickle.dumps([])
        s1.save()
        s2 = Snapshot.objects.get(pk=9)
        s2.pixelsDiff = pickle.dumps([])
        s2.save()
        s3 = Snapshot.objects.get(pk=10)
        s3.pixelsDiff = pickle.dumps([Pixel(1,1)])
        s3.save()
          
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 6}))
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content.decode('UTF-8'))
            self.assertTrue(data['8'])
            self.assertTrue(data['9'])
            self.assertFalse(data['10'])
         
    def test_step_status(self):
        """
        Test the result of a test session status when looking for reference
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp', content_type=self.content_type_application)))
            
            response = self.client.get(reverse('testStepStatusView', kwargs={'testCaseId': 5, 'testStepId': 2}))
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content.decode('UTF-8'))
            self.assertTrue(data['5'])