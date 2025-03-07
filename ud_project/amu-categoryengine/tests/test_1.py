import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the path to the module to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Amu_prompt import gen_category_subcategory


class TestGenCategorySubcategory(unittest.TestCase):
    @patch("Amu_prompt.requests.post")
    def test_gen_category_subcategory_none_content(self, mock_post):
        """Test the gen_category_subcategory function with None content"""
        # Input None content
        content = None

        # Call the function with None content and make sure the return is {"category": "None", "subcategory": "None"}
        result = gen_category_subcategory(content)

        # Check that the result is "None, None"
        # self.assertEqual(result["category"], "None")
        # self.assertEqual(result["subcategory"], "None")
        assert result["category"] == "None"
        assert result["subcategory"] == "None"

    @patch("Amu_prompt.requests.post")
    def test_gen_category_subcategory_scam_forex(self, mock_post):
        """Test the gen_category_subcategory function with scam and forex content."""
        # Mock the response from the API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"text": "Scam,Forex"}],
        }
        mock_post.return_value = mock_response

        # Input content for the test
        content = "Scam related to Forex trading."

        # Call the function with mocked API response
        result = gen_category_subcategory(content)

        # Check that the result is "Scam, Forex"
        # self.assertEqual(result["category"], "Scam")
        # self.assertEqual(result["subcategory"], "Forex")
        assert result["category"] == "Scam"
        assert result["subcategory"] == "Forex"


if __name__ == "__main__":
    unittest.main()
