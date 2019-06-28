'''
Created on 28 juin 2019

@author: s047432
'''
from django.urls.base import reverse
from rest_framework.test import APITestCase
from elementInfoServer.models import ElementInfo

class TestApi(APITestCase):
    '''
    Using APITestCase as we call the REST Framework API
    Client handles patch / put cases
    '''
    fixtures = ['elementInfoServer.yaml']

    def test_elementinfo_deletion(self):
        """
        Check that after 30 days, elementInfo is deleted if never updated
        """
        all_element_info = len(ElementInfo.objects.all())
        
        response = self.client.get(reverse('elementInfoApi'), data={})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
      
        current_element_info = len(ElementInfo.objects.all())
        self.assertTrue(all_element_info > current_element_info)
    
    def test_get_element_info_with_application(self):
        """
        Test we get only element info corresponding to selected application
        """
        response = self.client.get(reverse('elementInfoApi'), data={'version': 2, 'application': 1})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
             
        # check filtering is correct. We should not get any elementInfo corresponding to an other environment, test or version
        for element_info in response.data:
            self.assertTrue(element_info['application'] == 1, "ElementInfo %s should not be get as application is different from 1" % element_info['name'])
             
    
    def test_get_element_info_with_ids(self):
        """
        Test we get only element info corresponding to selected ids
        """
        response = self.client.get(reverse('elementInfoApi'), data={'version': 2, 'application': 1, 'ids': '1'})
        self.assertEqual(response.status_code, 200, 'status code should be 200: ' + str(response.content))
             
        # check filtering is correct. We should not get any elementInfo corresponding to an other environment, test or version
        for element_info in response.data:
            self.assertTrue(element_info['id'] == 1, "ElementInfo %s should not be get as id is different from 1" % element_info['name'])

