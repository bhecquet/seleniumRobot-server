'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse
from snapshotServer.tests.views.Test_Views import Test_Views


class Test_TestListView(Test_Views):


    def test_testExists(self):
        """
        Simple test to show that we get all test cases from session
        """
        response = self.client.get(reverse('testlistView', args=[1]))
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(list(response.context['object_list'])[0].testCase.name, "test1")
  
    def test_sessionIdAdded(self):
        """
        Check that sessionId is available in context
        """
        response = self.client.get(reverse('testlistView', args=[1]))
        self.assertEqual(len(response.context['sessionId']), 1)
  
    def test_noTest(self):
        """
        Test no error raised when no test exist in session
        """
        response = self.client.get(reverse('testlistView', args=[2]))
        self.assertEqual(len(response.context['object_list']), 0)