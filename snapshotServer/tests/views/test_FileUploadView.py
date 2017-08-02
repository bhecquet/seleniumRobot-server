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
    TestEnvironment, Version, Snapshot, TestCaseInSession, Application,\
    StepResult


class test_FileUploadView(django.test.TestCase):
    fixtures = ['snapshotServer.yaml']
    
    mediaDir = MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        # TODO: remove admin authentication
        self.client = Client()
        self.user = User.objects.create_superuser('admin', 'admin@django.com', 'admin')
        self.client.login(username='admin', password='admin')
        
        # test in a version
        self.testCase = TestCase(name='test upload', application=Application.objects.get(id=1))
        self.testCase.save()
        
        self.session1 = TestSession(sessionId="8888", date="2017-05-07", browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1))
        self.session1.save()
        self.tcs1 = TestCaseInSession(testCase=self.testCase, session=self.session1)
        self.tcs1.save()
        self.session2 = TestSession(sessionId="8889", date="2017-05-07", browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1))
        self.session2.save()
        self.tcs2 = TestCaseInSession(testCase=self.testCase, session=self.session2)
        self.tcs2.save()
        self.step1 = TestStep.objects.get(id=1)
        self.sr1 = StepResult(step=self.step1, testCase=self.tcs1, result=True)
        self.sr1.save()
        self.sr2 = StepResult(step=self.step1, testCase=self.tcs2, result=True)
        self.sr2.save()
        
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
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp})
            self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
            
            uploadedSnapshot = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            self.assertIsNotNone(uploadedSnapshot, "the uploaded snapshot should be recorded")
            
    def test_postSnapshotExistingRef(self):
        """
        Check we find the reference snapshot when it exists in the same version
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp})
            uploadedSnapshot1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr2.id, 'image': fp})
            self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
            
            uploadedSnapshot2 = Snapshot.objects.filter(stepResult__testCase=self.tcs2, stepResult__step__id=1).last()
            self.assertIsNotNone(uploadedSnapshot2, "the uploaded snapshot should be recorded")
            self.assertEqual(uploadedSnapshot2.refSnapshot, uploadedSnapshot1)
            
    def test_postSnapshotExistingRefInPreviousVersion(self):
        """
        Check that we search for a reference in a previous version if none is found in the current one
        """
        
        # same as self.testCase in a greater version
        session3 = TestSession(sessionId="8890", date="2017-05-07", browser="firefox", version=Version.objects.get(pk=2), environment=TestEnvironment.objects.get(id=1))
        session3.save()
        tcs3 = TestCaseInSession(testCase=self.testCase, session=session3)
        tcs3.save()
        tcs3.testSteps = [TestStep.objects.get(id=1)]
        tcs3.save()
        sr3 = StepResult(step=TestStep.objects.get(id=1), testCase=tcs3, result=True)
        sr3.save()
        
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp})
            uploadedSnapshot1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': sr3.id, 'image': fp})
            self.assertEqual(response.status_code, 204, 'status code should be 204: ' + str(response.content))
            
            uploadedSnapshot2 = Snapshot.objects.filter(stepResult__testCase=tcs3, stepResult__step__id=1).last()
            self.assertIsNotNone(uploadedSnapshot2, "the uploaded snapshot should be recorded")
            self.assertEqual(uploadedSnapshot2.refSnapshot, uploadedSnapshot1)
        
    def test_postSnapshotNoPicture(self):
        response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id})
        self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_postSnapshotMissingStep(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'image': fp})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
