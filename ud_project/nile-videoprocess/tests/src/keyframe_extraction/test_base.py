import unittest
import cv2
import numpy as np
import numpy.testing as npt

from src.keyframe_extraction.base import ImageSelector


class TestImageSelector(unittest.TestCase):
    def test_get_brightness_score(self):
        # Create a dummy image with all black pixels
        black_image = np.zeros((100, 100, 3), dtype=np.uint8)

        # Create an ImageSelector object
        image_selector = ImageSelector()

        # Calculate brightness score
        brightness_score = image_selector.__get_brightness_score__(black_image)

        # Assert that the brightness score is close to 0 (black)
        self.assertAlmostEqual(brightness_score, 0.0, delta=0.1)

    def test_get_brightness_score_white_image(self):
        # Create a dummy image with all white pixels
        white_image = np.ones((100, 100, 3), dtype=np.uint8) * 255

        # Create an ImageSelector object
        image_selector = ImageSelector()

        # Calculate brightness score
        brightness_score = image_selector.__get_brightness_score__(white_image)

        # Assert that the brightness score is close to 100 (white)
        self.assertAlmostEqual(brightness_score, 100.0, delta=0.1)

    def test_filter_optimum_brightness_and_contrast(self):
        # Create dummy images with different brightness and contrast
        bright_image = np.ones((100, 100, 3), dtype=np.uint8) * 150
        dark_image = np.ones((100, 100, 3), dtype=np.uint8) * 50
        high_contrast_image = cv2.imread("sample/high_contrast.jpg")
        low_contrast_image = cv2.imread("sample/low_contrast.jpg")

        # Set brightness and contrast ranges
        image_selector = ImageSelector()

        # Create a list of dummy images
        images = [bright_image, dark_image, high_contrast_image, low_contrast_image]

        # Filter images based on brightness and contrast
        filtered_images = (
            image_selector.__filter_optimum_brightness_and_contrast_images__(images)
        )

        # Assert that only high contrast image is filtered
        self.assertEqual(len(filtered_images), 2)
        npt.assert_array_equal(filtered_images[0], high_contrast_image)
