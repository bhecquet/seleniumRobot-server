'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse
from snapshotServer.tests.views.test_views import TestViews


class TestStepListView(TestViews):


          
    def test_stepExists(self):
        """
        Test that steps are found for our test case
        """
        response = self.client.get(reverse('steplistView', kwargs={'testCaseInSessionId': 1}))
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(list(response.context['object_list'])[0].name, "Step 1")
  
    def test_multiple_steps_with_order(self):
        """
        Test that steps are found for our test case
        """
        response = self.client.get(reverse('steplistView', kwargs={'testCaseInSessionId': 101}))
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertEqual(list(response.context['object_list'])[0].name, "Logged")
        self.assertEqual(list(response.context['object_list'])[1].name, "Login")
  
    def test_no_step_exists(self):
        """
        Test that no steps are found for our test case
        """
        response = self.client.get(reverse('steplistView', kwargs={'testCaseInSessionId': 20}))
        self.assertEqual(len(response.context['object_list']), 0)
          
    def test_context_complete(self):
        """
        Test that extra information are added to the context
        """
        response = self.client.get(reverse('steplistView', kwargs={'testCaseInSessionId': 1}))
        self.assertEqual(response.context['testCaseId'], '1')
