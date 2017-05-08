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

    def test_TestList_sessionIdAdded(self):
        """
        Simple test to show that we get all test cases from session
        """
        response = self.client.get(reverse('testlistView', args=[1]))
        self.assertEqual(len(response.context['sessionId']), 1)

    def test_TestList_noTest(self):
        """
        Simple test to show that we get all test cases from session
        """
        response = self.client.get(reverse('testlistView', args=[2]))
        self.assertEqual(len(response.context['object_list']), 0)
        
