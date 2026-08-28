'''
Layout-aware picture comparator.

Unlike PictureComparator (pixel by pixel comparison), this comparator tries to reason about
"zones" (logical blocks of content, roughly delimited by their edges/contours) rather than raw
pixels. This makes it tolerant to small, global changes that do not really affect the content of
a page: a few pixels shift of some element, a slightly different window size, minor color
variations, ...

The algorithm is voluntarily kept simple and relies only on OpenCV / numpy (already used
elsewhere in the project), so that no new dependency is required:

1. Optionally realign the reference image on the new image using an ORB feature based, origin-anchored
   scaling transform (see _align_reference for details). This compensates for global changes (browser
   window resized, ...) before zones are compared.
2. Detect zones in both images (reference and new image) using edge detection + dilation +
   contours. Dilation is used to merge close edges/text into bigger, logical zones instead of
   many small ones.
3. For each zone of the reference image, look for the best match in the new image:
   - first in a small window around the zone's original position (a shift of a few pixels is
     considered "no difference"),
   - if no good match is found there, widen the search window: this allows detecting a zone that
     has moved (its content is unchanged) without being fooled by other, similar zones located
     further away (typically: repetitive rows of a table), since the search window is only
     widened progressively, starting close to the expected position.
4. Zones of the reference image that could not be matched anywhere are reported as "missing".
   Zones of the new image that do not match any zone of the reference image are reported as
   "appeared". Zones found at the same place but with a low similarity score are reported as
   "changed". Zones found away from their original position (with a matching content) are
   reported as "shifted".

This module purposely only exposes a comparison algorithm. It does not (yet) interact with
Django models, the diff computer or the UI: this is meant to be plugged in a later iteration
once the algorithm has proven to give consistent results.
'''

import collections
import logging
import os

import cv2
import numpy

from snapshotServer.controllers.picture_comparator import Rectangle
from snapshotServer.exceptions.picture_comparator_error import PictureComparatorError

logger = logging.getLogger(__name__)


# 'type' is one of 'shifted', 'missing', 'appeared', 'changed'
# 'ref_rect' is the zone rectangle in the reference image (None for 'appeared')
# 'image_rect' is the zone rectangle in the compared image (None for 'missing')
# 'score' is the similarity score (cv2.matchTemplate correlation) of the best match found, when relevant
ZoneDiff = collections.namedtuple("ZoneDiff", ['type', 'ref_rect', 'image_rect', 'score'])


class LayoutPictureComparator:
    """
    Compares 2 images, not pixel by pixel, but zone by zone, so that it stays tolerant to minor
    shifts / color changes while still detecting zones that really moved, disappeared, appeared
    or changed.
    """

    def __init__(self,
                 min_zone_size=8,
                 merge_kernel_size=15,
                 position_tolerance=3,
                 shift_search_radius=40,
                 similarity_threshold=0.80,
                 presence_threshold=0.5,
                 align_globally=False,
                 min_orb_matches=10,
                 content_blur_kernel=9):
        """
        @param min_zone_size: minimal width/height (in pixels) for a detected zone to be taken into account.
                               Used to filter out noise (very small contours)
        @param merge_kernel_size: size (in pixels) of the dilation kernel used to merge close edges into a single zone.
                                   The bigger it is, the bigger (and fewer) the detected zones will be
        @param position_tolerance: maximum position difference (in pixels), in any direction, below which a zone is
                                    still considered to be "at the same place" (handles anti-aliasing / minor jitter)
        @param shift_search_radius: maximum distance (in pixels) to search for a zone that would have moved, before
                                     considering it is not present anymore in the image
        @param similarity_threshold: cv2.matchTemplate correlation score (0-1) above which 2 zones are considered
                                      identical
        @param presence_threshold: cv2.matchTemplate correlation score (0-1) below which we consider that a zone
                                    simply is not present anymore in the image (whatever the position)
        @param align_globally: if True, try to realign the reference image on the new image (using an ORB based
                                homography) before comparing zones, to compensate for global changes
        @param min_orb_matches: minimum number of ORB keypoint matches required to compute a global alignment.
                                 Below this value, global alignment is skipped and images are compared as-is
        @param content_blur_kernel: size (in pixels, must be odd) of the Gaussian blur kernel applied to zone
                                     content before computing its similarity score. Real screenshots of the same
                                     page (even at the exact same position/size) rarely match pixel for pixel on
                                     text: font hinting / sub-pixel anti-aliasing changes slightly from one render
                                     to the other. This has a small effect on the general shape of a zone but a
                                     large effect on the raw pixel correlation of fine, high frequency content
                                     such as text. Blurring smooths out this rendering noise while still keeping
                                     genuinely different content well below similarity_threshold. Set to 0 to
                                     disable (raw pixel comparison)
        """
        self.min_zone_size = min_zone_size
        self.merge_kernel_size = merge_kernel_size
        self.position_tolerance = position_tolerance
        self.shift_search_radius = shift_search_radius
        self.similarity_threshold = similarity_threshold
        self.presence_threshold = presence_threshold
        self.align_globally = align_globally
        self.min_orb_matches = min_orb_matches
        self.content_blur_kernel = content_blur_kernel


    def _compute_zone_diffs_surface(self, zone_diffs):

        surface = 0
        for zone in zone_diffs:
            if zone.ref_rect:
                surface += zone.ref_rect.width * zone.ref_rect.height
            elif zone.image_rect:
                surface += zone.image_rect.width * zone.image_rect.height

        return surface

    def compare_zones(self, reference, image, exclude_zones=None):
        """
        Compares the reference image to the new image, zone by zone.

        @param reference: path to the reference image
        @param image: path to the image to compare to the reference
        @param exclude_zones: list of Rectangle (or any 4-uple (x, y, width, height)) that must be ignored
        @return: list of ZoneDiff, one for each zone that changed (unchanged zones are not returned)
        """
        exclude_zones = exclude_zones or []

        if not os.path.isfile(reference):
            raise PictureComparatorError("Reference file %s does not exist" % reference)
        if not os.path.isfile(image):
            raise PictureComparatorError("Image file %s does not exist" % image)

        ref_gray = cv2.imread(reference, cv2.IMREAD_GRAYSCALE)
        img_gray = cv2.imread(image, cv2.IMREAD_GRAYSCALE)

        if ref_gray is None:
            raise PictureComparatorError("Reference file %s could not be read as an image" % reference)
        if img_gray is None:
            raise PictureComparatorError("Image file %s could not be read as an image" % image)

        if self.align_globally:
            ref_gray = self._align_reference(ref_gray, img_gray)

        ref_zones = self._detect_zones(ref_gray, exclude_zones)
        img_zones = self._detect_zones(img_gray, exclude_zones)

        diffs = []
        matched_image_rects = []

        for ref_rect in ref_zones:
            zone_diff = self._match_zone(ref_gray, ref_rect, img_gray)
            if zone_diff:
                diffs.append(zone_diff)
                if zone_diff.image_rect:
                    matched_image_rects.append(zone_diff.image_rect)
            else:
                # unchanged zone: still claim its own position so that it's not reported as 'appeared' below
                matched_image_rects.append(ref_rect)

        # any zone detected in the new image that is not explained by a reference zone is new content
        for img_rect in img_zones:
            if not self._overlaps_any(img_rect, matched_image_rects):
                diffs.append(ZoneDiff('appeared', None, img_rect, 0.0))

        diff_percentage = 100 * self._compute_zone_diffs_surface(diffs) / (ref_gray.shape[1] * ref_gray.shape[0])

        return diffs, diff_percentage

    # colors (BGR) used to visualize each kind of difference
    VISUALIZATION_COLORS = {
        'shifted': (0, 165, 255),    # orange
        'missing': (255, 0, 0),      # blue
        'appeared': (0, 255, 0),     # green
        'changed': (0, 0, 255),      # red
    }

    def visualize_diffs(self, image, diffs, thickness=2, show_labels=True):
        """
        Draws the list of ZoneDiff on top of the compared image, so that differences can be reviewed
        visually. Each kind of difference is drawn with its own color (see VISUALIZATION_COLORS):
        - 'shifted': the zone at its new (matched) position, in orange, with an arrow to its former
                     (reference) position
        - 'missing': the zone at its former (reference) position, dashed in blue (as it's not there anymore)
        - 'appeared': the new zone, in green
        - 'changed': the zone at its (unchanged) position, in red

        @param image: path to the image that was compared to the reference (the one passed as 'image' to
                       compare_zones)
        @param diffs: list of ZoneDiff, as returned by compare_zones()
        @param thickness: thickness (in pixels) of the rectangles / lines drawn
        @param show_labels: if True, prints the diff type next to each rectangle
        @return: a numpy array (BGR image) with all differences drawn on it
        """
        if not os.path.isfile(image):
            raise PictureComparatorError("Image file %s does not exist" % image)

        annotated = cv2.imread(image, cv2.IMREAD_COLOR)
        if annotated is None:
            raise PictureComparatorError("Image file %s could not be read as an image" % image)

        for zone_diff in diffs:
            color = self.VISUALIZATION_COLORS.get(zone_diff.type, (255, 255, 255))

            if zone_diff.type == 'missing':
                # nothing to draw on the new image but the former position of the vanished zone
                self._draw_dashed_rect(annotated, zone_diff.ref_rect, color, thickness)
                anchor_rect = zone_diff.ref_rect
            else:
                cv2.rectangle(
                    annotated,
                    (zone_diff.image_rect.x, zone_diff.image_rect.y),
                    (zone_diff.image_rect.x + zone_diff.image_rect.width, zone_diff.image_rect.y + zone_diff.image_rect.height),
                    color, thickness)
                anchor_rect = zone_diff.image_rect

                if zone_diff.type == 'shifted' and zone_diff.ref_rect:
                    # draw a line from the former position to the new one, to make the shift obvious
                    ref_center = (zone_diff.ref_rect.x + zone_diff.ref_rect.width // 2, zone_diff.ref_rect.y + zone_diff.ref_rect.height // 2)
                    new_center = (zone_diff.image_rect.x + zone_diff.image_rect.width // 2, zone_diff.image_rect.y + zone_diff.image_rect.height // 2)
                    cv2.arrowedLine(annotated, ref_center, new_center, color, thickness)

            if show_labels:
                label_pos = (anchor_rect.x, max(0, anchor_rect.y - 5))
                cv2.putText(annotated, zone_diff.type, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, thickness)

        return annotated

    def encode_visualization(self, image, diffs, thickness=2, show_labels=True):
        """
        Same as visualize_diffs(), but returns a PNG-encoded byte buffer instead of a numpy array, so that
        it can directly be saved to disk / stored in a File field, similarly to DiffComputer.mark_diff().
        """
        annotated = self.visualize_diffs(image, diffs, thickness=thickness, show_labels=show_labels)
        _, buffer = cv2.imencode(".png", annotated)
        return buffer.tobytes()

    def build_diff_overlay(self, image, diffs, thickness=2, show_labels=True):
        """
        Builds a transparent overlay (same size as 'image', RGBA), highlighting the zones reported as
        different, so that it can be superimposed on top of the original picture, the same way
        PictureComparator / DiffComputer.mark_diff() build their (opaque red on transparent background)
        diff mask. Unlike visualize_diffs()/encode_visualization() (meant for standalone debugging), this
        keeps the background fully transparent so it does not hide the picture it is overlaid on.

        @param image: path to the image that was compared to the reference (only used to get its dimensions)
        @param diffs: list of ZoneDiff, as returned by compare_zones()
        @param thickness: thickness (in pixels) of the rectangles drawn
        @param show_labels: if True, prints the diff type (shifted / missing / appeared / changed) next to
                             each rectangle, the same way visualize_diffs() does
        @return: a numpy array (BGRA image), transparent except on the rectangles (and, optionally, labels)
                 that highlight differences
        """
        if not os.path.isfile(image):
            raise PictureComparatorError("Image file %s does not exist" % image)

        img = cv2.imread(image, cv2.IMREAD_COLOR)
        if img is None:
            raise PictureComparatorError("Image file %s could not be read as an image" % image)

        height, width = img.shape[:2]
        overlay = numpy.zeros((height, width, 4), dtype=numpy.uint8)

        for zone_diff in diffs:
            color = self.VISUALIZATION_COLORS.get(zone_diff.type, (255, 255, 255))
            bgra_color = (color[0], color[1], color[2], 255)
            rect = zone_diff.ref_rect if zone_diff.type == 'missing' else zone_diff.image_rect
            if not rect:
                continue

            if zone_diff.type == 'missing':
                self._draw_dashed_rect(overlay, rect, bgra_color, thickness)
            else:
                cv2.rectangle(overlay, (rect.x, rect.y), (rect.x + rect.width, rect.y + rect.height), bgra_color, thickness)

            if show_labels:
                label_pos = (rect.x, max(0, rect.y - 5))
                cv2.putText(overlay, zone_diff.type, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 0.5, bgra_color, thickness)

        return overlay

    def encode_diff_overlay(self, image, diffs, thickness=2, show_labels=True):
        """
        Same as build_diff_overlay(), but returns a PNG-encoded byte buffer instead of a numpy array, so
        that it can directly be stored, e.g. in Snapshot.pixelsDiff.
        """
        overlay = self.build_diff_overlay(image, diffs, thickness=thickness, show_labels=show_labels)
        _, buffer = cv2.imencode(".png", overlay)
        return buffer.tobytes()

    def show_diffs(self, image, diffs, thickness=2, show_labels=True, window_name="LayoutPictureComparator diffs"):
        """
        Debugging helper: opens a window displaying the compared image with all differences drawn on it
        (see visualize_diffs()). Meant to be called manually from a test when investigating a doubtful
        result, not to be used in production code (it blocks until a key is pressed and requires a display).

        Closes the window as soon as a key is pressed.
        """
        annotated = self.visualize_diffs(image, diffs, thickness=thickness, show_labels=show_labels)

        # Custom window
        cv2.namedWindow(window_name, cv2.WINDOW_KEEPRATIO)
        cv2.imshow(window_name, annotated)
        cv2.resizeWindow(window_name, annotated.shape[1], annotated.shape[0])
        cv2.waitKey(0)
        cv2.destroyWindow(window_name)

    def _draw_dashed_rect(self, img, rect, color, thickness, dash_length=6):
        """
        Draws a dashed rectangle (used to represent a zone that is not present anymore in the image)
        """
        x, y, w, h = rect
        points = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            length = max(abs(x2 - x1), abs(y2 - y1))
            steps = max(1, length // dash_length)
            for i in range(0, steps, 2):
                start = (int(x1 + (x2 - x1) * i / steps), int(y1 + (y2 - y1) * i / steps))
                end = (int(x1 + (x2 - x1) * min(i + 1, steps) / steps), int(y1 + (y2 - y1) * min(i + 1, steps) / steps))
                cv2.line(img, start, end, color, thickness)

    def _align_reference(self, ref_gray, img_gray):
        """
        Tries to realign the reference image on the new image, using an ORB feature based transform, so
        that global changes (browser window resized, ...) do not impact zone comparisons. If not enough
        keypoints/matches are found, the reference image is returned unchanged.

        The transform is deliberately restricted to an axis-aligned scaling anchored at the image's
        top-left corner (0, 0): (x, y) -> (sx * x, sy * y), with independent horizontal/vertical scale
        factors and no translation/rotation/shear. This models how web content actually reflows when a
        browser window is resized: the page always starts being laid out from its top-left corner, and
        may stretch/shrink horizontally and vertically by different amounts (responsive layout), but it is
        not translated, rotated or scrolled between 2 screenshots taken the same way. Anchoring the
        transform at (0, 0) instead of letting it fit an arbitrary translation avoids the alignment
        "correcting" an offset that should actually be reported as a real difference.
        """
        try:
            orb = cv2.ORB_create(500)
            kp_ref, des_ref = orb.detectAndCompute(ref_gray, None)
            kp_img, des_img = orb.detectAndCompute(img_gray, None)

            if des_ref is None or des_img is None or len(kp_ref) < self.min_orb_matches or len(kp_img) < self.min_orb_matches:
                return ref_gray

            matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = sorted(matcher.match(des_ref, des_img), key=lambda m: m.distance)

            if len(matches) < self.min_orb_matches:
                return ref_gray

            src_pts = numpy.float32([kp_ref[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
            dst_pts = numpy.float32([kp_img[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

            # estimateAffinePartial2D is only used here to get a robust (RANSAC) inlier mask, rejecting
            # spurious keypoint matches: the transform itself is discarded, and replaced below by our own
            # scale-only, origin-anchored transform, fitted on the resulting inliers
            _, inlier_mask = cv2.estimateAffinePartial2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=5.0)
            if inlier_mask is None or inlier_mask.sum() < self.min_orb_matches:
                return ref_gray

            inliers = inlier_mask.ravel().astype(bool)
            src_x = src_pts[inliers, 0, 0]
            src_y = src_pts[inliers, 0, 1]
            dst_x = dst_pts[inliers, 0, 0]
            dst_y = dst_pts[inliers, 0, 1]

            scale_x = self._fit_origin_anchored_scale(src_x, dst_x)
            scale_y = self._fit_origin_anchored_scale(src_y, dst_y)
            if scale_x is None or scale_y is None:
                return ref_gray
            logger.info("Estimated scales: scale_x=%f, scale_y=%f", scale_x, scale_y)
            transform = numpy.float32([[scale_x, 0, 0], [0, scale_y, 0]])

            height, width = img_gray.shape
            return cv2.warpAffine(ref_gray, transform, (width, height), borderMode=cv2.BORDER_REPLICATE)
        except cv2.error:
            logger.exception("Could not align reference image on new image, comparing them as-is")
            return ref_gray

    def _fit_origin_anchored_scale(self, src_coords, dst_coords, min_scale=0.5, max_scale=2.0):
        """
        Finds the scale factor 's' that best maps 'src_coords' to 'dst_coords' as dst = s * src (i.e. a
        1D scaling anchored at 0), in the least squares sense: s = sum(src * dst) / sum(src ** 2).

        Before accepting it, the fit is compared to how well a plain translation (dst = src + t, with the
        best possible 't') would explain the same points. This is what distinguishes a genuine
        origin-anchored scaling from a translation (or a translation dominated movement): when points are
        actually offset by a constant amount, a translation model fits them almost perfectly while an
        origin-anchored scale cannot (it necessarily has a much higher residual, since a translation isn't
        a scaling from 0). Conversely, when points genuinely follow a scaling from the origin, the
        translation model fits markedly worse. Note: comparing raw residuals is preferred here to
        checking the intercept of an unconstrained regression, which would be unreliable: keypoints
        detected in a screenshot are rarely close to (0, 0), so extrapolating a regression line back to
        x=0 amplifies any small slope estimation noise into a large, misleading intercept.

        Fitting a pure origin-anchored scale on points that are actually offset by a translation is
        numerically well defined but meaningless: it would silently let part of a real translation be
        "explained away" as a bogus scale factor, which must not happen (see _align_reference's
        docstring: translations must not be compensated).

        Returns None if the scale cannot be reliably estimated (no/degenerate data, a better fit as a
        translation, or an aberrant scale value), in which case the caller should not apply any alignment.
        """
        if len(src_coords) < 2:
            return None

        denominator = numpy.sum(src_coords ** 2)
        if denominator < 1e-6:
            return None

        scale = float(numpy.sum(src_coords * dst_coords) / denominator)
        if not min_scale <= scale <= max_scale:
            return None

        residual_scale = numpy.sum((dst_coords - scale * src_coords) ** 2)
        translation = numpy.mean(dst_coords - src_coords)
        residual_translation = numpy.sum((dst_coords - (src_coords + translation)) ** 2)

        if residual_translation < residual_scale * 0.5:
            # a plain translation explains the points markedly better than an origin-anchored scale: this
            # looks like a scroll/translation, not a responsive-layout stretch. Do not compensate it
            return None

        return scale

    def _detect_zones(self, gray_img, exclude_zones):
        """
        Detects "zones" (logical blocks of content) in an image: edges are detected, then dilated so that
        close edges/text merge into a single zone, and contours of the resulting blobs are used as zones.
        """
        edges = cv2.Canny(gray_img, 50, 150)
        kernel = numpy.ones((self.merge_kernel_size, self.merge_kernel_size), numpy.uint8)
        dilated = cv2.dilate(edges, kernel)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        zones = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w < self.min_zone_size or h < self.min_zone_size:
                continue
            if self._overlaps_excluded(x, y, w, h, exclude_zones):
                continue
            zones.append(Rectangle(x, y, w, h))

        return zones

    def _overlaps_excluded(self, x, y, w, h, exclude_zones):
        for exclude_zone in exclude_zones:
            ex, ey, ew, eh = exclude_zone
            if x < ex + ew and x + w > ex and y < ey + eh and y + h > ey:
                return True
        return False

    def _match_zone(self, ref_gray, ref_rect, img_gray):
        """
        Looks for the best match of 'ref_rect' (from the reference image) in the new image.
        @return: None if the zone is unchanged, a ZoneDiff otherwise
        """
        x, y, w, h = ref_rect
        crop = ref_gray[y:y + h, x:x + w]

        # is content still there, at (roughly) the same position ?
        same_pos_score, _ = self._template_match(crop, img_gray, ref_rect, self.position_tolerance)
        if same_pos_score >= self.similarity_threshold:
            return None

        # look in a wider area: either the zone moved, its content changed, or it's simply not there anymore
        wide_score, wide_loc = self._template_match(crop, img_gray, ref_rect, self.shift_search_radius)

        if wide_score < self.presence_threshold:
            return ZoneDiff('missing', ref_rect, None, wide_score)

        matched_rect = Rectangle(wide_loc[0], wide_loc[1], w, h)
        delta = max(abs(wide_loc[0] - x), abs(wide_loc[1] - y))

        if delta <= self.position_tolerance:
            # same position, but not similar enough: content changed
            return ZoneDiff('changed', ref_rect, matched_rect, wide_score)
        elif wide_score >= self.similarity_threshold:
            return ZoneDiff('shifted', ref_rect, matched_rect, wide_score)
        else:
            return ZoneDiff('changed', ref_rect, matched_rect, wide_score)

    def _template_match(self, crop, img_gray, rect, radius):
        """
        Searches 'crop' (extracted from the reference image) inside a window of 'img_gray' centered on
        'rect' position, extended by 'radius' pixels in every direction.
        A light Gaussian blur (see content_blur_kernel) is applied beforehand to both the crop and the
        window, so that the returned similarity score is tolerant to fine-grained rendering noise (text
        anti-aliasing, sub-pixel hinting, ...) without hiding genuinely different content.
        @return: (score, (x, y)) the best correlation score and the position (top left corner, in img_gray
                 coordinates) where it was found
        """
        x, y, w, h = rect
        x0 = max(0, x - radius)
        y0 = max(0, y - radius)
        x1 = min(img_gray.shape[1], x + w + radius)
        y1 = min(img_gray.shape[0], y + h + radius)
        window = img_gray[y0:y1, x0:x1]

        if window.shape[0] < h or window.shape[1] < w:
            return -1.0, (x, y)

        if self.content_blur_kernel:
            crop = cv2.GaussianBlur(crop, (self.content_blur_kernel, self.content_blur_kernel), 0)
            window = cv2.GaussianBlur(window, (self.content_blur_kernel, self.content_blur_kernel), 0)

        result = cv2.matchTemplate(window, crop, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        return max_val, (x0 + max_loc[0], y0 + max_loc[1])

    def _overlaps_any(self, rect, rect_list, min_iou=0.3):
        return any(self._iou(rect, other) >= min_iou for other in rect_list)

    def _iou(self, rect_a, rect_b):
        ax2, ay2 = rect_a.x + rect_a.width, rect_a.y + rect_a.height
        bx2, by2 = rect_b.x + rect_b.width, rect_b.y + rect_b.height

        inter_x1 = max(rect_a.x, rect_b.x)
        inter_y1 = max(rect_a.y, rect_b.y)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)

        if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
            return 0.0

        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        union_area = rect_a.width * rect_a.height + rect_b.width * rect_b.height - inter_area

        return inter_area / union_area if union_area else 0.0
