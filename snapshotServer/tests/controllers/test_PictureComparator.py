'''
Created on 8 mars 2017

@author: worm
'''
import unittest

from snapshotServer.utils.utils import getTestDirectory
from snapshotServer.controllers.PictureComparator import PictureComparator,\
    Pixel, Rectangle
from snapshotServer.exceptions.PictureComparatorError import PictureComparatorError


class Test(unittest.TestCase):


    def setUp(self):
        unittest.TestCase.setUp(self)
        self.dataDir = getTestDirectory();

    def test_compare_sample_image(self):
        comparator = PictureComparator();
        rect = comparator.compare(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'template_Ibis_Mulhouse.png')
        self.assertNotEqual(rect, None, "A matching should have been found")
        self.assertEqual(rect.x, 467)
        self.assertEqual(rect.y, 244)
   
    def test_compare_same_image(self):
        comparator = PictureComparator();
        rect = comparator.compare(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'Ibis_Mulhouse.png')
        self.assertNotEqual(rect, None, "A matching should have been found")
        self.assertEqual(rect.x, 0)
        self.assertEqual(rect.y, 0)
           
    def test_compare_image_not_found(self):
        comparator = PictureComparator();
        rect = comparator.compare(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'engie.png')
        self.assertEqual(rect, None, "A matching should not have been found")
   
    def test_compare_with_greater_image(self):
        comparator = PictureComparator();
        self.assertRaisesRegex(PictureComparatorError, 
                               "must be greater", 
                               comparator.compare, 
                               self.dataDir + 'template_Ibis_Mulhouse.png', 
                               self.dataDir + 'Ibis_Mulhouse.png')
   
    def test_compare_with_unavailable_reference(self):
        comparator = PictureComparator();
        self.assertRaisesRegex(PictureComparatorError, 
                               "^Reference file", 
                               comparator.compare, 
                               self.dataDir + 'template_Ibis_Mulhou.png', 
                               self.dataDir + 'Ibis_Mulhouse.png')
   
    def test_compare_with_unavailable_image(self):
        comparator = PictureComparator();
        self.assertRaisesRegex(PictureComparatorError, 
                               "^Image file", 
                               comparator.compare, 
                               self.dataDir + 'template_Ibis_Mulhouse.png', 
                               self.dataDir + 'Ibis_Mulhou.png')
           
    def test_no_diff(self):
        comparator = PictureComparator();
        diff_pixels, too_many_diffs = comparator.getChangedPixels(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'Ibis_Mulhouse.png')
        self.assertEqual(0, len(diff_pixels), "No difference pixels should be found")
        self.assertFalse(too_many_diffs)
           
          
    def test_real_diff(self):
        comparator = PictureComparator();
        diff_pixels, too_many_diffs = comparator.getChangedPixels(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'Ibis_Mulhouse_diff.png')
        self.assertEqual(3, len(diff_pixels), "3 pixels should be found")
        self.assertEqual(Pixel(554, 256), diff_pixels[0], "detected position is wrong")
        self.assertTrue(too_many_diffs)
         
    def test_real_too_many_diff(self):
        comparator = PictureComparator();
        diff_pixels, too_many_diffs = comparator.getChangedPixels(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'Ibis_Mulhouse_tooManyDiffs.png')
        self.assertEqual(817176, len(diff_pixels), "207360 pixels should be found")
        self.assertEqual(diff_pixels[0], Pixel(0, 132), "First diff pixel should be (0, 132)")
        self.assertTrue(too_many_diffs)
          
         
    def test_real_diff_with_exclusion(self):
        """
        Test that is some exclude zones are defined, and covers the diff pixels, these pixels are not
        marked as diff
        """
        comparator = PictureComparator();
        diffPixels, tooManyDiffs = comparator.getChangedPixels(self.dataDir + 'Ibis_Mulhouse.png', 
                                                 self.dataDir + 'Ibis_Mulhouse_diff.png',
                                                 [Rectangle(550, 255, 5, 3)])
        self.assertEqual(2, len(diffPixels), "2 pixels should be found")
        self.assertEqual(Pixel(555, 256), diffPixels[0], "detected position is wrong")
         
        # [Pixel(x=554, y=256), Pixel(x=555, y=256), Pixel(x=556, y=256)]
        
    
    def test_compute_diff_with_cropping_on_reference_image(self):
        """
        Check no error is raised when comparing 2 images with different sizes
        Here reference image is smaller than step, so diff will be shown on missing pixels
        """
        
        comparator = PictureComparator();
        pixels_diff_map, too_many_diffs = comparator.getChangedPixels(self.dataDir + 'test_Image1Crop.png', 
                                                 self.dataDir + 'test_Image1.png',
                                                 [])
        
        # cropping on 58 lines. Check we have all points
        self.assertEqual(pixels_diff_map[0], Pixel(0, 701))
        self.assertEqual(pixels_diff_map[1174], Pixel(0, 702))
        self.assertEqual(pixels_diff_map[1174 * 58 - 1], Pixel(1173, 758))
        
        # cropping on 4 columns
        self.assertEqual(pixels_diff_map[1174 * 58], Pixel(1170, 0)) 
        self.assertEqual(pixels_diff_map[-1], Pixel(1173, 700)) 
        self.assertEqual(len(pixels_diff_map), 70896)
        
         
    def test_compute_diff_with_cropping_on_step_image(self):
        """
        Check no error is raised when comparing 2 images with different sizes
        Here step image is smaller than reference, so no diff will be shown
        """
        comparator = PictureComparator();
        pixels_diff_map, too_many_diffs = comparator.getChangedPixels(self.dataDir + 'test_Image1.png', 
                                                 self.dataDir + 'test_Image1Crop.png',
                                                 [])
        
        self.assertEqual(len(pixels_diff_map), 0, "no diff should be found")    
        
