'''
Created on 16 mai 2017

@author: bhecquet
'''

import django.test
from django.test.client import Client
from django.contrib.auth.models import User

class test_viewset(django.test.TestCase):
    fixtures = ['snapshotServer.yaml']
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser('admin', 'admin@django.com', 'admin')
        self.client.login(username='admin', password='admin')
    
    def test_creationWhenNotExist(self):
        """
        Test creation of object when it does not exist
        ex: we try to get an application, if it does not exist, it's created
        """
        response = self.client.post('/snapshot/api/application/', data={'name': 'test'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertEqual(eval(response.content)['name'], 'test')
    
    def test_noCreationWhenExist(self):
        """
        Test creation of object when it does exist
        ex: we try to get an application, if it does not exist, it's created
        """
        response = self.client.post('/snapshot/api/application/', data={'name': 'infotel'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertEqual(eval(response.content)['name'], 'infotel')
        self.assertEqual(eval(response.content)['id'], 1)
    
    def test_creationWhenExistWithManyToManyFields(self):
        """
        New testCaseInSession should be created as it does not match any existing testCaseInSession (no test steps)
        """
        response = self.client.post('/snapshot/api/testcaseinsession/', data={'session': 8, 'testCase': 4})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertNotEqual(eval(response.content)['id'], 1)
        
    def test_noCreationWhenExistWithManyToManyFields(self):
        """
        New testCaseInSession should not be created as it does match an existing testCaseInSession
        """
        response = self.client.post('/snapshot/api/testcaseinsession/', data={'session': 6, 'testCase': 4, 'testSteps': [1, 2, 3]})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertEqual(eval(response.content)['id'], 5)
        
    def test_noCreationWhenExistWithManyToManyFieldsEmpty(self):
        """
        New session should not be created as there are not test cases
        """
        response = self.client.post('/snapshot/api/testcaseinsession/', data={'session': 8, 'testCase': 2, 'testSteps': []})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertEqual(eval(response.content)['id'], 8)
    