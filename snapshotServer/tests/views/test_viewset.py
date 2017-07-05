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
        Test creation of object when it does not exist
        ex: we try to get an application, if it does not exist, it's created
        """
        response = self.client.post('/api/application/', data={'name': 'infotel'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue('id' in eval(response.content))
        self.assertEqual(eval(response.content)['name'], 'infotel')
        self.assertEqual(eval(response.content)['id'], 1)
        
    # TODO: test when parameter is an empty list because the current approach does not an 'equal' on list. Chaining filter may help