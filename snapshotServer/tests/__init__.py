from commonsServer.tests.test_parent import TestWebAndAdmin
from snapshotServer.controllers.diff_computer import DiffComputer
import logging
import re

class SnapshotTestCase(TestWebAndAdmin):
    
    def setUp(self):
        logging.error(str(self))
        super().setUp()
    
    def tearDown(self):
        DiffComputer.stopThread()
        logging.error("Stop threads")
        super().tearDown()
            
    def remove_spaces(self, html_code):
        new_html = html_code.replace("\n", "").replace("\r",  "")
        new_html = re.sub(">\\s+<", "><", new_html)
        new_html = re.sub("\\s+<", "<", new_html)
        new_html = re.sub(">\\s+", ">", new_html)
        return new_html