
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
from commonsServer.models import TruncatingCharField
from django.utils.safestring import mark_safe

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
    
class TestStepsThroughTestCaseInSession(models.Model):
    testcaseinsession = models.ForeignKey('TestCaseInSession', on_delete=models.CASCADE)
    teststep = models.ForeignKey('TestStep', on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', ]
    
class TestCaseInSession(models.Model):
    """
    The test case in a test session
    It is the test case, executed
    It allows to assiociate a test case with tests steps, as list of test step may change from time to time for the same test case
    """
    __test__= False  # avoid detecting it as a test class
    testCase = models.ForeignKey(TestCase, related_name="testCaseInSession", on_delete=models.CASCADE)
    session = models.ForeignKey('TestSession', on_delete=models.CASCADE)
    testSteps = models.ManyToManyField("TestStep", related_name="testCase", blank=True, through=TestStepsThroughTestCaseInSession)
    # testSteps = models.ManyToManyField("TestStep", related_name="testCase", blank=True)
    stacktrace = models.TextField(null=True)
    name = models.CharField(max_length=100, null=True)
    
    def isOkWithSnapshots(self):
        """
        Returns True if test is OK for this test case, executed in session. Look at each step. None of the snapshot should
        show a diff
        """
        
        snapshots = Snapshot.objects.filter(stepResult__testCase=self)
        result = True 
        computing_errors = 0
        
        for snapshot in snapshots:
            if snapshot.computingError:
                computing_errors += 1
                continue
            if snapshot.pixelsDiff is None:
                continue
            
            # pickling is only used for tests
            try:
                pixels = pickle.loads(snapshot.pixelsDiff)
                result = result and not bool(pixels)
            except:
                result = result and not snapshot.tooManyDiffs
                
        # result is undefined 
        # - if none of the snapshots has been computed
        # - at least one computation failed and remaining result is OK.
        if len(snapshots) == computing_errors or (computing_errors > 0 and result):
            return None
            
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
    
    def computingError(self):
        """
        Returns a list of computing errors
        """
        all_errors = []
        snapshots = Snapshot.objects.filter(stepResult__testCase=self)
        for snapshot in snapshots:
            if snapshot.computingError:
                all_errors.append("%s: %s" % (snapshot.name, snapshot.computingError))
            
        return all_errors
    
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
        if self.name:
            return "%s - %s" % (self.name, self.session.version.name)
        else:
            return "%s - %s" % (self.testCase.name, self.session.version.name)
    
class TestStep(models.Model):
    """
    A test step, not particularly associated to any test case
    association is done through TestCaseInSession
    """
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
    """
    A test session represents a set of tests that have been run in the same launch
    It may contain 1 to N tests
    """
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
        # a sub query is used because we need 'inner join' when filtering and django creates 'left outer join' which gets more than necessary
        for session in TestSession.objects.filter(ttl__gt=datetime.timedelta(days=0), 
                                                  date__lt=timezone.now() - F('ttl'))\
                                            .exclude(id__in=[s.stepResult.testCase.session.id for s in Snapshot.objects.filter(refSnapshot=None).select_related('stepResult__testCase__session')]).distinct():
            logging.info("deleting session {}-{} of the {}".format(session.id, str(session), session.date))
            session.delete()
     
def upload_path(instance, filename):
    return 'documents/references/%s/%s/%s' % (instance.testCase.application, instance.testCase.name, filename)
        
class StepReference(models.Model):
    """
    Class for storing reference picture and data associated to a successful step
    """
    
    # TODO: remove field stepResult as it won't be used anymore
    stepResult = models.ForeignKey('StepResult', related_name='step_reference', on_delete=models.CASCADE, null=True, blank=True)
    testCase = models.ForeignKey(TestCase, on_delete=models.CASCADE, null=True, blank=True)
    environment = models.ForeignKey(TestEnvironment, on_delete=models.CASCADE, null=True, blank=True)
    testStep = models.ForeignKey(TestStep, on_delete=models.CASCADE, null=True, blank=True)
    version = models.ForeignKey(Version, on_delete=models.CASCADE, null=True, blank=True)
    
    image = models.ImageField(upload_to=upload_path, max_length=200)
    
    field_detection_date = models.DateTimeField(blank=True, null=True) # empty if detection has not been performed
    field_detection_version = models.CharField(max_length=10, default="") # version of the model used to detect fields
    field_detection_data = models.FileField(upload_to=upload_path, max_length=200, blank=True, null=True)
    
    
    def image_tag(self):
        if self.image:
            return mark_safe('<img src="%s" style="width: 400px;" />' % self.image.url)
        else:
            return 'No Image Found'
    image_tag.short_description = 'Image'
    
    def step_name(self):
        return self.stepResult.step.name
    
    # we could also add: signature, text, fields, for comparison
    
class Snapshot(models.Model):
    """
    Snapshot class to store image with comparison data, for UI regression
    """

    stepResult = models.ForeignKey('StepResult', related_name='snapshots', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='documents/%Y/%m/%d')
    refSnapshot = models.ForeignKey('self', default=None, null=True, on_delete=models.DO_NOTHING)
    pixelsDiff = models.BinaryField(null=True)
    tooManyDiffs = models.BooleanField(default=False)
    name = models.CharField(max_length=150, default="") # name of the snapshot
    compareOption = models.CharField(max_length=100, default="true") # options for comparison
    computed = models.BooleanField(default=False)
    diffTolerance = models.FloatField(default=0.0) # pixel tolerance when comparing pictures. 0.0 means all pixels must be identical, 10.0 means 10% of the pixels may be different 
    computingError = TruncatingCharField(max_length=250, default="")
  
    def __str__(self):
        return "%s - %s - %s - %d" % (self.stepResult.testCase.testCase.name, self.stepResult.step.name, self.stepResult.testCase.session.sessionId, self.id) 
    
    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(diffTolerance__gte=0) & Q(diffTolerance__lte=100) , name='percentage_diff_tolerance'),
        ]
    
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
            
            diff_computer = DiffComputer.get_instance()
            
            # recompute diff pixels
            diff_computer.compute_now(snapshot.refSnapshot, snapshot)
            
            # recompute all following snapshot as they will depend on a previous ref
            for snap in snapshot.snapshotsUntilNextRef(snapshot):
                diff_computer.add_jobs(snapshot.refSnapshot, snap)
            
        # no reference snapshot found, only remove information about reference which makes this snapshot a reference    
        else:
            snapshot.refSnapshot = None
            snapshot.save()
            
        
class StepResult(models.Model):
    """
    The result (OK or KO) for a test step in a test case
    """
    
    def __str__(self):
        if self.id:
            return "result %d " % self.id
        else:
            return "result tmp"
    
    step = models.ForeignKey(TestStep, related_name='stepresult', on_delete=models.CASCADE)
    testCase = models.ForeignKey(TestCaseInSession, related_name='stepresult', on_delete=models.CASCADE)
    result = models.BooleanField(null=False)
    duration = models.FloatField(default=0.0)
    stacktrace = models.TextField(null=True)
    
class ExcludeZone(models.Model):
    """
    A zone in image that will be ignored when comparing snapshots
    """
    x = models.IntegerField()
    y = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE)
    
    def __str__(self):
        return "(x, y, width, height) = (%d, %d, %d, %d)" % (self.x, self.y, self.width, self.height)
    
    def toRectangle(self):
        return Rectangle(self.x, self.y, self.width, self.height)
    
    def copy_to_snapshot(self, snapshot):
        """
        Copy this exclude zone to the snapshot provided
        """
        ExcludeZone(x=self.x, y=self.y, width=self.width, height=self.height, snapshot=snapshot).save()
    
