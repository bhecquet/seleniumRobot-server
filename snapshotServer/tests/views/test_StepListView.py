'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse
from snapshotServer.tests.views.Test_Views import TestViews


class Test_StepListView(TestViews):


          
    def test_stepExists(self):
        """
        Test that steps are found for our test case
        """
        response = self.client.get(reverse('steplistView', kwargs={'testCaseInSessionId': 1}))
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(list(response.context['object_list'])[0].name, "Step 1")
  
    def test_noStepExists(self):
        """
        Test that no steps are found for our test case
        """
        response = self.client.get(reverse('steplistView', kwargs={'testCaseInSessionId': 20}))
        self.assertEqual(len(response.context['object_list']), 0)
          
    def test_contextComplete(self):
        """
        Test that extra information are added to the context
        """
        response = self.client.get(reverse('steplistView', kwargs={'testCaseInSessionId': 1}))
        self.assertEqual(response.context['testCaseId'], '1')
          