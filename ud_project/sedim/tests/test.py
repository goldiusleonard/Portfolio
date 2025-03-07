"""Testing modules."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, Path(__file__).parent.parent.resolve())

from radar_stored_procedure_api import stored_app

client = TestClient(stored_app)


def test_root() -> None:
    """Test endpoints related to role functionality."""
    response = client.get("/role/get_all_roles/")
    status_code = 500
    assert response.status_code == status_code
