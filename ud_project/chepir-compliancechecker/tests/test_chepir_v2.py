import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chepir_fastapi_v2 import app  # noqa: E402

# Initialize test client
client = TestClient(app)


@pytest.fixture
def mock_compliance_checker(monkeypatch):
    """Mock the ComplianceChecker to avoid real API calls"""

    def mock_analyze(*args, **kwargs):
        return []  # Return empty violations list for testing

    # Apply the mock
    monkeypatch.setattr("chepir_v2.ComplianceChecker.analyze_content", mock_analyze)


@pytest.mark.usefixtures("mock_compliance_checker")
def test_direct_analysis_endpoint():
    """Test the direct analysis endpoint with a sample text"""
    test_text = "This is a sample test text."
    response = client.post("/direct_analysis", json={"text": test_text})

    assert response.status_code == 200
    assert not response.json()["violations_found"]
    assert len(response.json()["violations_details"]) == 0
    assert "analysis_timestamp" in response.json()
    assert "documents_analyzed" in response.json()


@pytest.mark.usefixtures("mock_compliance_checker")
def test_law_violations_endpoint():
    """Test the law violations endpoint with sample data"""
    test_data = {
        "document_ids": ["Penal_Code.json.law_document.extraction.test"],
        "text": "This is a test content.",
    }

    response = client.post("/law_regulated", json=test_data)

    assert response.status_code == 200
    assert not response.json()["violations_found"]
    assert len(response.json()["violations_details"]) == 0
    assert "analysis_timestamp" in response.json()
    assert "documents_analyzed" in response.json()


def test_empty_content():
    """Test handling of empty content"""
    response = client.post("/direct_analysis", json={"text": ""})
    assert response.status_code == 400
    assert "Empty content" in response.json()["detail"]
