'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse

from snapshotServer.models import TestEnvironment
from snapshotServer.tests.views.Test_Views import TestViews


class Test_SessionListView(TestViews):


    def test_noFilter(self):
        """
        rendering when we arrive on page. No session found because no filter given
        """
        response = self.client.get(reverse('sessionListView', kwargs={'versionId': 1}))
        self.assertEqual(len(response.context['sessions']), 0)
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(len(response.context['selectedBrowser']), 0)
        self.assertEqual(len(response.context['environments']), 1) # only DEV in test data
        self.assertEqual(len(response.context['selectedEnvironments']), 0)
        self.assertTrue('error' in response.context)

    def test_missingFilter(self):
        """
        Filtering when not all select box are chosen lead to empty session list and error message
        """
        response = self.client.get(reverse('sessionListView', kwargs={'versionId': 1}), data={'browser': ['firefox']})
        self.assertEqual(len(response.context['sessions']), 0)
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 1) # only DEV in test data
        self.assertEqual(len(response.context['selectedEnvironments']), 0)
        self.assertTrue('error' in response.context)

    def test_allFilter(self):
        """
        Filtering done when all fields are filled
        3 sessions correspond to input parameters but one 2 them (id=7) has the compareSnapshot flag set to false
        Only one session should be returned
        """
        response = self.client.get(reverse('sessionListView', kwargs={'versionId': 1}), data={'browser': ['firefox'], 'environment': [1], 'testcase': [4]})
        self.assertEqual(len(response.context['sessions']), 2)      
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 1) # only DEV in test data
        self.assertEqual(response.context['selectedEnvironments'][0], TestEnvironment.objects.get(id=1))
        self.assertTrue('error' not in response.context)

    def test_allFilterWithDate(self):
        """
        When date are selected, we should get only session from the 06th may
        """
        response = self.client.get(reverse('sessionListView', kwargs={'versionId': 1}), data={'browser': ['firefox'], 
                                                                                              'environment': [1], 
                                                                                              'testcase': [4],
                                                                                              'sessionFrom': '06-05-2017',
                                                                                              'sessionTo': '06-05-2017'})
        self.assertEqual(len(response.context['sessions']), 1)
        self.assertEqual(len(response.context['browsers']), 1)     # only firefox in test data
        self.assertEqual(response.context['selectedBrowser'], ['firefox'])
        self.assertEqual(len(response.context['environments']), 1) # only DEV in test data
        self.assertEqual(response.context['selectedEnvironments'][0], TestEnvironment.objects.get(id=1))
        self.assertTrue('error' not in response.context)
        