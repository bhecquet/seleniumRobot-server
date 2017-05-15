'''
Created on 15 mai 2017

@author: bhecquet
'''
from asyncio.log import logger
import pickle
import threading
import time

from snapshotServer.controllers import Tools
from snapshotServer.controllers.PictureComparator import PictureComparator
from snapshotServer.exceptions.PictureComparatorError import PictureComparatorError


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
    def computeNow(cls, refSnapshot, stepSnapshot):
        DiffComputer._computeDiff(refSnapshot, stepSnapshot)
        
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
    def _computeDiff(refSnapshot, stepSnapshot): 
        
        logger.info('computing') 
        try:
            if refSnapshot and stepSnapshot and refSnapshot.image and stepSnapshot.image:
                pixelDiffs = PictureComparator().getChangedPixels(refSnapshot.image.path, stepSnapshot.image.path)
                binPixels = pickle.dumps(pixelDiffs, protocol=3)
                stepSnapshot.pixelsDiff = binPixels
            else:
                stepSnapshot.pixelsDiff = None
                
            stepSnapshot.refSnapshot = refSnapshot
            stepSnapshot.save()
        except PictureComparatorError as e:
            pass
        logger.info('finished')
