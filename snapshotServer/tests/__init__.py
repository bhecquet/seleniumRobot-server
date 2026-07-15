from commonsServer.tests.test_parent import TestWebAndAdmin
from snapshotServer.controllers.diff_computer import DiffComputer
from django.conf import settings
import logging
import re
import os

class SnapshotTestCase(TestWebAndAdmin):

    dataDir = 'snapshotServer/tests/data/'
    media_dir = settings.MEDIA_ROOT + os.sep + 'documents'
    
    def setUp(self):
        logging.error(str(self))
        super().setUp()
    
    def tearDown(self):
        DiffComputer.stopThread()
        logging.error("Stop threads")
        super().tearDown()

        for f in os.listdir(self.media_dir):
            if f.startswith('img_'):
                os.remove(self.media_dir + os.sep + f)
            
    def remove_spaces(self, html_code):
        new_html = html_code.replace("\n", "").replace("\r",  "")
        new_html = re.sub(">\\s+<", "><", new_html)
        new_html = re.sub("\\s+<", "<", new_html)
        new_html = re.sub(">\\s+", ">", new_html)
        return new_html