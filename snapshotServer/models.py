
from django.db import models

from snapshotServer.controllers.PictureComparator import Rectangle
import pickle
import commonsServer.models
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_delete, pre_delete

class TestEnvironment(commonsServer.models.TestEnvironment):
    class Meta:
        proxy = True

class Application(commonsServer.models.Application):
    class Meta:
        proxy = True

class Version(commonsServer.models.Version):
    class Meta:
        proxy = True

class TestCase(commonsServer.models.TestCase):
    class Meta:
        proxy = True    
    
class TestCaseInSession(models.Model):
    """
    The test case in a test session
    """
    __test__= False  # avoid detecting it as a test class
    testCase = models.ForeignKey(TestCase, related_name="testCaseInSession", on_delete=models.CASCADE)
    session = models.ForeignKey('TestSession', on_delete=models.CASCADE)
    testSteps = models.ManyToManyField("TestStep", related_name="testCase", blank=True)
    stacktrace = models.TextField(null=True)
    
    def isOkWithSnapshots(self):
        """
        Returns True if test is OK for the session in parameter. Look at each step. None of the snapshot should
        show a diff
        """
        
        snapshots = Snapshot.objects.filter(stepResult__testCase=self)
        result = True 
        for snapshot in snapshots:
            if snapshot.pixelsDiff is None:
                continue
            
            try:
                pixels = pickle.loads(snapshot.pixelsDiff)
            except:
                pixels = snapshot.pixelsDiff
            
            result = result and not bool(pixels)
            
        return result
    
    def isOkWithResult(self):
        """
        Returns True if test is OK for the session in parameter. Look at each step. None of the steps should be KO (look at StepResult object)
        """
        
        stepResults = StepResult.objects.filter(testCase=self)

        for stepResult in stepResults:
            if not stepResult.result:
                return False
            
        return True
    
    def __str__(self):
        return "%s - %s" % (self.testCase.name, self.session.version.name)
    
class TestStep(models.Model):
    __test__= False  # avoid detecting it as a test class
    name = models.CharField(max_length=100) 
    
    def __str__(self):
        return self.name 
    
    
    def isOkWithSnapshots(self, testCaseId):
        """
        Returns True if test is OK for the session in parameter. Look at each step. None of the snapshot should
        show a diff
        @param testSessionId: testSessionId
        @param testCaseIdparam: the test case this step belongs
        """
        
        snapshots = Snapshot.objects.filter(stepResult__testCase=testCaseId, stepResult__step=self)
        result = True 
        for snapshot in snapshots:
            if snapshot.pixelsDiff is None:
                continue
            try:
                pixels = pickle.loads(snapshot.pixelsDiff)
            except:
                pixels = snapshot.pixelsDiff
            
            result = result and not bool(pixels)
            
        return result
    
class TestSession(models.Model):
    __test__= False  # avoid detecting it as a test class
    sessionId = models.CharField(max_length=50)
    name = models.CharField(max_length=100, default="")
    date = models.DateTimeField()
    version = models.ForeignKey(Version, related_name='testsession', on_delete=models.CASCADE)
    browser = models.CharField(max_length=20)
    environment = models.ForeignKey(TestEnvironment, related_name='testsession', on_delete=models.CASCADE)
    compareSnapshot = models.BooleanField(default=False)                            # if True, this session will be displayed in snapshot comparator
    ttl = models.IntegerField(default=30) # time to live of the session, in days. After this delay, session may be deleted
    
    def __str__(self):
        if self.name:
            return self.name
        else:
            return "Session %s with %s" % (self.sessionId, self.browser)
    
# TODO delete file when snapshot is removed from database
class Snapshot(models.Model):

    stepResult = models.ForeignKey('StepResult', related_name='snapshots', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='documents/')
    refSnapshot = models.ForeignKey('self', default=None, null=True, on_delete=models.DO_NOTHING)
    pixelsDiff = models.BinaryField(null=True)
    tooManyDiffs = models.BooleanField(default=False)
    name = models.CharField(max_length=100, default="") # name of the snapshot
    compareOption = models.CharField(max_length=100, default="true") # options for comparison
  
    def __str__(self):
        return "%s - %s - %s - %d" % (self.stepResult.testCase.testCase.name, self.stepResult.step.name, self.stepResult.testCase.session.sessionId, self.id) 
    
    def snapshotsUntilNextRef(self, refSnapshot):
        """
        get all snapshots, sharing the same reference snapshot, until the next reference for the same testCase / testStep
        """
        
        # get list of all snapshots following ourself, sharing 'refSnapshot'
        nextSnapshots = Snapshot.objects.filter(stepResult__step=self.stepResult.step, 
                                            stepResult__testCase__testCase__name=self.stepResult.testCase.testCase.name, 
                                            stepResult__testCase__session__version__in=self.stepResult.testCase.session.version.nextVersions(),
                                            refSnapshot=refSnapshot,
                                            id__gt=self.id) \
                                        .order_by('id')
        
        snapshots = []
        
        for snap in nextSnapshots:
            if snap.refSnapshot:
                snapshots.append(snap)
            else:
                break
        
        return snapshots
    
    
    def snapshotWithSameRef(self):
        """
        Returns the list of snapshots sharing the same reference
        """
        if not self.refSnapshot:
            return []
        
        snapshots = Snapshot.objects.filter(stepResult__step=self.stepResult.step, 
                                            stepResult__testCase__testCase__name=self.stepResult.testCase.testCase.name, 
                                            refSnapshot=self.refSnapshot) \
                                        .order_by('id')
                          
        newSnapshots = []              
        for snap in snapshots:
            if snap != self:
                newSnapshots.append(snap)
                
        return newSnapshots
    

@receiver(pre_delete, sender=Snapshot)
def submission_delete(sender, instance, **kwargs):
    """
    When a snapshot is deleted, remove the associated picture
    Also rebuild reference tree for snapshots that could have referenced this one
    """

    from snapshotServer.controllers.DiffComputer import DiffComputer
    
    # deletion of image file
    instance.image.delete(False) 
    
    # recompute references if this snapshot is a reference for other
    for snapshot in instance.snapshotsUntilNextRef(instance):
    
        test_case = instance.stepResult.testCase
        
        # search any reference snapshot that exists previously
        ref_snapshots = Snapshot.objects.filter(stepResult__testCase__testCase__name=test_case.testCase.name, 
                                               stepResult__testCase__session__version=test_case.session.version,
                                               stepResult__step=snapshot.stepResult.step, 
                                               refSnapshot=None,
                                               id__lt=snapshot.id,
                                               name=snapshot.name).exclude(id=instance.id)
         
        # we find a reference snapshot, recompute diff
        if len(ref_snapshots) > 0:
            snapshot.refSnapshot = ref_snapshots.last()
            snapshot.save()
            
            # recompute diff pixels
            DiffComputer.computeNow(snapshot.refSnapshot, snapshot)
            
            # recompute all following snapshot as they will depend on a previous ref
            for snap in snapshot.snapshotsUntilNextRef(snapshot):
                DiffComputer.addJobs(snapshot.refSnapshot, snap)
            
        # no reference snapshot found, only remove information about reference which makes this snapshot a reference    
        else:
            snapshot.refSnapshot = None
            snapshot.save()
            
        
class StepResult(models.Model):
    
    def __str__(self):
        return "result %d " % self.id
    
    step = models.ForeignKey(TestStep, related_name='stepresult', on_delete=models.CASCADE)
    testCase = models.ForeignKey(TestCaseInSession, related_name='stepresult', on_delete=models.CASCADE)
    result = models.BooleanField(null=False)
    duration = models.FloatField(default=0.0)
    stacktrace = models.TextField(null=True)
    
class ExcludeZone(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE)
    
    def __str__(self):
        return "(x, y, width, height) = (%d, %d, %d, %d)" % (self.x, self.y, self.width, self.height)
    
    def toRectangle(self):
        return Rectangle(self.x, self.y, self.width, self.height)
    
