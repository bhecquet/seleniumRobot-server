from rest_framework.test import APITestCase
from snapshotServer.tests import authenticate_test_client_for_api
import os
from django.conf import settings
from snapshotServer.models import ExecutionLogs
from pathlib import Path

class TestExecutionLogsApiView(APITestCase):
    fixtures = ['snapshotServer.yaml']
    
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        authenticate_test_client_for_api(self.client)
        
        
    def tearDown(self):
        """
        Remove generated files
        """
        
        super().tearDown()
        
        for f in os.listdir(self.media_dir):
            if f.startswith('engie') or f.startswith('replyDetection'):
                os.remove(self.media_dir + os.sep + f)
                      
  
                   
    def test_delete_file(self):
        """
        Check file is uploaded
        """
        
        with open('snapshotServer/tests/data/test.html', 'rb') as fp:
            response = self.client.post('/snapshot/api/logs/', data={'testCase': 1, 'file': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            
            file = ExecutionLogs.objects.filter(testCase__id=1).last()
            file_path = Path(file.file.path)
            self.assertTrue(file_path.exists())
            file.delete()
            self.assertFalse(file_path.exists())

            
            