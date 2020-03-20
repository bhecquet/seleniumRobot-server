'''
Created on 26 juil. 2017

@author: worm
'''

from django.core.files.images import ImageFile
from django.urls.base import reverse

from snapshotServer.controllers.DiffComputer import DiffComputer
from snapshotServer.models import Snapshot, TestStep
from snapshotServer.tests.views.Test_Views import TestViews


class TestPictureView(TestViews):


    def test_pictures_exist(self):
        """
        Check that reference and snapshot are found and correct
        With this Test Step, reference should be found (snapshot.id = 2)
        """
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 100, 'testStepId': 1}))
        self.assertIsNotNone(response.context['captureList'][0]['reference'])
        self.assertIsNotNone(response.context['captureList'][0]['stepSnapshot'])
          
        self.assertIsNone(response.context['captureList'][0]['reference'].refSnapshot)
        self.assertIsNotNone(response.context['captureList'][0]['stepSnapshot'].refSnapshot)
          
    def test_snapshot_dont_exist(self):
        """
        Check that no error is raised when one of step / test case / session does not exist
        """
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 1, 'testStepId': 2}))
        self.assertEqual(len(response.context['captureList']), 0, "No picture should be returned")
          
    def test_make_new_ref(self):
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
              
            response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs1.id, 'testStepId': 1}) + "?makeRef=True&snapshotId=" + str(s1.id))
              
            # check display
            self.assertIsNone(response.context['captureList'][0]['reference'], "new reference should be the snapshot itself")
            self.assertIsNone(response.context['captureList'][0]['stepSnapshot'].refSnapshot, "new reference should be the snapshot itself")
            self.assertIsNone(response.context['captureList'][0]['stepSnapshot'].pixelsDiff)
            DiffComputer.stopThread()
              
            # check s2 ref as been changed
            self.assertEqual(Snapshot.objects.get(id=s2.id).refSnapshot, s1, "ref snapshot for s2 should have changed to s1")
            self.assertEqual(Snapshot.objects.get(id=2).refSnapshot, self.initialRefSnapshot, "snapshot previous to s1 should not have change")
          
    def test_multiple_snapshots_per_step(self):
        """
        Test that all snapshots are returned when there are multiple in one test
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:  
            s1 = Snapshot(stepResult=self.sr1, refSnapshot=self.initialRefSnapshot, pixelsDiff=None, name='cap1')
            s1.save()
            img = ImageFile(imgFile)
            s1.image.save("img", img)
            s1.save()
            s2 = Snapshot(stepResult=self.sr1, refSnapshot=self.initialRefSnapshot, pixelsDiff=None, name='cap2')
            s2.save()
            s2.image.save("img", img)
            s2.save()
              
            response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs1.id, 'testStepId': 1}))
            self.assertEqual(len(response.context['captureList']), 2, "2 snapshots should be returned")
            self.assertEqual(response.context['captureList'][0]['name'], 'cap1')
            self.assertEqual(response.context['captureList'][1]['name'], 'cap2')
           
          
    def test_make_ref_when_already_ref(self):
        """
        From a picture which is a reference, send makeRef=True. Nothing should happen
        
        We use
        -   model: snapshotServer.testcaseinsession
            pk: 3
            fields:
                testCase: 3
                session: 4
                testSteps: [1]
        -   model: snapshotServer.stepresult
            pk: 3
            fields: 
                step: 1
                testCase: 3
                result: true
        -   model: snapshotServer.snapshot
            pk: 3
            fields: 
                stepResult: 3
                image: documents/test_Image1.png
        
        """
          
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 3, 'testStepId': 1}) + "?makeRef=True&snapshotId=3")
          
        # check display
        self.assertIsNone(response.context['captureList'][0]['reference'], "picture is still a reference")
        self.assertIsNone(response.context['captureList'][0]['stepSnapshot'].refSnapshot, "new reference should be the snapshot itself")
        self.assertIsNone(response.context['captureList'][0]['stepSnapshot'].pixelsDiff, "no diff as we have a reference")
        DiffComputer.stopThread()
          
    def test_remove_very_first_ref(self):
        """
        From a picture which is the first reference for a testCase/testStep couple, try to remove the reference
        It should not be possible
        
        We use
        -   model: snapshotServer.testcaseinsession
            pk: 3
            fields:
                testCase: 3
                session: 4
                testSteps: [1]
        -   model: snapshotServer.stepresult
            pk: 3
            fields: 
                step: 1
                testCase: 3
                result: true
        -   model: snapshotServer.snapshot
            pk: 3
            fields: 
                stepResult: 3
                image: documents/test_Image1.png
        """
          
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 3, 'testStepId': 1}) + "?makeRef=False&snapshotId=3")
          
        # check display
        self.assertIsNone(response.context['captureList'][0]['reference'], "picture is still a reference")
        self.assertIsNone(response.context['captureList'][0]['stepSnapshot'].refSnapshot, "new reference should be the snapshot itself")
        self.assertIsNone(response.context['captureList'][0]['stepSnapshot'].pixelsDiff, "no diff as we have a reference")
        DiffComputer.stopThread()
          
    def test_remove_ref_when_not_ref(self):
        """
        From a picture which is not a reference, send makeRef=False. Nothing should happen
        
        -   model: snapshotServer.testcaseinsession
            pk: 4
            fields:
                testCase: 3
                session: 5
                testSteps: [1]
        -   model: snapshotServer.stepresult
            pk: 4
            fields: 
                step: 1
                testCase: 4
                result: true
        -   model: snapshotServer.snapshot
            pk: 4
            fields: 
                stepResult: 4
                image: documents/test_Image1Mod.png
                refSnapshot: 3
        """
          
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 4, 'testStepId': 1}) + "?makeRef=False&snapshotId=4")
          
        # check display
        self.assertIsNotNone(response.context['captureList'][0]['reference'], "picture is still not a reference")
        self.assertIsNotNone(response.context['captureList'][0]['stepSnapshot'].refSnapshot, "there is still a reference")
        DiffComputer.stopThread()
  
    def test_remove_ref(self):
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
              
            response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs1.id, 'testStepId': 1}) + "?makeRef=False&snapshotId=" + str(s1.id))
              
            # check display
            self.assertEqual(response.context['captureList'][0]['reference'], self.initialRefSnapshot, "new reference should be the first snapshot")
            self.assertEqual(response.context['captureList'][0]['stepSnapshot'].refSnapshot, self.initialRefSnapshot, "new reference should be the first snapshot")
            self.assertIsNotNone(response.context['captureList'][0]['stepSnapshot'].pixelsDiff)
            DiffComputer.stopThread()
              
            # check s2 ref as been changed
            self.assertEqual(Snapshot.objects.get(id=s2.id).refSnapshot, self.initialRefSnapshot, "ref snapshot for s2 should have changed to first snapshot")
   
   