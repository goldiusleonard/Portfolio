"""Testing modules."""

import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import httpx

# Adjust sys.path to allow module import from parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from radar_stored_procedure_api import stored_app  # Now this import should work

client = TestClient(stored_app)

def test_update_data_asset_status():
    """Test if the update_data_asset endpoint is up and running."""
    response = client.get("/update_content_data_asset/")

    # Check if the response status code is 200 (OK)
    assert response.status_code == 200