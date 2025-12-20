'''
Created on 8 mars 2017

@author: worm
'''

from snapshotServer.utils.utils import getTestDirectory
from snapshotServer.controllers.picture_comparator import Pixel, Rectangle
from snapshotServer.controllers.picture_comparator import PictureComparator
from snapshotServer.exceptions.picture_comparator_error import PictureComparatorError
import numpy
from numpy import uint8
from snapshotServer.tests import SnapshotTestCase
from django.test import override_settings

@override_settings(IMAGE_COMPARISON_THRESHOLD=0)
class TestPictureComparator(SnapshotTestCase):


    def setUp(self):
        super().setUp()
        self.dataDir = getTestDirectory();

    
    def convert_points_to_pixels(self, diff_pixels):
        """
        Convert a numpy array (typically, the array of difference pixels) to a list of Pixel objects
        """
        pixels = []
        for y, x in diff_pixels:
            pixels.append((x, y))
            
        return pixels

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
        diff_pixels, diff_percentage, diff_image = comparator.get_changed_pixels(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'Ibis_Mulhouse.png')
        self.assertEqual(0, len(diff_pixels), "No difference pixels should be found")
        self.assertEqual(int(diff_percentage), 0)
           
          
    def test_real_diff(self):
        comparator = PictureComparator()
        diff_pixels, diff_percentage, diff_image = comparator.get_changed_pixels(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'Ibis_Mulhouse_diff.png')
        
        diff_pixels = self.convert_points_to_pixels(diff_pixels)
        
        self.assertEqual(3, len(diff_pixels), "3 pixels should be found")
        self.assertEqual(Pixel(554, 256), diff_pixels[0], "detected position is wrong")
        self.assertTrue(diff_percentage > 0)

    def test_real_diff_under_threshold(self):
        """
        Picture test_threshold1 has 3 red pixels which should be detected as difference and an almost white pixel that
        should not be detected as under tolerance
        """

        with self.settings(IMAGE_COMPARISON_THRESHOLD=9):
            comparator = PictureComparator()
            diff_pixels, diff_percentage, diff_image = comparator.get_changed_pixels(self.dataDir + 'test_threshold_source.png', self.dataDir + 'test_threshold1.png')

            diff_pixels = self.convert_points_to_pixels(diff_pixels)

            self.assertEqual(3, len(diff_pixels), "3 pixels should be found")
            self.assertEqual(Pixel(0, 0), diff_pixels[0], "detected position is wrong")
            self.assertEqual(Pixel(117, 0), diff_pixels[1], "detected position is wrong")
            self.assertEqual(Pixel(0, 64), diff_pixels[2], "detected position is wrong")
            self.assertTrue(diff_percentage > 0)

    def test_real_diff_above_threshold(self):
        """
        Picture test_threshold1 has 3 red pixels which should be detected as difference and an almost white pixel that
        should not be detected as under tolerance
        """
        with self.settings(IMAGE_COMPARISON_THRESHOLD=8):
            comparator = PictureComparator()
            diff_pixels, diff_percentage, diff_image = comparator.get_changed_pixels(self.dataDir + 'test_threshold_source.png', self.dataDir + 'test_threshold1.png')

            diff_pixels = self.convert_points_to_pixels(diff_pixels)

            self.assertEqual(4, len(diff_pixels), "4 pixels should be found")
            self.assertEqual(Pixel(0, 0), diff_pixels[0], "detected position is wrong")
            self.assertEqual(Pixel(117, 0), diff_pixels[1], "detected position is wrong")
            self.assertEqual(Pixel(0, 64), diff_pixels[2], "detected position is wrong")
            self.assertEqual(Pixel(117, 64), diff_pixels[3], "detected position is wrong")
            self.assertTrue(diff_percentage > 0)
         
    def test_real_too_many_diff(self):
        comparator = PictureComparator()
        diff_pixels, diff_percentage, diff_image = comparator.get_changed_pixels(self.dataDir + 'Ibis_Mulhouse.png', self.dataDir + 'Ibis_Mulhouse_tooManyDiffs.png')
        
        diff_pixels = self.convert_points_to_pixels(diff_pixels)
        self.assertEqual(817176, len(diff_pixels), "207360 pixels should be found")
        self.assertEqual(diff_pixels[0], Pixel(0, 132), "First diff pixel should be (0, 132)")
        self.assertTrue(int(diff_percentage), 39)
          
         
    def test_real_diff_with_exclusion(self):
        """
        Test that if some exclude zones are defined, and covers the diff pixels, these pixels are not
        marked as diff
        """
        comparator = PictureComparator();
        diff_pixels, diff_percentage, diff_image = comparator.get_changed_pixels(self.dataDir + 'Ibis_Mulhouse.png', 
                                                 self.dataDir + 'Ibis_Mulhouse_diff.png',
                                                 [Rectangle(550, 255, 5, 3)])
        diff_pixels = self.convert_points_to_pixels(diff_pixels)
        self.assertEqual(2, len(diff_pixels), "2 pixels should be found")
        self.assertEqual(Pixel(555, 256), diff_pixels[0], "detected position is wrong")
         
        # [Pixel(x=554, y=256), Pixel(x=555, y=256), Pixel(x=556, y=256)]
        
    
    def test_compute_diff_with_cropping_on_reference_image(self):
        """
        Check no error is raised when comparing 2 images with different sizes
        Here reference image is smaller than step, so diff will be shown on missing pixels
        """
        
        comparator = PictureComparator();
        pixels_diff_map, diff_percentage, diff_image = comparator.get_changed_pixels(self.dataDir + 'test_Image1Crop.png', 
                                                 self.dataDir + 'test_Image1.png',
                                                 [])
        pixels_diff_map = self.convert_points_to_pixels(pixels_diff_map)
        
        # cropping on 58 lines. Check we have all points
        self.assertFalse(Pixel(0, 700) in pixels_diff_map) # last line where comparison is possible => same line
        self.assertTrue(Pixel(0, 701) in pixels_diff_map)  # first line where step image is taller that reference on
        self.assertTrue(Pixel(0, 702) in pixels_diff_map)
        self.assertTrue(Pixel(1173, 758) in pixels_diff_map) # top right corner
        
        # cropping on 4 columns
        self.assertTrue(Pixel(1170, 0) in pixels_diff_map)
        self.assertTrue(Pixel(1173, 700) in pixels_diff_map)
        self.assertEqual(len(pixels_diff_map), 70896)
        
    def test_compute_diff_with_cropping_on_reference_image_with_exclusions_outside_reference_height(self):
        """
        issue #81: check that if exclusion zones are partially ouside of reference image, computing is still done
        test_Image1Mod2.png is 1174x759
        test_Image1Crop.png is 1170x701
        
        We put an exclusion zone at Point(0x700) of 2 pixel height, so that it goes outside of test_Image1Crop.png range of 1 pixel
        """
        
        comparator = PictureComparator();
        pixels_diff_map, diff_percentage, diff_image = comparator.get_changed_pixels(self.dataDir + 'test_Image1Crop.png', 
                                                 self.dataDir + 'test_Image1Mod2.png',
                                                 [Rectangle(0, 700, 1, 2)])
        pixels_diff_map = self.convert_points_to_pixels(pixels_diff_map)
        
        self.assertEqual(pixels_diff_map[0], Pixel(0, 0))
        pixels_diff_map[700]
        self.assertFalse(Pixel(0, 700) in pixels_diff_map) # exclusion zone inside reference area is excluded from comparison 
        self.assertFalse(Pixel(0, 701) in pixels_diff_map) # exclusion zone outside reference area is excluded from comparison 
        self.assertTrue(Pixel(1, 701) in pixels_diff_map)  # pixel outside of reference area and outside of exclusion zone is marked as a diff
        self.assertTrue(Pixel(0, 702) in pixels_diff_map)  # pixel outside of reference area and outside of exclusion zone is marked as a diff
        
    def test_compute_diff_with_cropping_on_reference_image_with_exclusions_outside_reference_width(self):
        """
        issue #81: check that if exclusion zones are partially ouside of reference image (in width), computing is still done
        test_Image1Mod2.png is 1174x759
        test_Image1Crop.png is 1170x701
        
        We put an exclusion zone at Point(1169x700) of 2 pixel width, so that it goes outside of test_Image1Crop.png range of 1 pixel
        
        This checks that an exclusion zone can be set outside of reference image
        """
        
        comparator = PictureComparator();
        pixels_diff_map, diff_percentage, diff_image = comparator.get_changed_pixels(self.dataDir + 'test_Image1Crop.png', 
                                                 self.dataDir + 'test_Image1Mod2.png',
                                                [Rectangle(1169, 700, 2, 1)])
        pixels_diff_map = self.convert_points_to_pixels(pixels_diff_map)
        
        self.assertEqual(pixels_diff_map[0], Pixel(0, 0))
        self.assertFalse(Pixel(1169, 700) in pixels_diff_map) # exclusion zone inside reference area is excluded from comparison 
        self.assertFalse(Pixel(1170, 700) in pixels_diff_map) # exclusion zone outside reference area is excluded from comparison 
        self.assertTrue(Pixel(1171, 700) in pixels_diff_map)  # pixel outside of reference area and outside of exclusion zone is marked as a diff
        self.assertTrue(Pixel(1170, 699) in pixels_diff_map)  # pixel outside of reference area and outside of exclusion zone is marked as a diff

    def test_compute_diff_with_exclusions_outside_step_image(self):
        """
        issue #81: check that if exclusion zones are ouside of step image, computing is still done
        test_Image1Mod2.png is 1174x759
        test_Image1Crop.png is 1170x701
        
        We put an exclusion zone at Point(0x758) of 2 pixel height, so that it goes outside of test_Image1Mod2.png range of 1 pixel
        """
        
        comparator = PictureComparator();
        pixels_diff_map, diff_percentage, diff_image = comparator.get_changed_pixels(self.dataDir + 'test_Image1Crop.png', 
                                                 self.dataDir + 'test_Image1Mod2.png',
                                                 [Rectangle(0, 758, 1, 2)])
        pixels_diff_map = self.convert_points_to_pixels(pixels_diff_map)
        
        self.assertEqual(pixels_diff_map[0], Pixel(0, 0))
        self.assertFalse(Pixel(0, 758) in pixels_diff_map) # exclusion zone outside reference area is excluded from comparison 
        self.assertTrue(Pixel(0, 757) in pixels_diff_map) # this pixel is outside reference, so, there is difference on it
         
    def test_compute_diff_with_cropping_on_step_image(self):
        """
        Check no error is raised when comparing 2 images with different sizes
        Here step image is smaller than reference, so no diff will be shown
        """
        comparator = PictureComparator();
        pixels_diff_map, too_many_diffs, diff_image = comparator.get_changed_pixels(self.dataDir + 'test_Image1.png', 
                                                 self.dataDir + 'test_Image1Crop.png',
                                                 [])
 
        self.assertEqual(len(pixels_diff_map), 0, "no diff should be found")    
        
    def test_compute_diff_without_exclusions_on_datatable(self):
        """
        Check exclusions are correctly computed
        """
        
        # image without differences where we add a square of different pixels
        image = numpy.zeros((6, 7), dtype=uint8)
        image[0][0] = 1
        image[1][0] = 1
        image[0][1] = 1
        image[1][1] = 1
        
        comparator = PictureComparator();
        diff_pixels, diff_image = comparator._build_list_of_changed_pixels(image, 7, 6, 7, 6, [])
        diff_pixels = self.convert_points_to_pixels(diff_pixels)
        self.assertEqual([Pixel(x=0, y=0), Pixel(x=1, y=0), Pixel(x=0, y=1), Pixel(x=1, y=1)], diff_pixels)
        
    def test_compute_diff_with_exclusions_inside_datatable(self):
        """
        Check exclusions are correctly computed
        Exclusion zone is inside the shape of datatable
        """
        
        # image without differences where we add a square of different pixels
        image = numpy.zeros((6, 7), dtype=uint8)
        image[0][0] = 1
        image[1][0] = 1
        image[0][1] = 1
        image[1][1] = 1
        
        comparator = PictureComparator();
        diff_pixels, diff_image = comparator._build_list_of_changed_pixels(image, 7, 6, 7, 6, [Rectangle(1, 1, 3, 3)])
        diff_pixels = self.convert_points_to_pixels(diff_pixels)
        self.assertEqual([Pixel(x=0, y=0), Pixel(x=1, y=0), Pixel(x=0, y=1)], diff_pixels)
        
    def test_compute_diff_with_exclusions_outside_datatable(self):
        """
        Check exclusions are correctly computed
        Exclusion zone is outside the shape of datatable
        """
        
        # image without differences where we add a square of different pixels
        image = numpy.zeros((6, 7), dtype=uint8)
        image[0][0] = 1
        image[1][0] = 1
        image[0][1] = 1
        image[1][1] = 1
        
        comparator = PictureComparator();
        diff_pixels, diff_image = comparator._build_list_of_changed_pixels(image, 7, 6, 7, 6, [Rectangle(10, 10, 3, 3)])
        diff_pixels = self.convert_points_to_pixels(diff_pixels)
        self.assertEqual([Pixel(x=0, y=0), Pixel(x=1, y=0), Pixel(x=0, y=1), Pixel(x=1, y=1)], diff_pixels)
        
    def test_compute_diff_with_multiple_exclusions_on_datatable(self):
        """
        Check multiple exclusions are correctly computed
        """
        
        # image without differences where we add a square of different pixels
        image = numpy.zeros((6, 7), dtype=uint8)
        image[0][0] = 1
        image[1][0] = 1
        image[0][1] = 1
        image[1][1] = 1

        comparator = PictureComparator();
        diff_pixels, diff_image = comparator._build_list_of_changed_pixels(image, 7, 6, 7, 6, [Rectangle(1, 1, 3, 3), Rectangle(0, 0, 5, 1)])
        diff_pixels = self.convert_points_to_pixels(diff_pixels)

        self.assertEqual([Pixel(x=0, y=1)], diff_pixels)
        
        
        
        