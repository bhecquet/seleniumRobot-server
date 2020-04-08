
from django.db import models
from django.db.models import F, Q

from snapshotServer.controllers.PictureComparator import Rectangle
import pickle
import commonsServer.models
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_delete, pre_delete
from django.utils import timezone
import datetime
from django.db.models.aggregates import Count
import logging

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
        Returns True if test is OK for this test case, executed in session. Look at each step. None of the snapshot should
        show a diff
        """
        
        snapshots = Snapshot.objects.filter(stepResult__testCase=self)
        result = True 
        for snapshot in snapshots:
            if snapshot.pixelsDiff is None:
                continue
            
            # TODO: pickle should be removed as not pickling should exist in database anymore
            try:
                pixels = pickle.loads(snapshot.pixelsDiff)
                result = result and not bool(pixels)
            except:
                result = result and not snapshot.tooManyDiffs
            
        return result
    
    def computed(self):
        """
        Returns True if all snapshots have been computed
        """
        snapshots = Snapshot.objects.filter(stepResult__testCase=self)
        for snapshot in snapshots:
            if not snapshot.computed:
                return False
            
        return True
    
    def isOkWithResult(self):
        """
        Returns True if test is OK for the session in parameter. Look at each step. None of the steps should be KO (look at StepResult object)
        """
        
        step_results = StepResult.objects.filter(testCase=self)

        for step_result in step_results:
            if not step_result.result:
                return False
            
        return True
    
    def __str__(self):
        return "%s - %s" % (self.testCase.name, self.session.version.name)
    
class TestStep(models.Model):
    __test__= False  # avoid detecting it as a test class
    name = models.CharField(max_length=100) 
    
    def __str__(self):
        return self.name 
    
    
    def isOkWithSnapshots(self, test_case):
        """
        Returns True if step is OK for the session in parameter. Look at each step. 
        If None of the snapshot shows diff, returns True
        @param test_case: the test case this step belongs
        """
        
        snapshots = Snapshot.objects.filter(stepResult__testCase=test_case, stepResult__step=self)
        step_status = StepResult.objects.filter(step=self, testCase=test_case).last()
        
        if step_status == None:
            result = True
        else:
            result = step_status.result
        
        for snapshot in snapshots:
            if snapshot.pixelsDiff is None:
                continue
            
            # TODO: pickle should be removed as not pickling should exist in database anymore
            try:
                pixels = pickle.loads(snapshot.pixelsDiff)
                result = result and not bool(pixels)
            except:
                result = result and not snapshot.tooManyDiffs
           
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
    ttl = models.DurationField(default=datetime.timedelta(days=30)) # time to live of the session, in days. After this delay, session may be deleted
    
    def __str__(self):
        if self.name:
            return self.name
        else:
            return "Session %s with %s" % (self.sessionId, self.browser)
        

    def save(self, *args, **kwds):
        """
        While saving a new session, delete all too old sessions
        """
        super(TestSession, self).save(*args, **kwds)
        
        # search all sessions whose date is older than defined 'ttl' (ttl > 0)
        # do not select sessions whose snapshot number is > 0 and reference snapshot number is > 0
        for session in TestSession.objects.annotate(snapshot_number=Count('testcaseinsession__stepresult__snapshots')) \
                                            .filter(ttl__gt=datetime.timedelta(days=0), 
                                                  date__lt=timezone.now() - F('ttl')) \
                                            .exclude(~Q(snapshot_number=0) & Q(testcaseinsession__stepresult__snapshots__refSnapshot=None)):
            logging.info("deleting session {}-{} of the {}".format(session.id, str(session), session.date))
            session.delete()
        
    
# TODO delete file when snapshot is removed from database
class Snapshot(models.Model):

    stepResult = models.ForeignKey('StepResult', related_name='snapshots', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='documents/')
    refSnapshot = models.ForeignKey('self', default=None, null=True, on_delete=models.DO_NOTHING)
    pixelsDiff = models.BinaryField(null=True)
    tooManyDiffs = models.BooleanField(default=False)
    name = models.CharField(max_length=100, default="") # name of the snapshot
    compareOption = models.CharField(max_length=100, default="true") # options for comparison
    computed = models.BooleanField(default=False)
  
    def __str__(self):
        return "%s - %s - %s - %d" % (self.stepResult.testCase.testCase.name, self.stepResult.step.name, self.stepResult.testCase.session.sessionId, self.id) 
    
    def snapshotsUntilNextRef(self, ref_snapshot):
        """
        get all snapshots, sharing the same reference snapshot, until the next reference for the same testCase / testStep
        """
        
        # get list of all snapshots following ourself, sharing 'refSnapshot'
        next_snapshots = Snapshot.objects.filter(stepResult__step=self.stepResult.step, 
                                            stepResult__testCase__testCase__name=self.stepResult.testCase.testCase.name, 
                                            stepResult__testCase__session__version__in=self.stepResult.testCase.session.version.nextVersions(),
                                            refSnapshot=ref_snapshot,
                                            id__gt=self.id) \
                                        .order_by('id')
        
        snapshots = []
        
        for snap in next_snapshots:
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
                                               stepResult__testCase__session__environment=test_case.session.environment, 
                                               stepResult__testCase__session__browser=test_case.session.browser, 
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
    
