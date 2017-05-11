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


Rectangle = collections.namedtuple("Rectangle", ['x', 'y', 'width', 'height'])
Pixel = collections.namedtuple("Pixel", ['x', 'y'])

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
    
    def __init__(self, refSnapshot, stepSnapshot):
        self.refSnapshot = refSnapshot
        self.stepSnapshot = stepSnapshot
        super(DiffComputer, self).__init__()
    
    def run(self):
        print('starting')
        pixelDiffs = PictureComparator().getChangedPixels(self.refSnapshot.image.path, self.stepSnapshot.image.path)
        binPixels = pickle.dumps(pixelDiffs, protocol=3)
        self.stepSnapshot.pixelsDiff = binPixels
        self.stepSnapshot.refSnapshot = self.refSnapshot
        self.stepSnapshot.save()
        print('finished')
