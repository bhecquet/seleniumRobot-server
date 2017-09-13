'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse

from snapshotServer.models import StepResult
from snapshotServer.tests.views.Test_Views import Test_Views


class Test_TestResultView(Test_Views):


          
    def test_resultExists(self):
        """
        Test that step results are returned for our test
        """
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 6}))
        self.assertEqual(len(response.context['object_list']), 3)
        self.assertTrue(StepResult.objects.get(pk=8) in response.context['object_list'])
          