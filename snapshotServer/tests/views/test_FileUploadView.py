'''
Created on 15 mai 2017

@author: behe
'''

import os

from django.contrib.auth.models import User
import django.test
from django.test.client import Client
from django.urls.base import reverse

from seleniumRobotServer.settings import MEDIA_ROOT
from snapshotServer.models import TestCase, TestStep, TestSession, \
    TestEnvironment, Version, Snapshot


class test_FileUploadView(django.test.TestCase):
    fixtures = ['snapshotServer.yaml']
    
    mediaDir = MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        # TODO: remove admin authentication
        self.client = Client()
        self.user = User.objects.create_superuser('admin', 'admin@django.com', 'admin')
        self.client.login(username='admin', password='admin')
        
        # test in a version
        self.testCase = TestCase(name='test upload', version=Version.objects.get(id=1))
        self.testCase.save()
        self.testCase.testSteps = [TestStep.objects.get(id=1)]
        
        self.session1 = TestSession(sessionId="8888", date="2017-05-07", browser="firefox", environment=TestEnvironment.objects.get(id=1))
        self.session1.save()
        self.session1.testCases = [self.testCase]
        self.session1.save()
        self.session2 = TestSession(sessionId="8889", date="2017-05-07", browser="firefox", environment=TestEnvironment.objects.get(id=1))
        self.session2.save()
        self.session2.testCases = [self.testCase]
        self.session2.save()
        
    def tearDown(self):
        """
        Remove generated files
        """
        
        for f in os.listdir(self.mediaDir):
            if f.startswith('engie'):
                os.remove(self.mediaDir + os.sep + f)
    
    def test_postSnapshotNoRef(self):
        """
        Check a reference is created when non is found
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'step': 1, 'testCase': self.testCase.id, 'sessionId': '8888', 'image': fp})
            self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
            
            uploadedSnapshot = Snapshot.objects.filter(session__sessionId='8888', testCase=self.testCase, step__id=1).last()
            self.assertIsNotNone(uploadedSnapshot, "the uploaded snapshot should be recorded")
            
    def test_postSnapshotExistingRef(self):
        """
        Check we find the reference snapshot when it exists in the same version
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'step': 1, 'testCase': self.testCase.id, 'sessionId': '8888', 'image': fp})
            uploadedSnapshot1 = Snapshot.objects.filter(session__sessionId='8888', testCase=self.testCase, step__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'step': 1, 'testCase': self.testCase.id, 'sessionId': '8889', 'image': fp})
            self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
            
            uploadedSnapshot2 = Snapshot.objects.filter(session__sessionId='8889', testCase=self.testCase, step__id=1).last()
            self.assertIsNotNone(uploadedSnapshot2, "the uploaded snapshot should be recorded")
            self.assertEqual(uploadedSnapshot2.refSnapshot, uploadedSnapshot1)
            
    def test_postSnapshotExistingRefInPreviousVersion(self):
        """
        Check that we search for a reference in a previous version if none is found in the current one
        """
        
        # same as self.testCase in a greater version
        testCase2 = TestCase(name='test upload', version=Version.objects.get(id=2))
        testCase2.save()
        testCase2.testSteps = [TestStep.objects.get(id=1)]
        
        session3 = TestSession(sessionId="8890", date="2017-05-07", browser="firefox", environment=TestEnvironment.objects.get(id=1))
        session3.save()
        session3.testCases = [testCase2]
        session3.save()
        
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'step': 1, 'testCase': self.testCase.id, 'sessionId': '8888', 'image': fp})
            uploadedSnapshot1 = Snapshot.objects.filter(session__sessionId='8888', testCase=self.testCase, step__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'step': 1, 'testCase': testCase2.id, 'sessionId': '8890', 'image': fp})
            self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
            
            uploadedSnapshot2 = Snapshot.objects.filter(session__sessionId='8890', testCase=testCase2, step__id=1).last()
            self.assertIsNotNone(uploadedSnapshot2, "the uploaded snapshot should be recorded")
            self.assertEqual(uploadedSnapshot2.refSnapshot, uploadedSnapshot1)
        
    def test_postSnapshotNoPicture(self):
        response = self.client.post(reverse('upload', args=['img']), data={'step': 1, 'testCase': self.testCase.id, 'sessionId': '8888'})
        self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_postSnapshotMissingStep(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'testCase': self.testCase.id, 'sessionId': '8888', 'image': fp})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_postSnapshotMissingTestCase(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'step': 1, 'sessionId': '8888', 'image': fp})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_postSnapshotMissingSession(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'step': 1, 'testCase': self.testCase.id, 'image': fp})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
