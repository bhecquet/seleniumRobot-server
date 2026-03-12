'''
Created on 25 janv. 2021

@author: S047432
'''

from django.test.utils import override_settings
from django.urls.base import reverse
from rest_framework.test import APITestCase

class TestSerializers(APITestCase):
    '''
    Using APITestCase as we call the REST Framework API
    Client handles patch / put cases
    '''
    fixtures = ['varServer.yaml']


    def test_no_api_security(self):
        """
        protected variable values can be seen when API security is disabled
        """
        with self.settings(SECURITY_API_ENABLED=''):
            response = self.client.get(reverse('variableApi'), data={'version': 2, 'environment': 3, 'test': 1, 'name': 'proxyPassword2'})
            self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
         
            # check variable is not protected as user is authenticated
            self.assertEqual(response.data[0]['value'], 'azertyuiop')
