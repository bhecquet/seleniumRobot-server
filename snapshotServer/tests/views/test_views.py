'''
Created on 8 mai 2017

@author: bhecquet
'''

import os
import datetime
import pytz

from django.test import Client
from django.conf import settings

from snapshotServer.models import Snapshot, TestSession, TestStep, TestCase, \
    TestEnvironment, Version, TestCaseInSession, StepResult, Application
from snapshotServer.tests import SnapshotTestCase



class TestViews(SnapshotTestCase):
    
    fixtures = ['snapshotServer.yaml']
    dataDir = 'snapshotServer/tests/data/'
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        self.client = Client()
        
        # be sure permission for application is created
        Application.objects.get(pk=1).save()
        Application.objects.get(pk=2).save()
        
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
        
        super().tearDown()
        for f in os.listdir(self.media_dir):
            if f.startswith('img_'):
                os.remove(self.media_dir + os.sep + f)

    

        
        