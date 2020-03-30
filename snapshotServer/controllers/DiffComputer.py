'''
Created on 15 mai 2017

@author: bhecquet
'''
from asyncio.log import logger
import pickle
import threading
import time

from snapshotServer.controllers import Tools
from snapshotServer.controllers.PictureComparator import PictureComparator,\
    Pixel
from snapshotServer.exceptions.PictureComparatorError import PictureComparatorError
from snapshotServer.models import ExcludeZone
from builtins import staticmethod
from PIL import Image, ImageDraw
import io


class DiffComputer(threading.Thread):
    """
    Class for processing differences asynchronously
    """
    
    _instance = None
    _jobLock = threading.Lock()
    
    @classmethod
    def getInstance(cls):
        if not cls._instance:
            cls._instance = DiffComputer()
            cls._instance.start()
        return cls._instance
    
    @classmethod
    def addJobs(cls, refSnapshot, stepSnapshot, checkTestMode=True):
        """
        Add a job to handle
        @param refSnapshot: reference snapshot
        @param stepSnapshot: snapshot to compare with reference
        @param checkTestMode: default is True. If True and we are in unit tests, computation is not done through thread
        """
        if Tools.isTestMode() and checkTestMode:
            cls.computeNow(refSnapshot, stepSnapshot)
            return 
        else:
            inst = cls.getInstance()
            DiffComputer._jobLock.acquire()
            inst.jobs.append((refSnapshot, stepSnapshot))
            DiffComputer._jobLock.release()
        
    @classmethod
    def computeNow(cls, ref_snapshot, step_snapshot):
        DiffComputer._computeDiff(ref_snapshot, step_snapshot)
        
    @classmethod
    def stopThread(cls):
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
                DiffComputer._jobLock.acquire()
                tmpJobs = self.jobs[:]
                self.jobs = []
                DiffComputer._jobLock.release()

                for refSnapshot, stepSnapshot in tmpJobs:
                    try:
                        DiffComputer._computeDiff(refSnapshot, stepSnapshot)
                    except Exception as e:
                        logger.error('Error computing snapshot: %s', str(e))
                time.sleep(0.5)
        
        except Exception as e:
            logger.exception('Exception during computing: %s', str(e))
        
        DiffComputer._instance = None
          
    @staticmethod
    def _computeDiff(ref_snapshot, step_snapshot): 
        
        logger.info('computing') 
        try:
            if ref_snapshot and step_snapshot and ref_snapshot.image and step_snapshot.image:
                
                # get the list of exclude zones
                exclude_zones = [e.toRectangle() for e in ExcludeZone.objects.filter(snapshot=ref_snapshot)]
                
                pixel_diffs, too_many_diffs = PictureComparator().getChangedPixels(ref_snapshot.image.path, step_snapshot.image.path, exclude_zones)
                
                # store diff picture mask into database instead of pixels, to reduce size of stored object
                step_snapshot.pixelsDiff = DiffComputer.markDiff(step_snapshot.image.width, step_snapshot.image.height, pixel_diffs)
                step_snapshot.tooManyDiffs = too_many_diffs
            else:
                step_snapshot.pixelsDiff = None
                step_snapshot.tooManyDiffs = False
                
            step_snapshot.refSnapshot = ref_snapshot
            step_snapshot.save()
        except PictureComparatorError as e:
            pass
        logger.info('finished')

    @staticmethod
    def markDiff(width, height, diff_pixel):
        

        img = Image.new('RGBA', (width, height), (255, 0, 0, 0))
        
        draw = ImageDraw.Draw(img)
        draw.point(diff_pixel, 'red')

        with io.BytesIO() as output:
            img.save(output, format="PNG")
            return output.getvalue()     
                
                