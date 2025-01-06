'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse
from snapshotServer.tests.views.test_views import TestViews


class TestTestListView(TestViews):


    def test_test_exists(self):
        """
        Simple test to show that we get all test cases from session
        """
        response = self.client.get(reverse('testlistView', args=[1]))
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertEqual(list(response.context['object_list'])[0].testCase.name, "test1")
  
    def test_session_id_added(self):
        """
        Check that sessionId is available in context
        """
        response = self.client.get(reverse('testlistView', args=[1]))
        self.assertEqual(len(response.context['sessionId']), 1)
  
    def test_no_test(self):
        """
        Test no error raised when no test exist in session
        """
        response = self.client.get(reverse('testlistView', args=[9]))
        self.assertEqual(len(response.context['object_list']), 0)