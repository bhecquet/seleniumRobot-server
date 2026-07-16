'''
Created on 26 juil. 2017

@author: worm
'''

import os

from django.urls.base import reverse
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import Permission

from commonsServer.tests.test_api import TestApi
from snapshotServer.controllers.diff_computer import DiffComputer
from django.contrib.contenttypes.models import ContentType

from variableServer.models import Application, TestEnvironment as TestEnvironmentV


class TestRecomputeDiffView(TestApi):
    
    fixtures = ['test_recompute_diff_view.yaml']
    dataDir = 'snapshotServer/tests/data/'
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        
        # be sure permission for application / environment is created
        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()
        TestEnvironmentV.objects.get(pk=1).save()
        TestEnvironmentV.objects.get(pk=2).save()
        
        self.content_type_application = ContentType.objects.get_for_model(Application, for_concrete_model=False)
        self.content_type_environment = ContentType.objects.get_for_model(TestEnvironmentV, for_concrete_model=False)

    
    def tearDown(self):
        """
        Remove generated files*
        """
        
        super().tearDown()
        for f in os.listdir(self.media_dir):
            if f.startswith('img_'):
                os.remove(self.media_dir + os.sep + f)

        DiffComputer.stopThread()

    def test_recompute_diff_security_not_authenticated(self):
        """
        Check that with security enabled, we cannot access view without authentication
        """
        response = self.client.post(reverse('recompute', args=[2]))
        self.assertEqual(response.status_code, 401, "Reference exists for the snapshot, do computing")
        
    def test_recompute_diff_security_authenticated_no_permission_on_application(self):
        """
        Check that with 
        - security enabled
        - no permission on requested application
        We cannot post recompute
        """

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_myapp2', content_type=self.content_type_application)))

        response = self.client.post(reverse('recompute', args=[2]))
        self.assertEqual(response.status_code, 403, "Reference exists for the snapshot, do computing")
        
    def test_recompute_diff_security_authenticated_with_permission_on_application(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We can post recompute
        """

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)))

        response = self.client.post(reverse('recompute', args=[2]))
        self.assertEqual(response.status_code, 200, "Reference exists for the snapshot, do computing")

    def test_recompute_diff_security_authenticated_with_permission_on_environment(self):
        """
        Check that with
        - security enabled
        - permission on requested environment
        We can post recompute
        """

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_results_environment_DEV', content_type=self.content_type_environment)))

        response = self.client.post(reverse('recompute', args=[2]))
        self.assertEqual(response.status_code, 200, "Reference exists for the snapshot, do computing")

    def test_recompute_diff_security_authenticated_with_permission_on_other_environment(self):
        """
        Check that with
        - security enabled
        - permission on other environment
        We cannot post recompute
        """

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_results_environment_PROD', content_type=self.content_type_environment)))

        response = self.client.post(reverse('recompute', args=[2]))
        self.assertEqual(response.status_code, 403, "Reference exists for the snapshot, do computing")

            
    def test_recompute_diff_security_authenticated_with_permission_object_not_found(self):
        """
        Check that with 
        - security enabled
        - permission on requested application
        We get 404 error
        """

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)))

        response = self.client.post(reverse('recompute', args=[222]))
        self.assertEqual(response.status_code, 403)
   
    def test_recompute_diff_snapshot_exist_no_ref(self):
        """
        Send recompute request whereas no ref exists. Nothing should be done
        """

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)))

        response = self.client.post(reverse('recompute', args=[1]))
        self.assertEqual(response.status_code, 304, "No ref for this snapshot, 304 should be returned")
          
    def test_recompute_diff_snapshot_exist_with_ref(self):
        """
        Reference exists for the snapshot, do computing
        """

        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_results_application_myapp', content_type=self.content_type_application)))

        response = self.client.post(reverse('recompute', args=[2]))
        self.assertEqual(response.status_code, 200, "Reference exists for the snapshot, do computing")
          