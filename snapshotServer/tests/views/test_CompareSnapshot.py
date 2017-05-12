'''
Created on 8 mai 2017

@author: bhecquet
'''

from django.core.urlresolvers import reverse
from django.test import Client
import django.test

from snapshotServer.models import Snapshot, TestSession, TestStep, TestCase,\
    TestEnvironment


class test_CompareSnapshot(django.test.TestCase):
    
    fixtures = ['snapshotServer.yaml']
    
    def setUp(self):
        self.client = Client()
    

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
        From a picture which is not a reference, make it a new ref
        """
        t1 = TestCase.objects.get(1)
        ses1 = TestSession(sessionId="1237", date="2017-05-07", browser="firefox", environment=TestEnvironment.objects.get(1), testCases=[t1])
        ses1.save()
        ses2 = TestSession(sessionId="1238", date="2017-05-07", browser="firefox", environment=TestEnvironment.objects.get(1), testCases=[t1])
        ses2.save()
        s1 = Snapshot(step=TestStep.objects.get(1), image=None, session=ses1, testCase=t1, refSnapshot=Snapshot.objects.get(1), pixelsDiff=None)
        s1.save()
        s2 = Snapshot(step=TestStep.objects.get(1), image=None, session=ses2, testCase=t1, refSnapshot=Snapshot.objects.get(1), pixelsDiff=None)
        s2.save()
        
        response = self.client.get(reverse('pictureView', args=[ses1.id, 1, 1]), kwargs={'makeRef': 'True'})
        self.assertEqual(response.context['reference'], s1, "new reference should be the snapshot itself")
        self.assertEqual(response.context['stepSnapshot'], s1, "new reference should be the snapshot itself")
        
    # tests:
    # - makeRef à True et False => on vérifie que la référence est mise à jour et que le calcul est relancé
    # - suppression de la toute première référence: cela ne doit pas être possible
        