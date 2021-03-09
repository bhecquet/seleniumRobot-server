'''
Created on 11 mai 2017

@author: bhecquet
'''
from snapshotServer.models import Version, Application
from snapshotServer.tests import SnapshotTestCase


class TestVersions(SnapshotTestCase):


    def test_findPreviousVersions(self):
        app = Application(name="test")
        app.save()
        v1 = Version(application=app, name='1.0')
        v1.save()
        v2 = Version(application=app, name='2.0')
        v2.save()
        v3 = Version(application=app, name='3.0')
        v3.save()
    
        self.assertEqual(v2.previousVersions(), [v1], "version selection was wrong")
    
    def test_findPreviousVersionsDisorder(self):
        app = Application(name="test")
        app.save()
        v2 = Version(application=app, name='2.0')
        v2.save()
        v1 = Version(application=app, name='1.0')
        v1.save()
        v3 = Version(application=app, name='3.0')
        v3.save()
    
        self.assertEqual(v3.previousVersions(), [v1, v2], "version ordering was wrong")
    
    def test_findPreviousVersionsWithSeveralApps(self):
        app = Application(name="test")
        app.save()
        app2 = Application(name="test2")
        app2.save()
        v1 = Version(application=app, name='1.0')
        v1.save()
        v1bis = Version(application=app2, name='1.1')
        v1bis.save()
        v2 = Version(application=app, name='2.0')
        v2.save()
        v3 = Version(application=app, name='3.0')
        v3.save()
    
        self.assertEqual(v2.previousVersions(), [v1], "version selection was wrong, probably due to different application")
    
    def test_noPreviousVersion(self):
        app = Application(name="test")
        app.save()
        v1 = Version(application=app, name='1.0')
        v1.save()
        v2 = Version(application=app, name='2.0')
        v2.save()
        self.assertEqual(v1.previousVersions(), [], "version ordering was wrong")
        
    def test_findNextVersions(self):
        app = Application(name="test")
        app.save()
        v1 = Version(application=app, name='1.0')
        v1.save()
        v2 = Version(application=app, name='2.0')
        v2.save()
        v3 = Version(application=app, name='3.0')
        v3.save()
    
        self.assertEqual(v2.nextVersions(), [v2, v3], "version selection was wrong")
    
    def test_findNextVersionsDisorder(self):
        app = Application(name="test")
        app.save()
        v2 = Version(application=app, name='2.0')
        v2.save()
        v1 = Version(application=app, name='1.0')
        v1.save()
        v3 = Version(application=app, name='3.0')
        v3.save()
    
        self.assertEqual(v1.nextVersions(), [v1, v2, v3], "version ordering was wrong")
    
    def test_findNextVersionsWithSeveralApps(self):
        app = Application(name="test")
        app.save()
        app2 = Application(name="test2")
        app2.save()
        v1 = Version(application=app, name='1.0')
        v1.save()
        v1bis = Version(application=app2, name='1.1')
        v1bis.save()
        v2 = Version(application=app, name='2.0')
        v2.save()
    
        self.assertEqual(v1.nextVersions(), [v1, v2], "version selection was wrong, probably due to different application")
    
    def test_noNextVersion(self):
        app = Application(name="test")
        app.save()
        v1 = Version(application=app, name='1.0')
        v1.save()
        v2 = Version(application=app, name='2.0')
        v2.save()
        self.assertEqual(v2.nextVersions(), [v2], "version ordering was wrong")