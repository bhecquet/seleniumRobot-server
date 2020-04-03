'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse

from snapshotServer.models import TestEnvironment, TestCase
from snapshotServer.tests.views.Test_Views import TestViews


class TestResultTableView(TestViews):


    def test_no_filter(self):
        """
        rendering when we arrive on page. 0 session found because no env is provided by default
        """
        response = self.client.get(reverse('testResultTableView', kwargs={'version_id': 1}))
        self.assertEqual(len(response.context['sessions']), 0)
        self.assertEqual(len(response.context['browsers']), 2)     # only firefox/chrome in test data
        self.assertEqual(len(response.context['selectedBrowser']), 2) # all browsers are selected by default
        self.assertEqual(len(response.context['environments']), 2) # only DEV/AUT in test data
        self.assertEqual(len(response.context['selectedEnvironments']), 0)
        self.assertTrue('testCaseTable' in response.context)
  
    def test_all_filter_no_date(self):
        """
        Filtering done when all fields are filled but date
        Dates are mandatory for filter or else nothing is resturned
        """
        response = self.client.get(reverse('testResultTableView', kwargs={'version_id': 1}), data={'browser': ['firefox'], 'environment': [1], 'testcase': [4]})
        self.assertEqual(len(response.context['sessions']), 0)      
        self.assertEqual(len(response.context['browsers']), 2)     # only firefox/chrome in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 2) # only DEV/AUT in test data
        self.assertEqual(response.context['selectedEnvironments'][0], TestEnvironment.objects.get(id=1))
        self.assertTrue('testCaseTable' in response.context)
 
    def test_all_filter_with_date(self):
        """
        When date are selected, we should get only session from the 06th may
        """
        response = self.client.get(reverse('testResultTableView', kwargs={'version_id': 1}), data={'browser': ['firefox'], 
                                                                                              'environment': [1], 
                                                                                              'testcase': [4],
                                                                                              'sessionFrom': '06-05-2017',
                                                                                              'sessionTo': '07-05-2017'})
        self.assertEqual(len(response.context['sessions']), 2)
        self.assertEqual(len(response.context['browsers']), 2)     # only firefox/chrome in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 2) # only DEV/AUT in test data
        self.assertEqual(response.context['selectedEnvironments'][0], TestEnvironment.objects.get(id=1))
        
        # check content of test case table. For each test, we should have the list of sessions. Here, the 2 sessions 
        # have the same test
        tc = TestCase.objects.get(pk=4)
        self.assertEqual(len(response.context['testCaseTable']), 1)
        self.assertEqual(len(response.context['testCaseTable'][tc]), 2)
        
        