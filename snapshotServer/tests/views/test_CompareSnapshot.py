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
    TestEnvironment, Version, TestCaseInSession
from snapshotServer.controllers.PictureComparator import Pixel


class test_CompareSnapshot(django.test.TestCase):
    
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
    
    def tearDown(self):
        """
        Remove generated files
        """
        
        for f in os.listdir(self.mediaDir):
            if f.startswith('img_'):
                os.remove(self.mediaDir + os.sep + f)

    def test_ApplicationList_getList(self):
        """
        Application list should be rendered
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(len(response.context['object_list']), 2)

    def test_ApplicationList_selectAnApplication(self):
        """
        Redirect as we selected an application
        """
        response = self.client.post(reverse('home'), data={'application': 1})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/snapshot/compare/1/')

    def test_ApplicationList_noApplicationSelected(self):
        """
        Application list should be rendered and error displayed because an inexisting application has been requested
        """
        response = self.client.post(reverse('home'), data={'application': 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertTrue('error' in response.context)

    def test_SessionList_noFilter(self):
        """
        rendering when we arrive on page. No session found because no filter given
        """
        response = self.client.get(reverse('sessionListView', kwargs={'versionId': 1}))
        self.assertEqual(len(response.context['sessions']), 0)
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(len(response.context['selectedBrowser']), 0)
        self.assertEqual(len(response.context['environments']), 1) # only DEV in test data
        self.assertEqual(len(response.context['selectedEnvironments']), 0)
        self.assertTrue('error' in response.context)

    def test_SessionList_missingFilter(self):
        """
        Filtering when not all select box are chosen lead to empty session list and error message
        """
        response = self.client.get(reverse('sessionListView', kwargs={'versionId': 1}), data={'browser': ['firefox']})
        self.assertEqual(len(response.context['sessions']), 0)
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 1) # only DEV in test data
        self.assertEqual(len(response.context['selectedEnvironments']), 0)
        self.assertTrue('error' in response.context)

    def test_SessionList_allFilter(self):
        """
        Filtering done when all fields are filled
        """
        response = self.client.get(reverse('sessionListView', kwargs={'versionId': 1}), data={'browser': ['firefox'], 'environment': [1], 'testcase': [4]})
        self.assertEqual(len(response.context['sessions']), 2)
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 1) # only DEV in test data
        self.assertEqual(response.context['selectedEnvironments'][0], TestEnvironment.objects.get(id=1))
        self.assertTrue('error' not in response.context)

    def test_SessionList_allFilterWithDate(self):
        """
        When date are selected, we should get only session from the 06th may
        """
        response = self.client.get(reverse('sessionListView', kwargs={'versionId': 1}), data={'browser': ['firefox'], 
                                                                                              'environment': [1], 
                                                                                              'testcase': [4],
                                                                                              'sessionFrom': '06-05-2017',
                                                                                              'sessionTo': '06-05-2017'})
        self.assertEqual(len(response.context['sessions']), 1)
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 1) # only DEV in test data
        self.assertEqual(response.context['selectedEnvironments'][0], TestEnvironment.objects.get(id=1))
        self.assertTrue('error' not in response.context)
 
    def test_TestList_testExists(self):
        """
        Simple test to show that we get all test cases from session
        """
        response = self.client.get(reverse('testlistView', args=[1]))
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(list(response.context['object_list'])[0].testCase.name, "test1")
  
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
        self.assertEqual(list(response.context['object_list'])[0].name, "Step 1")
  
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
          
    def test_PictureView_makeNewRef(self):
        """
        From a picture which is not a reference (s1), make it a new ref
        """
          
      
        s1 = Snapshot(step=TestStep.objects.get(id=1), session=self.session1, testCase=self.tcs1, refSnapshot=self.initialRefSnapshot, pixelsDiff=None)
        s1.save()
        img = ImageFile(open(self.dataDir + "test_Image1.png", 'rb'))
        s1.image.save("img", img)
        s1.save()
        s2 = Snapshot(step=TestStep.objects.get(id=1), session=self.session2, testCase=self.tcs2, refSnapshot=self.initialRefSnapshot, pixelsDiff=None)
        s2.save()
        s2.image.save("img", img)
        s2.save()
          
        response = self.client.get(reverse('pictureView', args=[self.session1.id, self.tcs1.id, 1]) + "?makeRef=True")
          
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
  
        s1 = Snapshot(step=TestStep.objects.get(id=1), session=self.session1, testCase=self.tcs1, refSnapshot=None, pixelsDiff=None)
        s1.save()
        img = ImageFile(open(self.dataDir + "test_Image1.png", 'rb'))
        s1.image.save("img", img)
        s1.save()
        s2 = Snapshot(step=TestStep.objects.get(id=1), session=self.session2, testCase=self.tcs2, refSnapshot=s1, pixelsDiff=None)
        s2.save()
        s2.image.save("img", img)
        s2.save()
          
        response = self.client.get(reverse('pictureView', args=[self.session1.id, self.tcs1.id, 1]) + "?makeRef=False")
          
        # check display
        self.assertEqual(response.context['reference'], self.initialRefSnapshot, "new reference should be the first snapshot")
        self.assertEqual(response.context['stepSnapshot'].refSnapshot, self.initialRefSnapshot, "new reference should be the first snapshot")
        self.assertIsNotNone(response.context['stepSnapshot'].pixelsDiff)
        DiffComputer.stopThread()
          
        # check s2 ref as been changed
        self.assertEqual(Snapshot.objects.get(id=s2.id).refSnapshot, self.initialRefSnapshot, "ref snapshot for s2 should have changed to first snapshot")
          
    def test_RecomputeDiff_snapshotExistNoRef(self):
        """
        Send recompute request whereas no ref exists. Nothing should be done
        """
              
        response = self.client.post(reverse('recompute', args=[1]))
        self.assertEqual(response.status_code, 304, "No ref for this snapshot, 304 should be returned")
          
    def test_RecomputeDiff_snapshotExistWithRef(self):
        """
        Reference exists for the snapshot, do computing
        """
              
        response = self.client.post(reverse('recompute', args=[2]))
        self.assertEqual(response.status_code, 200, "Reference exists for the snapshot, do computing")
          
          
    def test_RecomputeDiff_snapshotDoesNotExist(self):
        """
        Reference exists for the snapshot, do computing
        """
              
        response = self.client.post(reverse('recompute', args=[25]))
        self.assertEqual(response.status_code, 404, "404 should be returned as snapshot does not exist")
          
    def test_TestStatus_sessionStatusOkOnReference(self):
        """
        Test the result of a test session status when looking for reference
        """
        response = self.client.get(reverse('testStatusView', kwargs={'sessionId': 6, 'testCaseId': 4}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('UTF-8'), encoding='UTF-8')
        self.assertTrue(data['5'])
          
    def test_TestStatus_sessionStatusOkOnNonReference(self):
        """
        Test the result of a test session status when snapshot are not reference
        """
        # no diff for snapshots
        s1 = Snapshot.objects.get(pk=8)
        s1.pixelsDiff = pickle.dumps([])
        s1.save()
        s2 = Snapshot.objects.get(pk=9)
        s2.pixelsDiff = pickle.dumps([])
        s2.save()
        s3 = Snapshot.objects.get(pk=10)
        s3.pixelsDiff = pickle.dumps([])
        s3.save()
          
        response = self.client.get(reverse('testStatusView', kwargs={'sessionId': 7, 'testCaseId': 4}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('UTF-8'), encoding='UTF-8')
        self.assertTrue(data['8'])
          
    def test_TestStatus_sessionStatusKo(self):
        """
        Test the result of a test session status when snapshot are not reference
        """
        # diff for last snapshots
        s1 = Snapshot.objects.get(pk=8)
        s1.pixelsDiff = pickle.dumps([])
        s1.save()
        s2 = Snapshot.objects.get(pk=9)
        s2.pixelsDiff = pickle.dumps([])
        s2.save()
        s3 = Snapshot.objects.get(pk=10)
        s3.pixelsDiff = pickle.dumps([Pixel(1,1)])
        s3.save()
          
        response = self.client.get(reverse('testStatusView', kwargs={'sessionId': 7, 'testCaseId': 4}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('UTF-8'), encoding='UTF-8')
        self.assertTrue(data['8'])
        self.assertTrue(data['9'])
        self.assertFalse(data['10'])
         
    def test_TestStatus_stepStatus(self):
        """
        Test the result of a test session status when looking for reference
        """
        response = self.client.get(reverse('testStepStatusView', kwargs={'sessionId': 6, 'testCaseId': 4, 'testStepId': 2}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('UTF-8'), encoding='UTF-8')
        self.assertTrue(data['5'])
        
        