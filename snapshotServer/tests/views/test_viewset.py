'''
Created on 16 mai 2017

@author: bhecquet
'''

import json
from variableServer.models import Application
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from snapshotServer.models import TestSession
from django.contrib.auth.models import Permission
from commonsServer.tests.test_api import TestApi

class TestViewset(TestApi):
    fixtures = ['snapshotServer.yaml']
 
    def setUp(self):
        
        Application.objects.get(pk=1).save()
        
        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_testsession = ContentType.objects.get_for_model(TestSession)
    
    
    def test_testsession_create(self):
        """
        Test it's possible to create session with model permissions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testsession', content_type=self.content_type_testsession)))
        response = self.client.post('/snapshot/api/session/', data={'sessionId': '12345', 'name': 'bla', 'version': 1, 'browser': 'BROWSER:chrome', 'environment': 'DEV', 'date': '2017-05-05T11:16:09.184106+01:00'})
        self.assertEqual(201, response.status_code)
        self.assertEqual(1, len(TestSession.objects.filter(name='bla')))
        
    def test_testsession_other_verbs_forbidden(self):
        """
        Check we cann only post sessions
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testsession', content_type=self.content_type_testsession) 
                                                                                      | Q(codename='change_testsession', content_type=self.content_type_testsession)
                                                                                      | Q(codename='delete_testsession', content_type=self.content_type_testsession)))
        response = self.client.get('/snapshot/api/session/1')
        self.assertEqual(405, response.status_code)
        response = self.client.patch('/snapshot/api/session/1')
        self.assertEqual(405, response.status_code)
        response = self.client.put('/snapshot/api/session/1')
        self.assertEqual(405, response.status_code)
        response = self.client.delete('/snapshot/api/session/1')
        self.assertEqual(405, response.status_code)
    
    def test_testsession_create_no_api_security(self):
        """
        Check it's possible to add a testsession when API security is disabled and user has no permissions
        """
        with self.settings(SECURITY_API_ENABLED=''):
            self._create_and_authenticate_user_with_permissions(Permission.objects.none())
            response = self.client.post('/snapshot/api/session/', data={'sessionId': '12345', 'name': 'bla', 'version': 1, 'browser': 'BROWSER:chrome', 'environment': 'DEV', 'date': '2017-05-05T11:16:09.184106+01:00'})
            self.assertEqual(201, response.status_code)
            self.assertEqual(1, len(TestSession.objects.filter(name='bla')))
        
    def test_testsession_create_forbidden(self):
        """
        Check it's NOT possible to add a testsession without 'add_testsession' permission
        """
        self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='view_testsession', content_type=self.content_type_testsession)))
        response = self.client.post('/snapshot/api/session/', data={'sessionId': '12345', 'name': 'bla', 'version': 1, 'browser': 'BROWSER:chrome', 'environment': 'DEV', 'date': '2017-05-05T11:16:09.184106+01:00'})
        self.assertEqual(403, response.status_code)
    
    def test_create_testcase_with_application_restriction_and_add_permission(self):
        """
        User
        - has add_testsession permission
        - has NOT app1 permission
        
        User can add test session
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testsession', content_type=self.content_type_testsession)))
            response = self.client.post('/snapshot/api/session/', data={'sessionId': '12345', 'name': 'bla', 'version': 1, 'browser': 'BROWSER:chrome', 'environment': 'DEV', 'date': '2017-05-05T11:16:09.184106+01:00'})
            self.assertEqual(201, response.status_code)
    
    def test_create_testcase_with_application_restriction_and_app1_permission(self):
        """
        User
        - has NOT add_testcase permission
        - has app1 permission
        
        User can add test case on app1
        """
        with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
            self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_m')))
            response = self.client.post('/snapshot/api/session/', data={'sessionId': '12345', 'name': 'bla', 'version': 1, 'browser': 'BROWSER:chrome', 'environment': 'DEV', 'date': '2017-05-05T11:16:09.184106+01:00'})
            self.assertEqual(201, response.status_code)
    
    # def test_create_testcase_with_application_restriction_and_app1_permission2(self):
    #     """
    #     User
    #     - has NOT add_testcase permission
    #     - has app1 permission
    #
    #     User can NOT add test case on an other application than app1
    #     """
    #     with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
    #         self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='can_view_application_app1')))
    #         response = self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 2})
    #         self.assertEqual(403, response.status_code)
    #
    # def test_create_testcase_with_application_restriction_and_change_permission(self):
    #     """
    #     User
    #     - has change_testcase permission
    #     - has NOT app1 permission
    #
    #     User can NOT add test case
    #     """
    #     with self.settings(RESTRICT_ACCESS_TO_APPLICATION_IN_ADMIN=True):
    #         self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='change_testcase')))
    #         response = self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 2})
    #         self.assertEqual(403, response.status_code)
    #
    #
    # def test_create_testcase_already_created(self):
    #     """
    #     Check it's possible to add a testcase with 'add_testcase' permission
    #     """
    #     self._create_and_authenticate_user_with_permissions(Permission.objects.filter(Q(codename='add_testcase', content_type=self.content_type_testcase)))
    #     self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 1})
    #     self.assertEqual(1, len(TestCase.objects.filter(name='myTestCase')))
    #
    #     # if we try to create the same test case an other time, the same is returned
    #     self.client.post(reverse('testcase'), data={'name': 'myTestCase', 'application': 1})
    #     self.assertEqual(1, len(TestCase.objects.filter(name='myTestCase')))
        
# -----------------------------------------------------------------
    def test_creation_when_exist_without_test_steps(self):
        """
        New testCaseInSession should be created as it does not match any existing testCaseInSession (no test steps)
        """
        response = self.client.post('/snapshot/api/testcaseinsession/', data={'session': 8, 'testCase': 4})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in json.loads(response.content))
        self.assertNotEqual(json.loads(response.content)['id'], 1)
    
    def test_creation_when_exist_with_test_steps(self):
        """
        New testCaseInSession should be created as it does not match any existing testCaseInSession (with test steps)
        """
        response = self.client.post('/snapshot/api/testcaseinsession/', data={'session': 8, 'testCase': 4, 'testSteps': [2, 3, 4]})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in json.loads(response.content))
        self.assertEquals(json.loads(response.content)['testSteps'], [2, 3, 4]) # steps has been added
        self.assertNotEqual(json.loads(response.content)['id'], 1)
        
    def test_no_creation_when_exist_with_many_to_many_fields(self):
        """
        New testCaseInSession should not be created as it does match an existing testCaseInSession
        """
        response = self.client.post('/snapshot/api/testcaseinsession/', data={'session': 7, 'testCase': 4, 'testSteps': [2, 3, 4]})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in json.loads(response.content))
        self.assertEqual(json.loads(response.content)['id'], 6)
        
    def test_no_creation_when_exist_with_many_to_many_fields_empty(self):
        """
        New session should not be created as there are no test steps
        """
        response = self.client.post('/snapshot/api/testcaseinsession/', data={'session': 8, 'testCase': 2, 'testSteps': []})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in json.loads(response.content))
        self.assertEquals(json.loads(response.content)['testSteps'], []) # steps has been removed
        self.assertEqual(json.loads(response.content)['id'], 8)
