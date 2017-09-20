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
        
        self.assertEqual(response.context['currentTest'].id, 6)
        self.assertEqual(response.context['stacktrace'], "no logs available")
        
    def test_stacktraceExists(self):
        """
        Test that step results are returned for our test
        """
        response = self.client.get(reverse('testResultView', kwargs={'testCaseInSessionId': 5}))
        self.assertEqual(len(response.context['object_list']), 3)
        self.assertEqual(len(response.context['stacktrace']), 8)
        self.assertTrue('test2' in response.context['stacktrace'][0])
        
          