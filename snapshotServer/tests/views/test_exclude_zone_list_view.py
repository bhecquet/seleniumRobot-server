'''
Created on 26 juil. 2017

@author: worm
'''

from django.core.files.images import ImageFile
from django.urls.base import reverse
from django.test.client import Client
from django.contrib.auth.models import User, Permission
from django.db.models import Q

from snapshotServer.controllers.diff_computer import DiffComputer
from snapshotServer.models import Snapshot, ExcludeZone, Application
from snapshotServer.tests.views.test_views import TestViews
from snapshotServer.tests import authenticate_test_client_for_web_view_with_permissions



class TestExcludeZoneListView(TestViews):
    
    fixtures = ['exclude_zone_list.yaml']
    
    def setUp(self):
        self.client = Client()
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()
    
    def test_exclude_zones_no_security_not_authenticated(self):
        """
        Check that with security disabled, we  access view without authentication
        """
        with self.settings(SECURITY_WEB_ENABLED=''):
            response = self.client.get(reverse('excludeListView', kwargs={'ref_snapshot_id': 1, 'step_snapshot_id': 2}))
            self.assertEqual(200, response.status_code)
        
    def test_exclude_zones_security_not_authenticated(self):
        """
        Check that with security enabled, we cannot access view without authentication
        """
        response = self.client.get(reverse('excludeListView', kwargs={'ref_snapshot_id': 1, 'step_snapshot_id': 2}))
        
        # check we are redirected to login
        self.assertEqual(302, response.status_code)
        self.assertEqual("/accounts/login/?next=/snapshot/compare/excludeList/1/2/", response.url)
        
    def test_exclude_zones_security_authenticated_no_permission(self):
        """
        Check that with 
        - security enabled
        - no permission on requested application
        We cannot view result => error page displayed
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp2')))
            response = self.client.get(reverse('excludeListView', kwargs={'ref_snapshot_id': 1, 'step_snapshot_id': 2}))
            
            # check we have no permission to view the report
            self.assertEqual(403, response.status_code)
           
        
    def test_exclude_zones_security_authenticated_with_permission(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We can view result
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.get(reverse('excludeListView', kwargs={'ref_snapshot_id': 1, 'step_snapshot_id': 2}))
            
            # check we have no permission to view the report
            self.assertEqual(200, response.status_code)
            
    def test_exclude_zones_security_authenticated_with_permission_object_not_found(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We get 404 page
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.get(reverse('excludeListView', kwargs={'ref_snapshot_id': 4, 'step_snapshot_id': 3}))
            
            # check we have no permission to view the report
            self.assertEqual(404, response.status_code)

    def test_exclude_zones_get_from_reference_and_step_snapshot(self):
        """
        Check we get exclude zone for reference picture AND for the picture itself
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.get(reverse('excludeListView', kwargs={'ref_snapshot_id': 1, 'step_snapshot_id': 2}))
            
            # check we have no permission to view the report
            self.assertEqual(200, response.status_code)
            
            # exclusions from reference / step snapshot
            self.assertEqual(2, len(response.context['object_list'])) 
            self.assertEqual(0, response.context['object_list'][0][0].x)
            self.assertEqual('red', response.context['object_list'][0][1])
            self.assertEqual('1', response.context['object_list'][0][2])
            self.assertEqual(1000, response.context['object_list'][1][0].x) # position of exclude zone
            self.assertEqual('blue', response.context['object_list'][1][1]) # display color
            self.assertEqual('2', response.context['object_list'][1][2]) # id of the snapshot
            
    def test_exclude_zones_get_from_step_snapshot(self):
        """
        Check we get exclude zone for reference picture AND for the picture itself
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            authenticate_test_client_for_web_view_with_permissions(self.client, Permission.objects.filter(Q(codename='can_view_application_myapp')))
            response = self.client.get(reverse('excludeListView', kwargs={'ref_snapshot_id': 'None', 'step_snapshot_id': 2}))
            
            # check we have no permission to view the report
            self.assertEqual(200, response.status_code)
            
            # exclusions from reference / step snapshot
            self.assertEqual(1, len(response.context['object_list'])) 
            self.assertEqual(1000, response.context['object_list'][0][0].x) # position of exclude zone
            self.assertEqual('red', response.context['object_list'][0][1]) # display color
            self.assertEqual('2', response.context['object_list'][0][2]) # id of the snapshot