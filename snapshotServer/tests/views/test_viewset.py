'''
Created on 16 mai 2017

@author: bhecquet
'''

import django.test
from django.test.client import Client
from django.contrib.auth.models import User
import json
from rest_framework.test import APITestCase
from snapshotServer.tests import authenticate_test_client_for_api

class TestViewset(APITestCase):
    fixtures = ['snapshotServer.yaml']
    
    def setUp(self):
        authenticate_test_client_for_api(self.client)
    
    
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
