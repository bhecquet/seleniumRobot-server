'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse
from snapshotServer.tests.views.test_views import TestViews
import json
from snapshotServer.models import Snapshot
import pickle
from snapshotServer.controllers.picture_comparator import Pixel


class TestStatusView(TestViews):
    
    def test_session_status_ok_on_reference(self):
        """
        Test the result of a test session status when looking for reference
        """
        response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 5}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('UTF-8'))
        self.assertTrue(data['5'])
          
    def test_session_status_ok_on_non_reference(self):
        """
        Test the result of a test session status when snapshot are not reference
        """
        # no diff for snapshots
        s1 = Snapshot.objects.get(pk=8)
        s1.pixelsDiff = pickle.dumps([])
        s1.save()
        s2 = Snapshot.objects.get(pk=9)
        s2.pixelsDiff = pickle.dumps([])
        s2.save()
        s3 = Snapshot.objects.get(pk=10)
        s3.pixelsDiff = pickle.dumps([])
        s3.save()
          
        response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 6}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('UTF-8'))
        self.assertTrue(data['8'])
          
    def test_session_status_ko(self):
        """
        Test the result of a test session status when snapshot are not reference
        """
        # diff for last snapshots
        s1 = Snapshot.objects.get(pk=8)
        s1.pixelsDiff = pickle.dumps([])
        s1.save()
        s2 = Snapshot.objects.get(pk=9)
        s2.pixelsDiff = pickle.dumps([])
        s2.save()
        s3 = Snapshot.objects.get(pk=10)
        s3.pixelsDiff = pickle.dumps([Pixel(1,1)])
        s3.save()
          
        response = self.client.get(reverse('testStatusView', kwargs={'testCaseId': 6}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('UTF-8'))
        self.assertTrue(data['8'])
        self.assertTrue(data['9'])
        self.assertFalse(data['10'])
         
    def test_step_status(self):
        """
        Test the result of a test session status when looking for reference
        """
        response = self.client.get(reverse('testStepStatusView', kwargs={'testCaseId': 5, 'testStepId': 2}))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('UTF-8'))
        self.assertTrue(data['5'])