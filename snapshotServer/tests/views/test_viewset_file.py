from rest_framework.test import APITestCase
from snapshotServer.tests import authenticate_test_client_for_api
import os
from django.conf import settings
from snapshotServer.models import File
from pathlib import Path
import zipfile

class TestFileApiView(APITestCase):
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
                
                
    def test_upload_image_file(self):
        """
        Check file is uploaded
        """
        
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post('/snapshot/api/file/', data={'stepResult': 1, 'file': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            
            file = File.objects.filter(stepResult__id=1).last()
            self.assertTrue(file.file.name.endswith(".png"))
            self.assertTrue(Path(file.file.path).exists())
            
                   
    def test_delete_file(self):
        """
        Check file is uploaded
        """
        
        with open('snapshotServer/tests/data/engie.png', 'rb') as fp:
            response = self.client.post('/snapshot/api/file/', data={'stepResult': 1, 'file': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            
            file = File.objects.filter(stepResult__id=1).last()
            file_path = Path(file.file.path)
            self.assertTrue(file_path.exists())
            file.delete()
            self.assertFalse(file_path.exists())
                
    def test_upload_html_file(self):
        """
        Check file is uploaded and zipped at the same time
        """
        
        with open('snapshotServer/tests/data/test.html', 'rb') as fp:
            response = self.client.post('/snapshot/api/file/', data={'stepResult': 1, 'file': fp})
            self.assertEqual(response.status_code, 201, 'status code should be 201')
            
            file = File.objects.filter(stepResult__id=1).last()
            self.assertTrue(file.file.name.endswith(".zip"))
            self.assertTrue(Path(file.file.path).exists())
            
            with zipfile.ZipFile(file.file.path) as zip:
                with zip.open('test.html', 'r') as myfile:
                    self.assertTrue('<html>' in myfile.read().decode('utf-8'))
                
    def test_upload_html_file_in_error(self):
        """
        Check file is uploaded and zipped at the same time
        """

        response = self.client.post('/snapshot/api/file/', data={'stepResult': 1})
        self.assertEqual(response.status_code, 500, 'status code should be 201')



            
            