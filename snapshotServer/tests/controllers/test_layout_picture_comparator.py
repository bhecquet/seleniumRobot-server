'''
Tests for LayoutPictureComparator.

Test images are generated programmatically (no external image files are needed): a synthetic
"page" made of a few rectangular, textured zones is built, then altered (zone shifted, removed,
added, content changed, ...) to exercise each kind of difference the comparator should detect.
'''

import os
import shutil
import tempfile

import cv2
import numpy

from snapshotServer.controllers.layout_picture_comparator import LayoutPictureComparator, ZoneDiff
from snapshotServer.controllers.picture_comparator import Rectangle
from snapshotServer.exceptions.picture_comparator_error import PictureComparatorError
from snapshotServer.tests import SnapshotTestCase
from snapshotServer.utils.utils import get_test_directory

# zones used to build the synthetic "page" used as reference image
ZONE_A = Rectangle(30, 30, 60, 40)
ZONE_B = Rectangle(150, 30, 60, 40)
ZONE_C = Rectangle(30, 120, 60, 40)
ZONE_D = Rectangle(150, 120, 60, 40)

CANVAS_WIDTH = 300
CANVAS_HEIGHT = 220


class TestLayoutPictureComparator(SnapshotTestCase):

    def setUp(self):
        super().setUp()
        self.tmp_dir = tempfile.mkdtemp(prefix="layout_picture_comparator_")
        self.data_dir = get_test_directory()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)
        super().tearDown()

    # ------------------------------------------------------------------
    # helpers to build synthetic images
    # ------------------------------------------------------------------

    def _make_canvas(self):
        return numpy.full((CANVAS_HEIGHT, CANVAS_WIDTH), 255, dtype=numpy.uint8)

    def _draw_zone(self, canvas, rect, fill=200, pattern='diagonal'):
        x, y, w, h = rect
        cv2.rectangle(canvas, (x, y), (x + w, y + h), fill, thickness=-1)
        cv2.rectangle(canvas, (x, y), (x + w, y + h), 0, thickness=2)

        if pattern == 'diagonal':
            cv2.line(canvas, (x, y), (x + w, y + h), 0, 2)
            cv2.line(canvas, (x + w, y), (x, y + h), 0, 2)
        elif pattern == 'cross':
            cv2.line(canvas, (x + w // 2, y), (x + w // 2, y + h), 0, 2)
            cv2.line(canvas, (x, y + h // 2), (x + w, y + h // 2), 0, 2)
        elif pattern == 'checker':
            step = 8
            for row in range(y, y + h, step):
                for col in range(x, x + w, step):
                    if ((row - y) // step + (col - x) // step) % 2 == 0:
                        cv2.rectangle(canvas, (col, row), (min(col + step, x + w), min(row + step, y + h)), 0, -1)

    def _reference_canvas(self):
        canvas = self._make_canvas()
        self._draw_zone(canvas, ZONE_A)
        self._draw_zone(canvas, ZONE_B)
        self._draw_zone(canvas, ZONE_C)
        self._draw_zone(canvas, ZONE_D)
        return canvas

    def _save(self, canvas, name):
        path = os.path.join(self.tmp_dir, name)
        cv2.imwrite(path, canvas)
        return path

    def _assert_rect_centered_on(self, rect, expected_rect, delta=6, msg=None):
        """
        Zone detection (edge detection + dilation) never returns exactly the rectangle that was drawn (it
        grows it a bit), but it stays centered on it: compare centers instead of raw coordinates.
        """
        self.assertAlmostEqual(rect.x + rect.width / 2, expected_rect.x + expected_rect.width / 2, delta=delta, msg=msg)
        self.assertAlmostEqual(rect.y + rect.height / 2, expected_rect.y + expected_rect.height / 2, delta=delta, msg=msg)

    # ------------------------------------------------------------------
    # tests
    # ------------------------------------------------------------------

    def test_no_diff_on_identical_images(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        comparator = LayoutPictureComparator()
        diffs, _ = comparator.compare_zones(reference, reference)

        self.assertEqual([], diffs, "No difference should be found between an image and itself")

    def test_small_shift_is_ignored(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._make_canvas()
        self._draw_zone(image_canvas, Rectangle(ZONE_A.x + 2, ZONE_A.y + 1, ZONE_A.width, ZONE_A.height))
        self._draw_zone(image_canvas, ZONE_B)
        self._draw_zone(image_canvas, ZONE_C)
        self._draw_zone(image_canvas, ZONE_D)
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, _ = comparator.compare_zones(reference, image)

        self.assertEqual([], diffs, "A shift of a couple of pixels should be tolerated")

    def test_zone_shifted_beyond_tolerance_is_reported(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._make_canvas()
        shifted_zone_a = Rectangle(ZONE_A.x + 15, ZONE_A.y + 10, ZONE_A.width, ZONE_A.height)
        self._draw_zone(image_canvas, shifted_zone_a)
        self._draw_zone(image_canvas, ZONE_B)
        self._draw_zone(image_canvas, ZONE_C)
        self._draw_zone(image_canvas, ZONE_D)
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, diff_percentage = comparator.compare_zones(reference, image)

        self.assertEqual(1, len(diffs), "Only the moved zone should be reported: %s" % (diffs,))
        self.assertEqual('shifted', diffs[0].type)
        self._assert_rect_centered_on(diffs[0].ref_rect, ZONE_A)
        self._assert_rect_centered_on(diffs[0].image_rect, shifted_zone_a)
        self.assertAlmostEqual(diff_percentage, 100 * (78 * 58) / (300 * 220), delta=0.1)

    def test_missing_zone_is_reported(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._make_canvas()
        # ZONE_A is not drawn: it "disappeared"
        self._draw_zone(image_canvas, ZONE_B)
        self._draw_zone(image_canvas, ZONE_C)
        self._draw_zone(image_canvas, ZONE_D)
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, _ = comparator.compare_zones(reference, image)

        self.assertEqual(1, len(diffs), "Only the missing zone should be reported: %s" % (diffs,))
        self.assertEqual('missing', diffs[0].type)
        self._assert_rect_centered_on(diffs[0].ref_rect, ZONE_A)
        self.assertIsNone(diffs[0].image_rect)

    def test_appeared_zone_is_reported(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._reference_canvas()
        new_zone = Rectangle(230, 150, 50, 40)
        self._draw_zone(image_canvas, new_zone, pattern='checker')
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, _ = comparator.compare_zones(reference, image)

        self.assertEqual(1, len(diffs), "Only the new zone should be reported: %s" % (diffs,))
        self.assertEqual('appeared', diffs[0].type)
        self.assertIsNone(diffs[0].ref_rect)
        self._assert_rect_centered_on(diffs[0].image_rect, new_zone)

    def test_zone_content_changed_is_reported(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._make_canvas()
        self._draw_zone(image_canvas, ZONE_A, fill=40, pattern='checker')  # content of A is completely different
        self._draw_zone(image_canvas, ZONE_B)
        self._draw_zone(image_canvas, ZONE_C)
        self._draw_zone(image_canvas, ZONE_D)
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, _ = comparator.compare_zones(reference, image)

        self.assertEqual(1, len(diffs), "Only the changed zone should be reported: %s" % (diffs,))
        self.assertEqual('changed', diffs[0].type)
        self._assert_rect_centered_on(diffs[0].ref_rect, ZONE_A)
        self._assert_rect_centered_on(diffs[0].image_rect, ZONE_A)

    def test_excluded_zone_change_is_ignored(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._make_canvas()
        self._draw_zone(image_canvas, ZONE_A, fill=40, pattern='checker')
        self._draw_zone(image_canvas, ZONE_B)
        self._draw_zone(image_canvas, ZONE_C)
        self._draw_zone(image_canvas, ZONE_D)
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, _ = comparator.compare_zones(reference, image, exclude_zones=[Rectangle(0, 0, 100, 100)])

        self.assertEqual([], diffs, "Changes inside an excluded zone should not be reported")

    def test_global_stretch_from_top_left_is_compensated_by_alignment(self):
        reference_canvas = self._reference_canvas()
        reference = self._save(reference_canvas, "ref.png")

        # simulate a responsive layout stretching horizontally and shrinking vertically, always starting
        # from the page's top-left corner (no scroll, no translation) - e.g. a wider but shorter browser
        # window
        scale_x, scale_y = 1.15, 0.9
        stretched_width, stretched_height = int(CANVAS_WIDTH * scale_x), int(CANVAS_HEIGHT * scale_y)
        transform = numpy.float32([[scale_x, 0, 0], [0, scale_y, 0]])
        stretched_canvas = cv2.warpAffine(
            reference_canvas, transform, (stretched_width, stretched_height), borderValue=255)
        image = self._save(stretched_canvas, "image.png")

        comparator_without_alignment = LayoutPictureComparator(align_globally=False)
        diffs_without_alignment, _ = comparator_without_alignment.compare_zones(reference, image)
        self.assertTrue(
            len(diffs_without_alignment) > 0,
            "Without alignment, a global stretch should make (at least some) zones look different")

        comparator_with_alignment = LayoutPictureComparator(align_globally=True)
        diffs_with_alignment, _ = comparator_with_alignment.compare_zones(reference, image)
        self.assertEqual(
            [], diffs_with_alignment,
            "Global alignment should compensate the stretch so that no difference is reported: %s" % (diffs_with_alignment,))

    def test_translation_is_not_compensated_by_alignment(self):
        """
        Unlike a stretch, a pure translation (e.g. the whole page shifted without any change of scale) is
        not a transform web content can naturally undergo (a page is always laid out from its top-left
        corner): alignment must not try to compensate it, so that a real translation difference is still
        reported. Here, the shift is small enough that the per-zone local search (shift_search_radius)
        still finds and tolerates it, but the reference image itself, once "aligned", must remain
        (roughly) unchanged, i.e. still anchored at (0, 0), regardless of the translation applied to the
        compared image.
        """
        reference_canvas = self._reference_canvas()

        comparator = LayoutPictureComparator(align_globally=True)
        translation = numpy.float32([[1, 0, 8], [0, 1, 5]])
        translated_canvas = cv2.warpAffine(
            reference_canvas, translation, (CANVAS_WIDTH, CANVAS_HEIGHT), borderValue=255)

        aligned = comparator._align_reference(reference_canvas, translated_canvas)

        # the alignment must not have introduced any translation: comparing the "aligned" reference to the
        # original (untranslated) reference should show no significant difference, proving (0, 0) stayed
        # invariant
        diff = cv2.absdiff(aligned, reference_canvas)
        self.assertLess(diff.mean(), 1.0, "Alignment must not compensate a translation: top-left corner should stay invariant")

    def test_visualize_diffs_draws_rectangle_for_each_diff_type(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._make_canvas()
        # A is moved, B stays untouched, C disappears, D content changes, a new zone appears
        shifted_zone_a = Rectangle(ZONE_A.x + 15, ZONE_A.y + 10, ZONE_A.width, ZONE_A.height)
        self._draw_zone(image_canvas, shifted_zone_a)
        self._draw_zone(image_canvas, ZONE_B)
        self._draw_zone(image_canvas, ZONE_D, fill=40, pattern='checker')
        new_zone = Rectangle(230, 150, 50, 40)
        self._draw_zone(image_canvas, new_zone, pattern='checker')
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, _ = comparator.compare_zones(reference, image)
        diff_types = {zone_diff.type for zone_diff in diffs}
        self.assertEqual({'shifted', 'missing', 'changed', 'appeared'}, diff_types, "test setup should exercise all diff types: %s" % (diffs,))

        annotated = comparator.visualize_diffs(image, diffs)

        # the annotated picture is a color image, same size as the compared image, and different from it
        # (something has been drawn on it)
        original = cv2.imread(image, cv2.IMREAD_COLOR)
        self.assertEqual(original.shape, annotated.shape)
        self.assertFalse(numpy.array_equal(original, annotated), "Visualization should have drawn something on the image")

    def test_visualize_diffs_returns_unmodified_image_when_no_diff(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        comparator = LayoutPictureComparator()
        annotated = comparator.visualize_diffs(reference, [])

        original = cv2.imread(reference, cv2.IMREAD_COLOR)
        numpy.testing.assert_array_equal(original, annotated)

    def test_visualize_diffs_raises_when_image_file_not_found(self):
        comparator = LayoutPictureComparator()

        self.assertRaisesRegex(
            PictureComparatorError, "^Image file",
            comparator.visualize_diffs, os.path.join(self.tmp_dir, "missing.png"), [])

    def test_encode_visualization_returns_valid_png_bytes(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._make_canvas()
        self._draw_zone(image_canvas, ZONE_B)
        self._draw_zone(image_canvas, ZONE_C)
        self._draw_zone(image_canvas, ZONE_D)
        # ZONE_A is missing
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, _ = comparator.compare_zones(reference, image)

        png_bytes = comparator.encode_visualization(image, diffs)

        self.assertTrue(png_bytes.startswith(b'\x89PNG'), "Returned bytes should be a valid PNG file")

        decoded = cv2.imdecode(numpy.frombuffer(png_bytes, dtype=numpy.uint8), cv2.IMREAD_COLOR)
        self.assertEqual((CANVAS_HEIGHT, CANVAS_WIDTH, 3), decoded.shape)

    def test_build_diff_overlay_is_transparent_except_on_diffs(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._make_canvas()
        self._draw_zone(image_canvas, ZONE_B)
        self._draw_zone(image_canvas, ZONE_C)
        self._draw_zone(image_canvas, ZONE_D)
        # ZONE_A is missing
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, _ = comparator.compare_zones(reference, image)
        self.assertTrue(len(diffs) > 0, "test setup should produce at least one diff")

        overlay = comparator.build_diff_overlay(image, diffs)

        self.assertEqual((CANVAS_HEIGHT, CANVAS_WIDTH, 4), overlay.shape, "overlay should be a BGRA image, same size as the compared image")
        alpha = overlay[:, :, 3]
        self.assertTrue(numpy.any(alpha > 0), "overlay should not be fully transparent since there are diffs")
        self.assertTrue(numpy.any(alpha == 0), "overlay should stay transparent outside of the diffs")

    def test_build_diff_overlay_draws_more_when_labels_are_shown(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._make_canvas()
        self._draw_zone(image_canvas, ZONE_B)
        self._draw_zone(image_canvas, ZONE_C)
        self._draw_zone(image_canvas, ZONE_D)
        # ZONE_A is missing
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, _ = comparator.compare_zones(reference, image)

        overlay_without_labels = comparator.build_diff_overlay(image, diffs, show_labels=False)
        overlay_with_labels = comparator.build_diff_overlay(image, diffs, show_labels=True)

        non_transparent_without_labels = numpy.count_nonzero(overlay_without_labels[:, :, 3])
        non_transparent_with_labels = numpy.count_nonzero(overlay_with_labels[:, :, 3])
        self.assertGreater(
            non_transparent_with_labels, non_transparent_without_labels,
            "showing labels should draw additional (text) pixels on the overlay")

    def test_encode_diff_overlay_returns_valid_png_bytes(self):
        reference = self._save(self._reference_canvas(), "ref.png")

        image_canvas = self._make_canvas()
        self._draw_zone(image_canvas, ZONE_B)
        self._draw_zone(image_canvas, ZONE_C)
        self._draw_zone(image_canvas, ZONE_D)
        # ZONE_A is missing
        image = self._save(image_canvas, "image.png")

        comparator = LayoutPictureComparator(align_globally=False)
        diffs, _ = comparator.compare_zones(reference, image)

        png_bytes = comparator.encode_diff_overlay(image, diffs)

        self.assertTrue(png_bytes.startswith(b'\x89PNG'), "Returned bytes should be a valid PNG file")

        decoded = cv2.imdecode(numpy.frombuffer(png_bytes, dtype=numpy.uint8), cv2.IMREAD_UNCHANGED)
        self.assertEqual((CANVAS_HEIGHT, CANVAS_WIDTH, 4), decoded.shape, "decoded overlay should keep its alpha channel")

    def test_raises_when_reference_file_not_found(self):
        image = self._save(self._reference_canvas(), "image.png")
        comparator = LayoutPictureComparator()

        self.assertRaisesRegex(
            PictureComparatorError, "^Reference file",
            comparator.compare_zones, os.path.join(self.tmp_dir, "missing.png"), image)

    def test_raises_when_image_file_not_found(self):
        reference = self._save(self._reference_canvas(), "ref.png")
        comparator = LayoutPictureComparator()

        self.assertRaisesRegex(
            PictureComparatorError, "^Image file",
            comparator.compare_zones, reference, os.path.join(self.tmp_dir, "missing.png"))

    def _compare_zone_diff(self, expected, actual):
        self.assertEqual(expected.type, actual.type)
        if expected.ref_rect and actual.ref_rect:
            self.assertAlmostEqual(expected.ref_rect.x, actual.ref_rect.x, delta=2)
            self.assertAlmostEqual(expected.ref_rect.y, actual.ref_rect.y, delta=2)
            self.assertAlmostEqual(expected.ref_rect.width, actual.ref_rect.width, delta=2)
            self.assertAlmostEqual(expected.ref_rect.height, actual.ref_rect.height, delta=2)

        if expected.image_rect and actual.image_rect:
            self.assertAlmostEqual(expected.image_rect.x, actual.image_rect.x, delta=2)
            self.assertAlmostEqual(expected.image_rect.y, actual.image_rect.y, delta=2)
            self.assertAlmostEqual(expected.image_rect.width, actual.image_rect.width, delta=2)
            self.assertAlmostEqual(expected.image_rect.height, actual.image_rect.height, delta=2)

        self.assertAlmostEqual(expected.score, actual.score, delta=0.1)

    def test_no_diff_found_on_resize_real_image(self):
        comparator = LayoutPictureComparator(align_globally=True, similarity_threshold=0.8)
        reference = os.path.join(self.data_dir, 'controllers', 'layout_picture_comparator', 'jenkins_100p_full_cropped.png')
        image = os.path.join(self.data_dir, 'controllers', 'layout_picture_comparator', 'jenkins_90p_reduced_cropped.png')
        diffs, diff_percentage = comparator.compare_zones(reference, image)

        diffs = sorted(diffs, key=lambda zone: zone.ref_rect.x if zone.ref_rect else zone.image_rect.x)
        print(diffs)
        # comparator.show_diffs(image, diffs)  # uncomment locally to visually debug a failure

        self.assertAlmostEqual(diff_percentage, 5.76, delta=0.1)
        self.assertEqual(len(diffs), 18)
        self._compare_zone_diff(diffs[4], ZoneDiff(type='shifted', ref_rect=Rectangle(x=194, y=502, width=50, height=27), image_rect=Rectangle(x=200, y=493, width=50, height=27), score=0.873561441898346))
        self._compare_zone_diff(diffs[2], ZoneDiff(type='changed', ref_rect=Rectangle(x=17, y=384, width=156, height=165), image_rect=Rectangle(x=16, y=381, width=156, height=165), score=0.630462646484375))
        self._compare_zone_diff(diffs[13], ZoneDiff(type='missing', ref_rect=Rectangle(x=1539, y=15, width=30, height=29), image_rect=None, score=0.11229448020458221))
        self._compare_zone_diff(diffs[8], ZoneDiff(type='appeared', ref_rect=None, image_rect=Rectangle(x=268, y=605, width=28, height=10), score=0.0))

    def test_diffs_found_matches_expected_content_on_real_image(self):
        """
        These 2 real screenshots (same page, 2 different states) exhibit genuine content differences,
        verified visually: a zone that moved a bit (nav element), a zone whose content changed, and 3
        new zones that appeared (extra content displayed on the second screenshot). This does not check
        an exact pixel match (there isn't one between these 2 real screenshots), only that the kind,
        position and score of the differences found matches what was visually confirmed (see
        _compare_zone_diff, which tolerates a few pixels of difference on positions/score), so that a
        regression in zone detection/matching would still be caught.
        """
        comparator = LayoutPictureComparator(align_globally=True, similarity_threshold=0.8)
        reference = os.path.join(self.data_dir, 'controllers', 'layout_picture_comparator', 'avantages_MMA_1.png')
        image = os.path.join(self.data_dir, 'controllers', 'layout_picture_comparator', 'avantages_MMA_2.png')
        diffs, diff_percentage = comparator.compare_zones(reference, image)
        # comparator.show_diffs(image, diffs)  # uncomment locally to visually debug a failure

        diffs = sorted(diffs, key=lambda zone: zone.ref_rect.x if zone.ref_rect else zone.image_rect.x)

        self.assertEqual(len(diffs), 5, "Unexpected differences found: %s" % (diffs,))
        self._compare_zone_diff(diffs[4], ZoneDiff(type='shifted', ref_rect=Rectangle(x=918, y=994, width=84, height=25), image_rect=Rectangle(x=898, y=994, width=84, height=25), score=0.950654149055481))
        self._compare_zone_diff(diffs[0], ZoneDiff(type='changed', ref_rect=Rectangle(x=529, y=686, width=862, height=290), image_rect=Rectangle(x=527, y=686, width=862, height=290), score=0.6739785075187683))
        self._compare_zone_diff(diffs[2], ZoneDiff(type='appeared', ref_rect=None, image_rect=Rectangle(x=630, y=887, width=240, height=65), score=0.0))
        self._compare_zone_diff(diffs[3], ZoneDiff(type='appeared', ref_rect=None, image_rect=Rectangle(x=683, y=832, width=128, height=33), score=0.0))
        self._compare_zone_diff(diffs[1], ZoneDiff(type='appeared', ref_rect=None, image_rect=Rectangle(x=541, y=812, width=49, height=50), score=0.0))
