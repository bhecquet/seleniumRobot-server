'''
Created on 8 mars 2017

@author: worm
'''
import unittest

from snapshotServer.utils.utils import getTestDirectory
from snapshotServer.controllers.PictureComparator import PictureComparator,\
    Pixel
from snapshotServer.exceptions.PictureComparatorError import PictureComparatorError


class Test(unittest.TestCase):


    def setUp(self):
        unittest.TestCase.setUp(self)
        self.dataDir = getTestDirectory();

    def test_compareSampleImage(self):
        comparator = PictureComparator();
        rect = comparator.compare(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'template_Ibis_Mulhouse.png')
        self.assertNotEqual(rect, None, "A matching should have been found")
        self.assertEqual(rect.x, 467)
        self.assertEqual(rect.y, 244)
 
    def test_compareSameImage(self):
        comparator = PictureComparator();
        rect = comparator.compare(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'Ibis_Mulhouse.png')
        self.assertNotEqual(rect, None, "A matching should have been found")
        self.assertEqual(rect.x, 0)
        self.assertEqual(rect.y, 0)
         
    def test_compareImageNotFound(self):
        comparator = PictureComparator();
        rect = comparator.compare(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'engie.png')
        self.assertEqual(rect, None, "A matching should not have been found")
 
    def test_compareWithGreaterImage(self):
        comparator = PictureComparator();
        self.assertRaisesRegex(PictureComparatorError, 
                               "must be greater", 
                               comparator.compare, 
                               self.dataDir + 'template_Ibis_Mulhouse.png', 
                               self.dataDir + 'Ibis_Mulhouse.png')
 
    def test_compareWithUnavailableReference(self):
        comparator = PictureComparator();
        self.assertRaisesRegex(PictureComparatorError, 
                               "^Reference file", 
                               comparator.compare, 
                               self.dataDir + 'template_Ibis_Mulhou.png', 
                               self.dataDir + 'Ibis_Mulhouse.png')
 
    def test_compareWithUnavailableImage(self):
        comparator = PictureComparator();
        self.assertRaisesRegex(PictureComparatorError, 
                               "^Image file", 
                               comparator.compare, 
                               self.dataDir + 'template_Ibis_Mulhouse.png', 
                               self.dataDir + 'Ibis_Mulhou.png')
         
    def test_noDiff(self):
        comparator = PictureComparator();
        diffPixels = comparator.getChangedPixels(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'Ibis_Mulhouse.png')
        self.assertEqual(0, len(diffPixels), "No difference pixels should be found")
         
        
    def test_realDiff(self):
        comparator = PictureComparator();
        diffPixels = comparator.getChangedPixels(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'Ibis_Mulhouse_diff.png')
        self.assertEqual(3, len(diffPixels), "3 pixels should be found")
        self.assertEqual(Pixel(554, 256), diffPixels[0], "detected position is wrong")
         
