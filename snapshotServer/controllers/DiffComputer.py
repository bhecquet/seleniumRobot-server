'''
Created on 15 mai 2017

@author: bhecquet
'''
import pickle
import threading
import time

from snapshotServer.controllers import Tools
from django.db.models import Q
from snapshotServer.controllers.PictureComparator import PictureComparator,\
    Pixel
from snapshotServer.exceptions.PictureComparatorError import PictureComparatorError
from snapshotServer.models import ExcludeZone
from PIL import Image, ImageDraw
import io
import logging
import cv2

logger = logging.getLogger(__name__)

class DiffComputer(threading.Thread):
    """
    Class for processing differences asynchronously
    """
    
    _instance = None
    _jobLock = threading.Lock()
    _instanceLock = threading.Lock()
    picture_comparator = PictureComparator()
    
    @classmethod
    def get_instance(cls):
        with cls._instanceLock:
            if not cls._instance:
                cls._instance = DiffComputer()
                cls._instance.start()
                
                if not cls._instance.running:
                    time.sleep(0.1)
                
            return cls._instance

    def add_jobs(self, ref_snapshot, step_snapshot, check_test_mode=True):
        """
        Add a job to handle
        @param ref_snapshot: reference snapshot
        @param step_snapshot: snapshot to compare with reference
        @param check_test_mode: default is True. If True and we are in unit tests, computation is not done through thread
        """
        # as we will (re)compute, consider that current diff are not valid anymore
        step_snapshot.computed = False
        step_snapshot.save()
        
        if Tools.isTestMode() and check_test_mode:
            self.compute_now(ref_snapshot, step_snapshot)
   
        else:
            with DiffComputer._jobLock:
                self.jobs.append((ref_snapshot, step_snapshot))

    def compute_now(self, ref_snapshot, step_snapshot):
        """
        Compute difference now
        @param ref_snapshot: the reference snapshot
        @param step_snapshot: the snapshot to compare to step_snapshot
        """
        self._compute_diff(ref_snapshot, step_snapshot)
        
    @classmethod
    def stopThread(cls):
        with cls._instanceLock:
            if cls._instance:
                cls._instance.running = False
                cls._instance.join()
            cls._instance = None
    
    def __init__(self):
        self.jobs = []
        self.running = False
        super(DiffComputer, self).__init__()
    
    def run(self):
        logger.info('starting compute thread')
        self.running = True
        
        # be sure we can restart a new thread if something goes wrong
        try:
            while self.running or self.jobs:
                with DiffComputer._jobLock:
                    tmp_jobs = self.jobs[:]
                    self.jobs = []

                for ref_snapshot, step_snapshot in tmp_jobs:
                    try:
                        self._compute_diff(ref_snapshot, step_snapshot)
                    except Exception as e:
                        logger.exception('Error computing snapshot: %s', str(e))
                time.sleep(0.5)
        
        except Exception as e:
            logger.exception('Exception during computing: %s', str(e))
        
        DiffComputer._instance = None

    def _compute_diff(self, ref_snapshot, step_snapshot): 
        """
        Compare all pixels from reference snapshto and step snapshot, and store difference to database
        """
        
        logger.info('computing') 
        start = time.perf_counter()
        try:
            if ref_snapshot and step_snapshot and ref_snapshot.image and step_snapshot.image:
                
                # get the list of exclude zones
                exclude_zones = [e.toRectangle() for e in ExcludeZone.objects.filter(Q(snapshot=ref_snapshot) | Q(snapshot=step_snapshot))]
                
                pixel_diffs, diff_percentage, diff_image = DiffComputer.picture_comparator.get_changed_pixels(ref_snapshot.image.path, step_snapshot.image.path, exclude_zones)
                
                # store diff picture mask into database instead of pixels, to reduce size of stored object
#                 step_snapshot.pixelsDiff = self.mark_diff(step_snapshot.image.width, step_snapshot.image.height, pixel_diffs)
                step_snapshot.pixelsDiff = self.mark_diff(diff_image)
                
                # too many pixel differences if we go over tolerance
                step_snapshot.tooManyDiffs = step_snapshot.diffTolerance < diff_percentage
            else:
                step_snapshot.pixelsDiff = None
                step_snapshot.tooManyDiffs = False
                
            step_snapshot.refSnapshot = ref_snapshot
            step_snapshot.computingError = ''
            
        except PictureComparatorError:
            pass
        except Exception as e:
            step_snapshot.computingError = str(e)
        finally:
            # issue #81: be sure step_snapshot is marked as computed so that it never remain in "computing" state
            if step_snapshot:
                step_snapshot.computed = True
                step_snapshot.save()
            logger.info('finished computing in %.2fs' % (time.perf_counter() - start))

    def mark_diff(self, diff_image):
        """
        Save 'difference' pixels to a picture
        """
        is_success, buffer = cv2.imencode(".png", diff_image)
        return io.BytesIO(buffer).getvalue()
                
                