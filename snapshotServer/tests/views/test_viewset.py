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
        response = self.client.post('/api/application/', data={'name': 'test'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertEqual(eval(response.content)['name'], 'test')
    
    def test_noCreationWhenExist(self):
        """
        Test creation of object when it does exist
        ex: we try to get an application, if it does not exist, it's created
        """
        response = self.client.post('/api/application/', data={'name': 'infotel'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertEqual(eval(response.content)['name'], 'infotel')
        self.assertEqual(eval(response.content)['id'], 1)
    
    def test_creationWhenExistWithManyToManyFields(self):
        """
        New session should be created as it does not match any existing session (no test cases)
        """
        response = self.client.post('/api/session/', data={'sessionId': 1252, 'version': 1, 'date': '2017-05-06', 'browser': 'firefox', 'environment': 'DEV'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertNotEqual(eval(response.content)['id'], 1)
        
    def test_noCreationWhenExistWithManyToManyFields(self):
        """
        New session should be created as it does not match any existing session (no test cases)
        """
        response = self.client.post('/api/session/', data={'sessionId': 1252, 'version': 1, 'testCases': [1, 2], 'date': '2017-05-06', 'browser': 'firefox', 'environment': 'DEV'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertEqual(eval(response.content)['id'], 8)
        
    def test_noCreationWhenExistWithManyToManyFieldsEmpty(self):
        """
        New session should be created as it does not match any existing session (no test cases)
        """
        response = self.client.post('/api/session/', data={'sessionId': 1235, 'version': 1, 'testCases': [], 'date': '2017-05-05', 'browser': 'firefox', 'environment': 'DEV'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertEqual(eval(response.content)['id'], 2)
    