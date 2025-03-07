"""Module for handling law violation file operations."""

from datetime import datetime, timezone

import requests
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.constants import SUCCESS_CODE
from app.models.law_violation_table import LawViolation
from app.models.schemas.law_violation_schema import LawViolationData


def parse_law_effective_date(date_str: str, date_format: str = "%m-%d-%Y") -> datetime:
    """Parse a date string into a datetime object with timezone awareness."""
    try:
        if isinstance(date_str, datetime):
            return date_str

        return datetime.strptime(date_str, date_format).replace(
            tzinfo=timezone.utc,
        )
    except ValueError as e:
        error_message = (
            f"Invalid date format. Expected format: {date_format}. Error: {e}"
        )
        raise ValueError(error_message) from e


def get_law_violation_file(db: Session) -> dict:
    """Retrieve all law violation files."""
    violations = db.query(LawViolation).all()
    return {
        "data": [
            {
                "id": v.id,
                "name": v.name,
                "file_name": v.file,
                "category": v.category,
                "effective_date": v.effective_date,
                "upload_date": v.upload_date,
                "publisher": v.publisher,
                "summary": v.summary,
            }
            for v in violations
        ],
    }


def get_law_violation_file_by_id(violation_id: int, db: Session) -> dict:
    """Retrieve a specific law violation file by ID."""
    violation = db.query(LawViolation).filter(LawViolation.id == violation_id).first()
    if violation:
        return {
            "data": {
                "id": violation.id,
                "name": violation.name,
                "file_name": violation.file,
                "category": violation.category,
                "effective_date": violation.effective_date,
                "upload_date": violation.upload_date,
                "publisher": violation.publisher,
                "summary": violation.summary,
            },
        }
    return {"error": "File not found"}


def upload_file(
    law_file: UploadFile,
    law_violation_data: LawViolationData,
    db: Session,
) -> dict:
    """Upload file to the external endpoint and store collection_name alongside other data."""
    url = "http://a155f7502d7f2406087d86f8aefcac97-500080031.ap-southeast-1.elb.amazonaws.com:8077/process-document/?language=en"
    files = {"file": (law_file.filename, law_file.file.read())}
    response = requests.post(url, files=files)  # noqa: S113
    if response.status_code != SUCCESS_CODE:
        return {"message": "Failed to upload file", "error": response.text}
    payload = response.json()
    collection_name = str(payload.get("collection_name"))
    effective_date = parse_law_effective_date(law_violation_data.effective_date)
    new_violation = LawViolation(
        file=collection_name,
        name=law_violation_data.law_name,
        category=law_violation_data.category,
        effective_date=effective_date,
        publisher=law_violation_data.publisher,
        summary=law_violation_data.summary,
        is_publish=False,
    )

    db.add(new_violation)
    db.commit()
    db.refresh(new_violation)

    return {"message": "File uploaded successfully", "id": new_violation.id}


def edit_file(
    id_violation: int,
    law_violation_data: LawViolationData,
    db: Session,
) -> dict:
    """Edit details of an existing law violation file."""
    violation = db.query(LawViolation).filter(LawViolation.id == id_violation).first()
    if violation:
        violation.name = law_violation_data.law_name
        violation.category = law_violation_data.category
        violation.effective_date = parse_law_effective_date(
            law_violation_data.effective_date,
        )
        violation.upload_date = parse_law_effective_date(
            law_violation_data.upload_date,
        )
        violation.publisher = law_violation_data.publisher
        violation.summary = law_violation_data.summary
        db.commit()
        return {"message": "File updated successfully"}
    return {"error": "File not found"}


def delete_file(id_violation: int, db: Session) -> dict:
    """Delete a law violation collection by id."""
    violation = db.query(LawViolation).filter(LawViolation.id == id_violation).first()
    if not violation:
        return {"error": "File not found"}

    collection_name = violation.file

    url = f"http://a155f7502d7f2406087d86f8aefcac97-500080031.ap-southeast-1.elb.amazonaws.com:8077/collections/{collection_name}"

    response = requests.delete(url)  # noqa: S113

    if response.status_code == SUCCESS_CODE:
        db.delete(violation)
        db.commit()
        return {"message": "Collection deleted successfully"}
    return {"error": "Failed to delete collection", "details": response.text}
