'''
Created on 8 mai 2017

@author: bhecquet
'''

from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse

class test_CompareSnapshot(TestCase):
    
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
        response = self.client.get(reverse('pictureView', args=[1, 1, 1]))
        self.assertIsNotNone(response.context['reference'])
        self.assertIsNotNone(response.context['stepSnapshot'])
        
        self.assertTrue(response.context['reference'].isReference)
        self.assertFalse(response.context['stepSnapshot'].isReference)
        
    def test_PictureView_snapshotExist(self):
        response = self.client.get(reverse('pictureView', args=[1, 1, 2]))
        self.assertIsNotNone(response.context['reference'])
        self.assertIsNone(response.context['stepSnapshot'])
        