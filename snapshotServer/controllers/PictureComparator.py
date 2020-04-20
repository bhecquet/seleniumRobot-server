'''
Created on 8 mars 2017

@author: worm
'''

import collections
import logging
import os
import numpy


import cv2 

from snapshotServer.exceptions.PictureComparatorError import PictureComparatorError
import math


Rectangle = collections.namedtuple("Rectangle", ['x', 'y', 'width', 'height'])
Pixel = collections.namedtuple("Pixel", ['x', 'y'])

logger = logging.getLogger(__name__)

class PictureComparator:
    
    MAX_DIFF_THRESHOLD = 0.1
    
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
        
    def getChangedPixels(self, reference, image, exclude_zones=[]):
        """
        @param reference: reference picture
        @param image: image to compare with
        @param exclude_zones: list of zones (Rectangle objects) which should not be marked as differences.
        @return: list of pixels which are different between reference and image
                a percentage of diff pixels
        """
        if not os.path.isfile(reference):
            raise PictureComparatorError("Reference file %s does not exist" % reference)
        if not os.path.isfile(image):
            raise PictureComparatorError("Image file %s does not exist" % image)
        
        excluded_pixels = self._buildListOfExcludedPixels(exclude_zones)
        
        reference_img = cv2.imread(reference, 0)
        image_img = cv2.imread(image, 0)
        
        reference_height = len(reference_img)
        reference_width = len(reference_img[0])
        image_height = len(image_img)
        image_width = len(image_img[0])
        
        min_height = min(reference_height, image_height)
        if min_height == 0:
            min_width = 0
        else:
            min_width = min(reference_width, image_width)
        
        diff = cv2.absdiff(reference_img[0:min_height, 0:min_width], image_img[0:min_height, 0:min_width])
        
        pixels = []
        
        # ignore excluded pixels
        for x, y in excluded_pixels:
            diff[y][x] = 0
        
        mat_diff = numpy.matrix(diff)
        diff_pixels = numpy.transpose(mat_diff.nonzero());
        
        for y, x in diff_pixels:
            pixels.append(Pixel(x, y))
            
        # step image is taller that reference image, add missing pixels from reference
        for y in range(max(0, image_height - reference_height)):
            for x in range(image_width):
                pixels.append(Pixel(x, y + reference_height))
        for x in range(max(0, image_width - reference_width)):
            for y in range(reference_height):
                pixels.append(Pixel(x + reference_width, y))
            
        return pixels, len(pixels) * 100.0 / (image_height * image_width)
    
    def _buildListOfExcludedPixels(self, excludeZones):
        """
        From the list of rectangles, build a list of pixels that these rectangles cover
        """
        
        pixels = []
        for x, y, width, height in excludeZones:
            for row in range(height):
                for col in range(width):
                    pixels.append(Pixel(col + x, row + y))
                    
        return pixels
