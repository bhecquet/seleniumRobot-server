'''
Created on 8 mars 2017

@author: worm
'''

import collections
import os
import pickle
import threading

import cv2 

import numpy as np
from snapshotServer.exceptions.PictureComparatorError import PictureComparatorError
import logging
import time


Rectangle = collections.namedtuple("Rectangle", ['x', 'y', 'width', 'height'])
Pixel = collections.namedtuple("Pixel", ['x', 'y'])

logger = logging.getLogger(__name__)

class PictureComparator:
    
    def __init__(self):
        pass
    
    def compare(self, reference, image):
        """
        Compares an image to its reference
        @return: a rectangle of the matching zone in reference image or None if nothing is found
        """
        
        if not os.path.isfile(reference):
            raise PictureComparatorError("Reference file %s does not exist" % reference)
        if not os.path.isfile(image):
            raise PictureComparatorError("Image file %s does not exist" % image)
        
        referenceImg = cv2.imread(reference, 0)
        imageImg = cv2.imread(image, 0)
        referenceWidth, referenceHeight = referenceImg.shape[::-1]
        imageWidth, imageHeight = imageImg.shape[::-1]
        
        if referenceWidth < imageWidth or referenceHeight < imageHeight:
            raise PictureComparatorError("Reference picture must be greater than image to find")

        method = cv2.TM_CCOEFF_NORMED
    
        # Apply template Matching
        res = cv2.matchTemplate(referenceImg, imageImg, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

        if max_val > 0.95:
            return Rectangle(max_loc[0], max_loc[1], imageWidth, imageHeight)
        else:
            return None
        
    def getChangedPixels(self, reference, image):
        """
        @param reference: reference picture
        @param image: image to compare with
        @return: list of pixels which are different between reference and image
        """
        if not os.path.isfile(reference):
            raise PictureComparatorError("Reference file %s does not exist" % reference)
        if not os.path.isfile(image):
            raise PictureComparatorError("Image file %s does not exist" % image)
        
        referenceImg = cv2.imread(reference, 0)
        imageImg = cv2.imread(image, 0)
        
        diff = cv2.absdiff(referenceImg, imageImg)
        
        pixels = []
        
        for y, row in enumerate(diff):
            if sum(row) == 0:
                continue
            for x, value in enumerate(row):
                if value != 0:
                    pixels.append(Pixel(x, y))

        return pixels
    
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
    def addJobs(cls, refSnapshot, stepSnapshot):
        inst = cls.getInstance()
        DiffComputer._jobLock.acquire()
        inst.jobs.append((refSnapshot, stepSnapshot))
        DiffComputer._jobLock.release()
        
    @classmethod
    def computeNow(cls, refSnapshot, stepSnapshot):
        cls.getInstance()._computeDiff(refSnapshot, stepSnapshot)
    
    def __init__(self):
        self.jobs = []
        super(DiffComputer, self).__init__()
    
    def run(self):
        logger.info('starting compute thread')
        
        # be sure we can restart a new thread if something goes wrong
        try:
            while True:
                DiffComputer._jobLock.acquire()
                tmpJobs = self.jobs[:]
                self.jobs = []
                DiffComputer._jobLock.release()
                
                for refSnapshot, stepSnapshot in tmpJobs:
                    try:
                        self._computeDiff(refSnapshot, stepSnapshot)
                    except Exception as e:
                        logger.error('Error computing snapshot: %s', str(e))
                time.sleep(1)
        
        except Exception as e:
            logger.exception('Exception during computing: %s', str(e))
        
        DiffComputer._instance = None
          
          
    def _computeDiff(self, refSnapshot, stepSnapshot): 
        
        logger.info('computing') 
        try:
            pixelDiffs = PictureComparator().getChangedPixels(refSnapshot.image.path, stepSnapshot.image.path)
            binPixels = pickle.dumps(pixelDiffs, protocol=3)
            stepSnapshot.pixelsDiff = binPixels
            stepSnapshot.refSnapshot = refSnapshot
            stepSnapshot.save()
        except PictureComparatorError as e:
            pass
        logger.info('finished')
