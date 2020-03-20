'''
Created on 26 juil. 2017

@author: worm
'''

from django.urls.base import reverse
from snapshotServer.tests.views.Test_Views import TestViews


class Test_RecomputeDiffView(TestViews):

   
    def test_RecomputeDiff_snapshotExistNoRef(self):
        """
        Send recompute request whereas no ref exists. Nothing should be done
        """
              
        response = self.client.post(reverse('recompute', args=[1]))
        self.assertEqual(response.status_code, 304, "No ref for this snapshot, 304 should be returned")
          
    def test_RecomputeDiff_snapshotExistWithRef(self):
        """
        Reference exists for the snapshot, do computing
        """
              
        response = self.client.post(reverse('recompute', args=[2]))
        self.assertEqual(response.status_code, 200, "Reference exists for the snapshot, do computing")
          
          
    def test_RecomputeDiff_snapshotDoesNotExist(self):
        """
        Reference exists for the snapshot, do computing
        """
              
        response = self.client.post(reverse('recompute', args=[25]))
        self.assertEqual(response.status_code, 404, "404 should be returned as snapshot does not exist")
          