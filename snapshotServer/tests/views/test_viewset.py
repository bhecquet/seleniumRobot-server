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
        Application.objects.get(pk=2).save()
        
        # permissions will be allowed on variableServer models, not commonsServer models
        self.content_type_testsession = ContentType.objects.get_for_model(TestSession)
    

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
