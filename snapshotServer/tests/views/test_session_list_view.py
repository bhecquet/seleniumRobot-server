'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse

from snapshotServer.models import TestEnvironment
from snapshotServer.tests.views.test_views import TestViews


class TestSessionListView(TestViews):


    def test_no_filter(self):
        """
        rendering when we arrive on page. No session found because no filter given
        """
        response = self.client.get(reverse('sessionListView', kwargs={'version_id': 1}))
        self.assertEqual(len(response.context['sessions']), 0)
        self.assertEqual(len(response.context['browsers']), 0)
        self.assertEqual(len(response.context['selectedBrowser']), 0)
        self.assertEqual(len(response.context['environments']), 2) # only DEV/AUT in test data
        self.assertEqual(len(response.context['selectedEnvironments']), 0)
        self.assertTrue('error' in response.context)

    def test_missingFilter(self):
        """
        Filtering when not all select box are chosen lead to empty session list and error message
        """
        response = self.client.get(reverse('sessionListView', kwargs={'version_id': 1}), data={'environment': ['1'], 'browser': ['firefox'], 'sessionName': ['session1']})
        self.assertEqual(len(response.context['sessions']), 0)
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 2) # only DEV/AUT in test data
        self.assertEqual(len(response.context['selectedEnvironments']), 1)
        self.assertTrue('error' in response.context)

    def test_onlyEnvironmentFilter(self):
        """
        Filtering when not all select box are chosen lead to empty session list and error message
        """
        response = self.client.get(reverse('sessionListView', kwargs={'version_id': 1}), data={'environment': ['1']})
        self.assertEqual(len(response.context['sessions']), 0)
        self.assertEqual(response.context['sessionNames'], ['', 'session1', 'session2'])    
        self.assertEqual(len(response.context['browsers']), 0)     # only firefox in test data
        self.assertEqual(len(response.context['environments']), 2) # only DEV/AUT in test data
        self.assertEqual(len(response.context['selectedEnvironments']), 1)
        self.assertTrue('error' in response.context)

    def test_allFilter(self):
        """
        Filtering done when all fields are filled
        3 sessions correspond to input parameters but one 2 them (id=7) has the compareSnapshot flag set to false
        Only one session should be returned
        """
        response = self.client.get(reverse('sessionListView', kwargs={'version_id': 1}), data={'browser': ['firefox'], 'environment': [1], 'testcase': [4], 'sessionName': ['session1']})
        self.assertEqual(len(response.context['sessions']), 2)      
        self.assertEqual(response.context['sessionNames'], ['', 'session1', 'session2'])      
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 2) # only DEV/AUT in test data
        self.assertEqual(response.context['selectedEnvironments'][0], TestEnvironment.objects.get(id=1))
        self.assertTrue('error' not in response.context)

    def test_all_filter_with_date(self):
        """
        When date are selected, we should get only session from the 06th may
        """
        response = self.client.get(reverse('sessionListView', kwargs={'version_id': 1}), data={'browser': ['firefox'], 
                                                                                              'environment': [1], 
                                                                                              'testcase': [4],
                                                                                              'sessionFrom': '06-05-2017',
                                                                                              'sessionTo': '06-05-2017', 
                                                                                              'sessionName': ['session1']
        })
        self.assertEqual(len(response.context['sessions']), 1)
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 2) # only DEV/AUT in test data
        self.assertEqual(response.context['selectedEnvironments'][0], TestEnvironment.objects.get(id=1))
        self.assertTrue('error' not in response.context)
        