'''
Created on 8 mai 2017

@author: bhecquet
'''

import os

from django.test import Client
import django.test

from seleniumRobotServer.settings import MEDIA_ROOT
from snapshotServer.models import Snapshot, TestSession, TestStep, TestCase, \
    TestEnvironment, Version, TestCaseInSession, StepResult
from snapshotServer.tests import authenticate_test_client_for_web_view
import datetime
import pytz


class TestViews(django.test.TestCase):
    
    fixtures = ['snapshotServer.yaml']
    dataDir = 'snapshotServer/tests/data/'
    mediaDir = MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        self.client = Client()
        authenticate_test_client_for_web_view(self.client)
        
        # prepare data
        self.testCase = TestCase.objects.get(id=1)
        self.initialRefSnapshot = Snapshot.objects.get(id=1)
        self.step1 = TestStep.objects.get(id=1)
        
        self.session1 = TestSession(sessionId="1237", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session1.save()
        self.tcs1 = TestCaseInSession(testCase=self.testCase, session=self.session1)
        self.tcs1.save()
        self.sr1 = StepResult(step=self.step1, testCase=self.tcs1, result=True)
        self.sr1.save()
        
        self.session_same_env = TestSession(sessionId="1238", date=datetime.datetime(2017, 5, 7, tzinfo=pytz.UTC), browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1), ttl=datetime.timedelta(0))
        self.session_same_env.save()
        self.tcs_same_env = TestCaseInSession(testCase=self.testCase, session=self.session_same_env)
        self.tcs_same_env.save()
        self.step_result_same_env = StepResult(step=self.step1, testCase=self.tcs_same_env, result=True)
        self.step_result_same_env.save()
        
        # session with other env (AUT instead of DEV), other characteristics remain the same as session1
        self.session_other_env = TestSession.objects.get(pk=10)
        self.tcs_other_env = TestCaseInSession.objects.get(pk=9)
        self.step_result_other_env = StepResult.objects.get(pk=11)
        
        # session with other browser (chrome instead of firefox), other characteristics remain the same as session1
        self.session_other_browser = TestSession.objects.get(pk=11)
        self.tcs_other_browser = TestCaseInSession.objects.get(pk=10)
        self.step_result_other_browser = StepResult.objects.get(pk=12)
        
    
    def tearDown(self):
        """
        Remove generated files
        """
        
        for f in os.listdir(self.mediaDir):
            if f.startswith('img_'):
                os.remove(self.mediaDir + os.sep + f)

    

        
        