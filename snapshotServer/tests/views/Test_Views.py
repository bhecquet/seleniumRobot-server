'''
Created on 8 mai 2017

@author: bhecquet
'''

import json
import os
import pickle
import time

from django.core.files.images import ImageFile
from django.core.urlresolvers import reverse
from django.test import Client
import django.test

from seleniumRobotServer.settings import MEDIA_ROOT
from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.controllers.Tools import isTestMode
from snapshotServer.models import Snapshot, TestSession, TestStep, TestCase, \
    TestEnvironment, Version, TestCaseInSession, StepResult
from snapshotServer.controllers.PictureComparator import Pixel


class Test_Views(django.test.TestCase):
    
    fixtures = ['snapshotServer.yaml']
    dataDir = 'snapshotServer/tests/data/'
    mediaDir = MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        self.client = Client()
        
        # prepare data
        self.testCase = TestCase.objects.get(id=1)
        self.initialRefSnapshot = Snapshot.objects.get(id=1)
        
        self.session1 = TestSession(sessionId="1237", date="2017-05-07", browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1))
        self.session1.save()
        self.tcs1 = TestCaseInSession(testCase=self.testCase, session=self.session1)
        self.tcs1.save()
        self.session2 = TestSession(sessionId="1238", date="2017-05-07", browser="firefox", version=Version.objects.get(pk=1), environment=TestEnvironment.objects.get(id=1))
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
            if f.startswith('img_'):
                os.remove(self.mediaDir + os.sep + f)

    

        
        