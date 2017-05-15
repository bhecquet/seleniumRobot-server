'''
Created on 15 mai 2017

@author: behe
'''

import django.test
from django.test.client import Client
from django.urls.base import reverse
from django.contrib.auth.models import User
from snapshotServer.models import TestCase, TestStep, TestSession,\
    TestEnvironment, Version

class test_FileUploadView(django.test.TestCase):
    fixtures = ['snapshotServer.yaml']
    
    def setUp(self):
        # TODO: remove admin authentication
        self.client = Client()
        self.user = User.objects.create_superuser('admin', 'admin@django.com', 'admin')
        self.client.login(username='admin', password='admin')
        
        self.testCase = TestCase(name='test upload', version=Version.objects.get(id=1))
        self.testCase.save()
        self.testCase.testSteps = [TestStep.objects.get(id=1)]
        self.session1 = TestSession(sessionId="8888", date="2017-05-07", browser="firefox", environment=TestEnvironment.objects.get(id=1))
        self.session1.save()
        self.session1.testCases = [self.testCase]
        self.session1.save()
    
    def test_postSnapshotNoRef(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'step': 1, 'testCase': self.testCase.id, 'sessionId': '8888', 'image': fp})
            self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
        
    # - test où la référence est recherchée dans les versions précédentes
    # - référence existe dans notre version
    # - pas d'imagee
    # - manque certains paramètres