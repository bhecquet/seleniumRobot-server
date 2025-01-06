'''
Created on 26 juil. 2017

@author: worm
'''

from django.core.files.images import ImageFile
from django.urls.base import reverse

from snapshotServer.controllers.diff_computer import DiffComputer
from snapshotServer.models import Snapshot, ExcludeZone
from snapshotServer.tests.views.test_views import TestViews
from django.test.client import Client
from django.contrib.auth.models import User


class TestPictureView(TestViews):

    def test_creation_when_not_exist_no_security(self):
        """
        Check we cannot access view without being authenticated
        Use an empty client (anonymous user)
        """
        response = Client().get(reverse('pictureView', kwargs={'testCaseInSessionId': 100, 'testStepId': 1}))
        
        # we should get a redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_picture_display_for_authenticated_user_no_permission(self):
        """
        Check we can access view without having permission to edit it
        """
        client = Client()
        user = User.objects.create_user(username='usernoperm', password='pwd')
        client.login(username='usernoperm', password='pwd')
        response = client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 100, 'testStepId': 1}))
        
        # we should get the page, but exclude zones won't be editable
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['editable'])

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
        
        # we should get the page, and exclude zones should be editable
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['editable'])
        self.assertTrue(response.context['enable'])
        self.assertEquals(response.context['testStepName'], "Step 1")

    def test_pictures_exist_no_header(self):
        """
        Check its possible to call picture view from TestResultView, where we do not need step name
        With this Test Step, reference should be found (snapshot.id = 2)
        """
        response = self.client.get(reverse('pictureViewNoHeader', kwargs={'testCaseInSessionId': 100, 'testStepId': 1}))
        self.assertIsNotNone(response.context['captureList'][0]['reference'])
        self.assertIsNotNone(response.context['captureList'][0]['stepSnapshot'])
          
        self.assertIsNone(response.context['captureList'][0]['reference'].refSnapshot)
        self.assertIsNotNone(response.context['captureList'][0]['stepSnapshot'].refSnapshot)
        
        # we should get the page, and exclude zones should be editable
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['editable'])
        self.assertTrue(response.context['enable'])
        self.assertEquals(response.context['testStepName'], "Snapshot comparison")

    def test_no_pictures_exist_no_header(self):
        """
        Check that when no picture exists for comparison, 'enable' should be set to false so that it's not displayed in test report
        """
        response = self.client.get(reverse('pictureViewNoHeader', kwargs={'testCaseInSessionId': 100, 'testStepId': 2}))
        self.assertEqual(len(response.context['captureList']), 0)
      
        # we should get the page, and exclude zones should be editable
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['editable'])
        self.assertFalse(response.context['enable'])
        self.assertEquals(response.context['testStepName'], "Snapshot comparison")
          
    def test_snapshot_dont_exist(self):
        """
        Check that no error is raised when one of step / test case / session does not exist
        """
        response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': 1, 'testStepId': 2}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['captureList']), 0, "No picture should be returned")
          
    def test_make_new_ref(self):
        """
        From a picture which is not a reference (snapshot_future_ref_same_env), make it a new ref
        'snapshot_same_env' should then have 'snapshot_future_ref_same_env' as reference because it has a higher id than 'initialRefSnapshot' and same name / browser / environment / version
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile: 
            
            img = ImageFile(imgFile)
             
            snapshot_future_ref_same_env = Snapshot(stepResult=self.sr1, refSnapshot=self.initialRefSnapshot, pixelsDiff=None)
            snapshot_future_ref_same_env.save()
            snapshot_future_ref_same_env.image.save("img", img)
            snapshot_future_ref_same_env.save()
            
            exclusion1 = ExcludeZone(x=0, y=0, width=10, height=10, snapshot=self.initialRefSnapshot)
            exclusion1.save()
            exclusion2 = ExcludeZone(x=10, y=10, width=10, height=10, snapshot=self.initialRefSnapshot)
            exclusion2.save()
            self.assertEqual(len(ExcludeZone.objects.filter(snapshot=self.initialRefSnapshot)), 2)
            self.assertEqual(len(ExcludeZone.objects.filter(snapshot=snapshot_future_ref_same_env)), 0)
            
            snapshot_same_env = Snapshot(stepResult=self.step_result_same_env, refSnapshot=self.initialRefSnapshot, pixelsDiff=None)
            snapshot_same_env.save()
            snapshot_same_env.image.save("img", img)
            snapshot_same_env.save()
              
            response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs1.id, 'testStepId': 1}) + "?makeRef=True&snapshotId=" + str(snapshot_future_ref_same_env.id))
              
            # check display
            self.assertIsNone(response.context['captureList'][0]['reference'], "new reference should be the snapshot itself")
            self.assertIsNone(response.context['captureList'][0]['stepSnapshot'].refSnapshot, "new reference should be the snapshot itself")
            self.assertIsNone(response.context['captureList'][0]['stepSnapshot'].pixelsDiff)
            DiffComputer.stopThread()
              
            # check snapshot_same_env ref as been changed
            self.assertEqual(Snapshot.objects.get(id=snapshot_same_env.id).refSnapshot, snapshot_future_ref_same_env, "ref snapshot for snapshot_same_env should have changed to snapshot_future_ref_same_env")
            self.assertEqual(Snapshot.objects.get(id=2).refSnapshot, self.initialRefSnapshot, "snapshot previous to snapshot_future_ref_same_env should not have change")
          
            # check 'initialRefSnapshot' has kept its references
            self.assertEqual(len(ExcludeZone.objects.filter(snapshot=self.initialRefSnapshot)), 2)
            
            # check new ref 'snapshot_future_ref_same_env' has got a copy of the exclusion zones
            self.assertEqual(len(ExcludeZone.objects.filter(snapshot=snapshot_future_ref_same_env)), 2)
          
    def test_make_new_ref_diff_image(self):
        """
        Compare 2 pictures (force computation to be sure we have diff data)
        Check we get the diff percentage
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile: 
            with open("snapshotServer/tests/data/test_Image1Mod.png", 'rb') as img_file_mod: 
                
                img = ImageFile(imgFile)
                img_mod = ImageFile(img_file_mod)
                 
                snapshot_future_ref_same_env = Snapshot(stepResult=self.sr1, refSnapshot=self.initialRefSnapshot, pixelsDiff=None)
                snapshot_future_ref_same_env.save()
                snapshot_future_ref_same_env.image.save("img", img)
                snapshot_future_ref_same_env.save()
                
                exclusion1 = ExcludeZone(x=0, y=0, width=10, height=10, snapshot=self.initialRefSnapshot)
                exclusion1.save()
                exclusion2 = ExcludeZone(x=10, y=10, width=10, height=10, snapshot=self.initialRefSnapshot)
                exclusion2.save()
                self.assertEqual(len(ExcludeZone.objects.filter(snapshot=self.initialRefSnapshot)), 2)
                self.assertEqual(len(ExcludeZone.objects.filter(snapshot=snapshot_future_ref_same_env)), 0)
                
                snapshot_same_env = Snapshot(stepResult=self.step_result_same_env, refSnapshot=self.initialRefSnapshot, pixelsDiff=None)
                snapshot_same_env.save()
                snapshot_same_env.image.save("img", img_mod)
                snapshot_same_env.save()
                  
                # force computing
                self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs1.id, 'testStepId': 1}) + "?makeRef=True&snapshotId=" + str(snapshot_future_ref_same_env.id))

                DiffComputer.stopThread()
                
                # ask for the step snapshot and look for data
                response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs_same_env.id, 'testStepId': 1}) + "?snapshotId=" + str(snapshot_same_env.id))
                self.assertIsNotNone(response.context['captureList'][0]['stepSnapshot'].pixelsDiff) 
                self.assertTrue(response.context['captureList'][0]['diffPercentage'] > 0.086) 

                
          
    def test_multiple_snapshots_per_step(self):
        """
        Test that all snapshots are returned when there are multiple in one test
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:  
            
            img = ImageFile(imgFile)
            
            snapshot_ref_same_env = Snapshot(stepResult=self.sr1, refSnapshot=self.initialRefSnapshot, pixelsDiff=None, name='cap1')
            snapshot_ref_same_env.save()
            snapshot_ref_same_env.image.save("img", img)
            snapshot_ref_same_env.save()
            
            snapshot_same_env = Snapshot(stepResult=self.sr1, refSnapshot=self.initialRefSnapshot, pixelsDiff=None, name='cap2')
            snapshot_same_env.save()
            snapshot_same_env.image.save("img", img)
            snapshot_same_env.save()
              
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
  
    def test_remove_ref(self):
        """
        From a picture which is a reference (snapshot_ref_same_env), remove the reference flag. Next snpashots (snapshot_same_env) should then refere to the last 
        reference available
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile: 
            
            img = ImageFile(imgFile)
             
            snapshot_ref_same_env = Snapshot(stepResult=self.sr1, refSnapshot=None, pixelsDiff=None)
            snapshot_ref_same_env.save()
            snapshot_ref_same_env.image.save("img", img)
            snapshot_ref_same_env.save()
            
            snapshot_same_env = Snapshot(stepResult=self.step_result_same_env, refSnapshot=snapshot_ref_same_env, pixelsDiff=None)
            snapshot_same_env.save()
            snapshot_same_env.image.save("img", img)
            snapshot_same_env.save()
              
            response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs1.id, 'testStepId': 1}) + "?makeRef=False&snapshotId=" + str(snapshot_ref_same_env.id))
              
            # check display
            self.assertEqual(response.context['captureList'][0]['reference'], self.initialRefSnapshot, "new reference should be the first snapshot")
            self.assertEqual(response.context['captureList'][0]['stepSnapshot'].refSnapshot, self.initialRefSnapshot, "new reference should be the first snapshot")
            self.assertIsNotNone(response.context['captureList'][0]['stepSnapshot'].pixelsDiff)
            self.assertEqual(response.context['captureList'][0]['diffPercentage'], 0.0)
            DiffComputer.stopThread()
              
            # check snapshot_same_env ref as been changed
            self.assertEqual(Snapshot.objects.get(id=snapshot_same_env.id).refSnapshot, self.initialRefSnapshot, "ref snapshot for snapshot_same_env should have changed to first snapshot")
   
    def test_remove_ref_with_different_env(self):
        """
        Test the case where we remove a ref a we want to make sure that the new reference is searched with the same environment
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:  
            
            img = ImageFile(imgFile)
            
            # snapshot associated to same version, same test case, but other environment as 'initialRefSnapshot'
            snapshot_other_env = Snapshot(stepResult=self.step_result_other_env, refSnapshot=None, pixelsDiff=None)
            snapshot_other_env.save()
            snapshot_other_env.image.save("img", img)
            snapshot_other_env.save()
            
            # reference snapshot associated to same version / test case / environment / browser as 'initialRefSnapshot'
            snapshot_ref_same_env = Snapshot(stepResult=self.sr1, refSnapshot=None, pixelsDiff=None)
            snapshot_ref_same_env.save()
            snapshot_ref_same_env.image.save("img", img)
            snapshot_ref_same_env.save()
            
            # snapshot associated to same version / test case / environment / browser as 'snapshot_ref_same_env'
            snapshot_same_env = Snapshot(stepResult=self.step_result_same_env, refSnapshot=snapshot_ref_same_env, pixelsDiff=None)
            snapshot_same_env.save()
            snapshot_same_env.image.save("img", img)
            snapshot_same_env.save()
            
              
            response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs1.id, 'testStepId': 1}) + "?makeRef=False&snapshotId=" + str(snapshot_ref_same_env.id))
              
            # check display
            self.assertEqual(response.context['captureList'][0]['reference'], self.initialRefSnapshot, "new reference should be the first snapshot")
            self.assertEqual(response.context['captureList'][0]['stepSnapshot'].refSnapshot, self.initialRefSnapshot, "new reference should be the first snapshot")
            self.assertIsNotNone(response.context['captureList'][0]['stepSnapshot'].pixelsDiff)
            DiffComputer.stopThread()
              
            # check 'snapshot_same_env' ref as been changed and its reference snapshot is 'initialRefSnapshot' becaus it's the same environment / test case / version 
            self.assertEqual(Snapshot.objects.get(id=snapshot_same_env.id).refSnapshot, self.initialRefSnapshot, "ref snapshot for 'snapshot_same_env' should have changed to first snapshot")
   
    def test_remove_ref_with_different_browser(self):
        """
        Test the case where we remove a ref a we want to make sure that the new reference is searched with the same browsert 
        """
        with open("snapshotServer/tests/data/test_Image1.png", 'rb') as imgFile:  
            
            img = ImageFile(imgFile)
            
            # snapshot associated to same version, same test case, but other environment as 'initialRefSnapshot'
            snapshot_other_browser = Snapshot(stepResult=self.step_result_other_env, refSnapshot=None, pixelsDiff=None)
            snapshot_other_browser.save()
            snapshot_other_browser.image.save("img", img)
            snapshot_other_browser.save()
            
            # reference snapshot associated to same version / test case / environment / browser as 'initialRefSnapshot'
            snapshot_ref_same_env = Snapshot(stepResult=self.sr1, refSnapshot=None, pixelsDiff=None)
            snapshot_ref_same_env.save()
            snapshot_ref_same_env.image.save("img", img)
            snapshot_ref_same_env.save()
            
            # snapshot associated to same version / test case / environment / browser as 'snapshot_ref_same_env'
            snapshot_same_env = Snapshot(stepResult=self.step_result_same_env, refSnapshot=snapshot_ref_same_env, pixelsDiff=None)
            snapshot_same_env.save()
            snapshot_same_env.image.save("img", img)
            snapshot_same_env.save()
            
              
            response = self.client.get(reverse('pictureView', kwargs={'testCaseInSessionId': self.tcs1.id, 'testStepId': 1}) + "?makeRef=False&snapshotId=" + str(snapshot_ref_same_env.id))
              
            # check display
            self.assertEqual(response.context['captureList'][0]['reference'], self.initialRefSnapshot, "new reference should be the first snapshot")
            self.assertEqual(response.context['captureList'][0]['stepSnapshot'].refSnapshot, self.initialRefSnapshot, "new reference should be the first snapshot")
            self.assertIsNotNone(response.context['captureList'][0]['stepSnapshot'].pixelsDiff)
            DiffComputer.stopThread()
              
            # check 'snapshot_same_env' ref as been changed and its reference snapshot is 'initialRefSnapshot' becaus it's the same environment / test case / version 
            self.assertEqual(Snapshot.objects.get(id=snapshot_same_env.id).refSnapshot, self.initialRefSnapshot, "ref snapshot for 'snapshot_same_env' should have changed to first snapshot, not 'snapshot_other_browser'")
   
   