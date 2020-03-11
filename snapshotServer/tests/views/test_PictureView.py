'''
Created on 26 juil. 2017

@author: worm
'''

from django.core.files.images import ImageFile
from django.urls.base import reverse

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.models import Snapshot, TestStep
from snapshotServer.tests.views.Test_Views import Test_Views


class Test_PictureView(Test_Views):


    def test_picturesExist(self):
        """
        Check that reference and snapshot are found and correct
        With this Test Step, reference should be found (snapshot.id = 2)
        """
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 100, 'testStepId': 1}))
        self.assertIsNotNone(response.context['reference'])
        self.assertIsNotNone(response.context['stepSnapshot'])
          
        self.assertIsNone(response.context['reference'].refSnapshot)
        self.assertIsNotNone(response.context['stepSnapshot'].refSnapshot)
          
    def test_snapshotDontExist(self):
        """
        Check that no error is raised when one of step / test case / session does not exist
        """
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 1, 'testStepId': 2}))
        self.assertIsNone(response.context['reference'])
        self.assertIsNone(response.context['stepSnapshot'])
          
    def test_makeNewRef(self):
        """
        From a picture which is not a reference (s1), make it a new ref
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:  
            s1 = Snapshot(stepResult=self.sr1, refSnapshot=self.initialRefSnapshot, pixelsDiff=None)
            s1.save()
            img = ImageFile(imgFile)
            s1.image.save("img", img)
            s1.save()
            s2 = Snapshot(stepResult=self.sr2, refSnapshot=self.initialRefSnapshot, pixelsDiff=None)
            s2.save()
            s2.image.save("img", img)
            s2.save()
              
            response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs1.id, 'testStepId': 1}) + "?makeRef=True")
              
            # check display
            self.assertIsNone(response.context['reference'], "new reference should be the snapshot itself")
            self.assertIsNone(response.context['stepSnapshot'].refSnapshot, "new reference should be the snapshot itself")
            self.assertIsNone(response.context['stepSnapshot'].pixelsDiff)
            DiffComputer.stopThread()
              
            # check s2 ref as been changed
            self.assertEqual(Snapshot.objects.get(id=s2.id).refSnapshot, s1, "ref snapshot for s2 should have changed to s1")
            self.assertEqual(Snapshot.objects.get(id=2).refSnapshot, self.initialRefSnapshot, "snapshot previous to s1 should not have change")
          
    def test_makeRefWhenAlreadyRef(self):
        """
        From a picture which is a reference, send makeRef=True. Nothing should happen
        """
          
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 3, 'testStepId': 1}) + "?makeRef=True")
          
        # check display
        self.assertIsNone(response.context['reference'], "picture is still a reference")
        self.assertIsNone(response.context['stepSnapshot'].refSnapshot, "new reference should be the snapshot itself")
        self.assertIsNone(response.context['stepSnapshot'].pixelsDiff, "no diff as we have a reference")
        DiffComputer.stopThread()
          
    def test_removeVeryFirstRef(self):
        """
        From a picture which is the first reference for a testCase/testStep couple, try to remove the reference
        It should not be possible
        """
          
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 3, 'testStepId': 1}) + "?makeRef=False")
          
        # check display
        self.assertIsNone(response.context['reference'], "picture is still a reference")
        self.assertIsNone(response.context['stepSnapshot'].refSnapshot, "new reference should be the snapshot itself")
        self.assertIsNone(response.context['stepSnapshot'].pixelsDiff, "no diff as we have a reference")
        DiffComputer.stopThread()
          
    def test_removeRefWhenNotRef(self):
        """
        From a picture which is not a reference, send makeRef=False. Nothing should happen
        """
          
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 4, 'testStepId': 1}) + "?makeRef=False")
          
        # check display
        self.assertIsNotNone(response.context['reference'], "picture is still not a reference")
        self.assertIsNotNone(response.context['stepSnapshot'].refSnapshot, "there is still a reference")
        DiffComputer.stopThread()
  
    def test_removeRef(self):
        """
        From a picture which is a reference (s1), remove the reference flag. Next snpashots (s2) should then refere to the last 
        reference available
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:  
            s1 = Snapshot(stepResult=self.sr1, refSnapshot=None, pixelsDiff=None)
            s1.save()
            img = ImageFile(imgFile)
            s1.image.save("img", img)
            s1.save()
            s2 = Snapshot(stepResult=self.sr2, refSnapshot=s1, pixelsDiff=None)
            s2.save()
            s2.image.save("img", img)
            s2.save()
              
            response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs1.id, 'testStepId': 1}) + "?makeRef=False")
              
            # check display
            self.assertEqual(response.context['reference'], self.initialRefSnapshot, "new reference should be the first snapshot")
            self.assertEqual(response.context['stepSnapshot'].refSnapshot, self.initialRefSnapshot, "new reference should be the first snapshot")
            self.assertIsNotNone(response.context['stepSnapshot'].pixelsDiff)
            DiffComputer.stopThread()
              
            # check s2 ref as been changed
            self.assertEqual(Snapshot.objects.get(id=s2.id).refSnapshot, self.initialRefSnapshot, "ref snapshot for s2 should have changed to first snapshot")
   
   