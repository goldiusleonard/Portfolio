"""Test law violation function."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.api.endpoints.functions.law_violation_function import (
    delete_file,
    edit_file,
    get_law_violation_file_by_id,
    upload_file,
)
from app.core.constants import SUCCESS_CODE
from app.models.schemas.law_violation_schema import (
    LawViolationData,
    LawViolationDataEdit,
)


@pytest.fixture
def mock_db_session() -> Session:
    """Fixture to mock a database session."""
    return MagicMock(spec=Session)


def test_get_law_violation_file_by_id_found(mock_db_session: Session) -> None:
    """Test retrieval of a specific law violation file by ID when found."""
    mock_violation = MagicMock()
    mock_violation.id = 1
    mock_violation.name = "Violation 1"
    mock_violation.file = "test_file.pdf"  # Corrected attribute name
    mock_violation.category = "Category A"
    mock_violation.effective_date = "2024-01-01"
    mock_violation.upload_date = "2024-01-01"
    mock_violation.publisher = "Publisher X"
    mock_violation.summary = "Summary of violation"

    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_violation
    )
    result = get_law_violation_file_by_id(1, mock_db_session)
    expected_result = {
        "data": {
            "id": 1,
            "name": "Violation 1",
            "file_name": "test_file.pdf",
            "category": "Category A",
            "effective_date": "2024-01-01",
            "upload_date": "2024-01-01",
            "publisher": "Publisher X",
            "summary": "Summary of violation",
        },
    }
    assert result == expected_result  # noqa: S101


def test_get_law_violation_file_by_id_not_found(mock_db_session: Session) -> None:
    """Test retrieval of a specific law violation file by ID when not found."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    result = get_law_violation_file_by_id(1, mock_db_session)

    assert result == {"error": "File not found"}  # noqa: S101


def test_upload_file(mock_db_session: Session) -> None:
    """Test uploading a new law violation file."""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.file = MagicMock()  # Added 'file' attribute
    mock_file.filename = "test.pdf"
    mock_file.file.read.return_value = b"file_content"

    # Create a LawViolationData instance
    law_violation_data = LawViolationData(
        law_name="Violation 1",
        category="Category A",
        effective_date=datetime.strptime("01-01-2024", "%m-%d-%Y"),  # noqa: DTZ007
        publisher="Publisher X",
        summary="Summary",
    )

    with patch(
        "app.api.endpoints.functions.law_violation_function.requests.post",
    ) as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = SUCCESS_CODE
        mock_response.json.return_value = {"collection_name": "test_collection"}
        mock_post.return_value = mock_response

        result = upload_file(
            mock_file,
            law_violation_data,
            mock_db_session,
        )

    assert result["message"] == "File uploaded successfully"  # noqa: S101
    assert "id" in result  # noqa: S101


def test_edit_file_success(mock_db_session: Session) -> None:
    """Test editing an existing law violation file successfully."""
    mock_violation = MagicMock()
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_violation
    )

    updated_data = LawViolationDataEdit(
        law_name="Updated Law Name",
        category="Updated Category",
        effective_date="01-10-2023",
        upload_date="01-10-2023",
        publisher="Updated Publisher",
        summary="Updated Summary",
    )

    result = edit_file(1, updated_data, mock_db_session)

    assert result == {"message": "File updated successfully"}  # noqa: S101


def test_edit_file_not_found(mock_db_session: Session) -> None:
    """Test editing a law violation file that does not exist."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    law_data = LawViolationDataEdit(
        law_name="Updated Law Name",
        category="Updated Category",
        effective_date="01-10-2023",
        upload_date="01-10-2023",
        publisher="Updated Publisher",
        summary="Updated Summary",
    )
    result = edit_file(
        id_violation=1,
        law_violation_data=law_data,
        db=mock_db_session,
    )

    assert result == {"error": "File not found"}  # noqa: S101


def test_delete_file_success(mock_db_session: Session) -> None:
    """Test deleting an existing law violation file successfully."""
    mock_violation = MagicMock()
    mock_db_session.query.return_value.filter.return_value.first.return_value = (
        mock_violation
    )
    with patch(
        "app.api.endpoints.functions.law_violation_function.requests.delete",
    ) as mock_delete:
        mock_delete.return_value.status_code = SUCCESS_CODE
        result = delete_file(1, mock_db_session)
    assert result == {"message": "Collection deleted successfully"}  # noqa: S101


def test_delete_file_not_found(mock_db_session: Session) -> None:
    """Test deleting a law violation file that does not exist."""
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    result = delete_file(1, mock_db_session)

    assert result == {"error": "File not found"}  # noqa: S101
