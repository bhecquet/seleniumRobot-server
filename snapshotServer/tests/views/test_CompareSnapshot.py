'''
Created on 8 mai 2017

@author: bhecquet
'''

import time

from django.core.files.images import ImageFile
from django.core.urlresolvers import reverse
from django.test import Client
import django.test

from snapshotServer.controllers.Tools import isTestMode
from snapshotServer.models import Snapshot, TestSession, TestStep, TestCase, \
    TestEnvironment
import os
from seleniumRobotServer.settings import MEDIA_ROOT
from snapshotServer.controllers.DiffComputer import DiffComputer


class test_CompareSnapshot(django.test.TestCase):
    
    fixtures = ['snapshotServer.yaml']
    dataDir = 'snapshotServer/tests/data/'
    mediaDir = MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        self.client = Client()
        
        # prepare data
        self.testCase = TestCase.objects.get(id=1)
        self.initialRefSnapshot = Snapshot.objects.get(id=1)
        
        self.session1 = TestSession(sessionId="1237", date="2017-05-07", browser="firefox", environment=TestEnvironment.objects.get(id=1))
        self.session1.save()
        self.session1.testCases = [self.testCase]
        self.session1.save()
        self.session2 = TestSession(sessionId="1238", date="2017-05-07", browser="firefox", environment=TestEnvironment.objects.get(id=1))
        self.session2.save()
        self.session2.testCases = [self.testCase]
        self.session2.save()
    
    def tearDown(self):
        """
        Remove generated files
        """
        
        for f in os.listdir(self.mediaDir):
            if f.startswith('img_'):
                os.remove(self.mediaDir + os.sep + f)


    def test_TestList_testExists(self):
        """
        Simple test to show that we get all test cases from session
        """
        response = self.client.get(reverse('testlistView', args=[1]))
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].name, "test1")

    def test_TestList_sessionIdAdded(self):
        """
        Check that sessionId is available in context
        """
        response = self.client.get(reverse('testlistView', args=[1]))
        self.assertEqual(len(response.context['sessionId']), 1)

    def test_TestList_noTest(self):
        """
        Test no error raised when no test exist in session
        """
        response = self.client.get(reverse('testlistView', args=[2]))
        self.assertEqual(len(response.context['object_list']), 0)
        
    def test_StepList_stepExists(self):
        """
        Test that steps are found for our test case
        """
        response = self.client.get(reverse('steplistView', args=[1, 1]))
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0].name, "Step 1")

    def test_StepList_noStepExists(self):
        """
        Test that no steps are found for our test case
        """
        response = self.client.get(reverse('steplistView', args=[1, 20]))
        self.assertEqual(len(response.context['object_list']), 0)
        
    def test_StepList_contextComplete(self):
        """
        Test that extra information are added to the context
        """
        response = self.client.get(reverse('steplistView', args=[1, 1]))
        self.assertEqual(response.context['sessionId'], '1')
        self.assertEqual(response.context['testCaseId'], '1')
        
    def test_PictureView_picturesExist(self):
        """
        Check that reference and snapshot are found and correct
        """
        response = self.client.get(reverse('pictureView', args=[1, 1, 1]))
        self.assertIsNotNone(response.context['reference'])
        self.assertIsNotNone(response.context['stepSnapshot'])
        
        self.assertIsNone(response.context['reference'].refSnapshot)
        self.assertIsNotNone(response.context['stepSnapshot'].refSnapshot)
        
    def test_PictureView_snapshotDontExist(self):
        """
        Check that no error is raised when one of step / test case / session does not exist
        """
        response = self.client.get(reverse('pictureView', args=[1, 1, 2]))
        self.assertIsNone(response.context['reference'])
        self.assertIsNone(response.context['stepSnapshot'])
        
    def test_PictureViex_makeNewRef(self):
        """
        From a picture which is not a reference (s1), make it a new ref
        """
        
    
        s1 = Snapshot(step=TestStep.objects.get(id=1), session=self.session1, testCase=self.testCase, refSnapshot=self.initialRefSnapshot, pixelsDiff=None)
        s1.save()
        img = ImageFile(open(self.dataDir + "test_Image1.png", 'rb'))
        s1.image.save("img", img)
        s1.save()
        s2 = Snapshot(step=TestStep.objects.get(id=1), session=self.session2, testCase=self.testCase, refSnapshot=self.initialRefSnapshot, pixelsDiff=None)
        s2.save()
        s2.image.save("img", img)
        s2.save()
        
        response = self.client.get(reverse('pictureView', args=[self.session1.id, 1, 1]) + "?makeRef=True")
        
        # check display
        self.assertIsNone(response.context['reference'], "new reference should be the snapshot itself")
        self.assertIsNone(response.context['stepSnapshot'].refSnapshot, "new reference should be the snapshot itself")
        self.assertIsNone(response.context['stepSnapshot'].pixelsDiff)
        DiffComputer.stopThread()
        
        # check s2 ref as been changed
        self.assertEqual(Snapshot.objects.get(id=s2.id).refSnapshot, s1, "ref snapshot for s2 should have changed to s1")
        self.assertEqual(Snapshot.objects.get(id=2).refSnapshot, self.initialRefSnapshot, "snapshot previous to s1 should not have change")
        
    def test_PictureViex_makeRefWhenAlreadyRef(self):
        """
        From a picture which is a reference, send makeRef=True. Nothing should happen
        """
        
        response = self.client.get(reverse('pictureView', args=[4, 3, 1]) + "?makeRef=True")
        
        # check display
        self.assertIsNone(response.context['reference'], "picture is still a reference")
        self.assertIsNone(response.context['stepSnapshot'].refSnapshot, "new reference should be the snapshot itself")
        self.assertIsNone(response.context['stepSnapshot'].pixelsDiff, "no diff as we have a reference")
        DiffComputer.stopThread()
        
    def test_PictureViex_removeVeryFirstRef(self):
        """
        From a picture which is the first reference for a testCase/testStep couple, try to remove the reference
        It should not be possible
        """
        
        response = self.client.get(reverse('pictureView', args=[4, 3, 1]) + "?makeRef=False")
        
        # check display
        self.assertIsNone(response.context['reference'], "picture is still a reference")
        self.assertIsNone(response.context['stepSnapshot'].refSnapshot, "new reference should be the snapshot itself")
        self.assertIsNone(response.context['stepSnapshot'].pixelsDiff, "no diff as we have a reference")
        DiffComputer.stopThread()
        
    def test_PictureViex_removeRefWhenNotRef(self):
        """
        From a picture which is not a reference, send makeRef=False. Nothing should happen
        """
        
        response = self.client.get(reverse('pictureView', args=[5, 3, 1]) + "?makeRef=False")
        
        # check display
        self.assertIsNotNone(response.context['reference'], "picture is still not a reference")
        self.assertIsNotNone(response.context['stepSnapshot'].refSnapshot, "there is still a reference")
        DiffComputer.stopThread()

    def test_PictureViex_removeRef(self):
        """
        From a picture which is a reference (s1), remove the reference flag. Next snpashots (s2) should then refere to the last 
        reference available
        """

        s1 = Snapshot(step=TestStep.objects.get(id=1), session=self.session1, testCase=self.testCase, refSnapshot=None, pixelsDiff=None)
        s1.save()
        img = ImageFile(open(self.dataDir + "test_Image1.png", 'rb'))
        s1.image.save("img", img)
        s1.save()
        s2 = Snapshot(step=TestStep.objects.get(id=1), session=self.session2, testCase=self.testCase, refSnapshot=s1, pixelsDiff=None)
        s2.save()
        s2.image.save("img", img)
        s2.save()
        
        response = self.client.get(reverse('pictureView', args=[self.session1.id, 1, 1]) + "?makeRef=False")
        
        # check display
        self.assertEqual(response.context['reference'], self.initialRefSnapshot, "new reference should be the first snapshot")
        self.assertEqual(response.context['stepSnapshot'].refSnapshot, self.initialRefSnapshot, "new reference should be the first snapshot")
        self.assertIsNotNone(response.context['stepSnapshot'].pixelsDiff)
        DiffComputer.stopThread()
        
        # check s2 ref as been changed
        self.assertEqual(Snapshot.objects.get(id=s2.id).refSnapshot, self.initialRefSnapshot, "ref snapshot for s2 should have changed to first snapshot")
        