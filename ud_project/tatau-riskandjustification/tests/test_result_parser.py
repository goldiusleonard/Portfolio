import os
import sys

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)
# Get the directory path of the current file
current_dir_path = os.path.dirname(current_file_path)
# Get the parent directory path
parent_dir_path = os.path.dirname(current_dir_path)
# Add the parent directory path to the sys.path
sys.path.insert(0, parent_dir_path)

from justification_risk import (
    ResultParser,
)  # Adjust the import to match your file structure


# Dummy test class
class TestResultParser:
    def test_valid_json(self):
        """Test parsing a valid JSON string."""
        llm_result = """
        {
            "English Justification": "The comment promotes fraudulent investment.",
            "Bahasa Malay Justification": "Komen ini mempromosikan pelaburan palsu.",
            "Risk Level": "High",
            "Irrelevant Score": "0/10"
        }
        """
        parser = ResultParser()
        result = parser.parse_justification_risk_results(llm_result)
        assert result == (
            "The comment promotes fraudulent investment.",
            "Komen ini mempromosikan pelaburan palsu.",
            "High",
            "0/10",
        )

    def test_json_with_backticks_and_text(self):
        """Test parsing JSON wrapped in backticks with extra explanatory text."""
        llm_result = """```json
        {
            "English Justification": "The comment promotes fraudulent investment.",
            "Bahasa Malay Justification": "Komen ini mempromosikan pelaburan palsu.",
            "Risk Level": "High",
            "Irrelevant Score": "0/10"
        }
        ```
        Note: The comment is classified as high risk.
        """
        parser = ResultParser()
        result = parser.parse_justification_risk_results(llm_result)
        assert result == (
            "The comment promotes fraudulent investment.",
            "Komen ini mempromosikan pelaburan palsu.",
            "High",
            "0/10",
        )

    def test_invalid_json(self):
        """Test parsing a completely invalid JSON string."""
        llm_result = "Invalid data here, definitely not JSON."
        parser = ResultParser()
        result = parser.parse_justification_risk_results(llm_result)
        assert "error" in result
        assert "No JSON block found in the result" in result["error"]

    def test_no_json_block_found(self):
        """Test parsing a string with no JSON block."""
        llm_result = "```text\nThis is not JSON.\n```"
        parser = ResultParser()
        result = parser.parse_justification_risk_results(llm_result)
        assert "error" in result
        assert "No JSON block found in the result" in result["error"]

    def test_missing_fields(self):
        """Test parsing JSON with missing fields."""
        llm_result = """
        {
            "English Justification": "The comment promotes fraudulent investment.",
            "Risk Level": "High"
        }
        """
        parser = ResultParser()
        result = parser.parse_justification_risk_results(llm_result)
        assert result == (
            "The comment promotes fraudulent investment.",
            "Missing",  # Missing "Bahasa Malay Justification"
            "High",
            "Missing",  # Missing "Irrelevant Score"
        )
