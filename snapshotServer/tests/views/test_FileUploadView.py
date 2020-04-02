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
import datetime
import pytz


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
        
        self.session1 = TestSession(sessionId="8888", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session1.save()
        self.tcs1 = TestCaseInSession(testCase=self.testCase, session=self.session1)
        self.tcs1.save()
        self.session2 = TestSession(sessionId="8889", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
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
    
    def test_post_snapshot_no_ref(self):
        """
        Check a reference is created when non is found
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot, "the uploaded snapshot should be recorded")
            
    def test_post_snapshot_existing_ref(self):
        """
        Check we find the reference snapshot when it exists in the same version / same name
        """
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            uploaded_snapshot_1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr2.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot_2 = Snapshot.objects.filter(stepResult__testCase=self.tcs2, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot_2, "the uploaded snapshot should be recorded")
            self.assertEqual(uploaded_snapshot_2.refSnapshot, uploaded_snapshot_1)
            
    def test_post_snapshot_existing_ref_in_previous_version(self):
        """
        Check that we search for a reference in a previous version if none is found in the current one
        """
        
        # same as self.testCase in a greater version
        session3 = TestSession(sessionId="8890", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=2), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        session3.save()
        tcs3 = TestCaseInSession(testCase=self.testCase, session=session3)
        tcs3.save()
        tcs3.testSteps.set([TestStep.objects.get(id=1)])
        tcs3.save()
        sr3 = StepResult(step=TestStep.objects.get(id=1), testCase=tcs3, result=True)
        sr3.save()
        
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            uploaded_snapshot_1 = Snapshot.objects.filter(stepResult__testCase=self.tcs1, stepResult__step__id=1).last()
            
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': sr3.id, 'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 201, 'status code should be 201: ' + str(response.content))
            
            uploaded_snapshot_2 = Snapshot.objects.filter(stepResult__testCase=tcs3, stepResult__step__id=1).last()
            self.assertIsNotNone(uploaded_snapshot_2, "the uploaded snapshot should be recorded")
            self.assertEqual(uploaded_snapshot_2.refSnapshot, uploaded_snapshot_1)
        
    def test_post_snapshot_no_picture(self):
        response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'name': 'img', 'compare': 'true'})
        self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_post_snapshot_missing_step(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'image': fp, 'name': 'img', 'compare': 'true'})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
        
    def test_post_snapshot_missing_name(self):
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post(reverse('upload', args=['img']), data={'stepResult': self.sr1.id, 'image': fp, 'compare': 'true'})
            self.assertEqual(response.status_code, 500, 'status code should be 500')
