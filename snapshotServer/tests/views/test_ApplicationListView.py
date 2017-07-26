'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse
from snapshotServer.tests.views.Test_Views import Test_Views


class Test_ApplicationListView(Test_Views):

    def test_getList(self):
        """
        Application list should be rendered
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(len(response.context['object_list']), 2)

    def test_selectAnApplication(self):
        """
        Redirect as we selected an application
        """
        response = self.client.post(reverse('home'), data={'application': 1})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/snapshot/compare/1/')

    def test_noApplicationSelected(self):
        """
        Application list should be rendered and error displayed because an inexisting application has been requested
        """
        response = self.client.post(reverse('home'), data={'application': 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)
        self.assertTrue('error' in response.context)