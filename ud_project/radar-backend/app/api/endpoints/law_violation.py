"""Law endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.endpoints.functions import law_violation_function
from app.core.dependencies import get_db
from app.models.schemas.law_violation_schema import (
    EditFileDetailsRequest,
    LawViolationData,
    LawViolationDataEdit,
)

law_violation_module = APIRouter()


@law_violation_module.get("/law_violation_files")
def get_law_violation_file(
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve all law violation files."""
    return law_violation_function.get_law_violation_file(db)


@law_violation_module.get("/law_violation_file/{id_violation}")
def get_law_violation_file_by_id(
    id_violation: int,
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve a specific law violation file by ID."""
    return law_violation_function.get_law_violation_file_by_id(id_violation, db)


def get_law_violation_data(
    law_name: Annotated[str, Form(...)],
    category: Annotated[str, Form(...)],
    effective_date: Annotated[str, Form(...)],
    publisher: Annotated[str, Form(...)],
    summary: Annotated[str, Form(...)],
) -> LawViolationData:
    """Dependency to parse form data into LawViolationData."""
    return LawViolationData(
        law_name=law_name,
        category=category,
        effective_date=effective_date,
        publisher=publisher,
        summary=summary,
    )


@law_violation_module.post("/upload_file")
def upload_file(
    law_violation_data: LawViolationData = Depends(get_law_violation_data),
    law_file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """Upload a new law violation file with date validation."""
    try:
        # Parse and validate the effective date
        return law_violation_function.upload_file(
            law_file,
            law_violation_data,
            db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@law_violation_module.put("/edit_file_details/{id_violation}")
def edit_file_details(
    id_violation: int,
    request: EditFileDetailsRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Edit details of an existing law violation file with date validation."""
    try:
        effparsed_date = law_violation_function.parse_law_effective_date(
            request.effective_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        upparsed_date = law_violation_function.parse_law_effective_date(
            request.upload_date,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    law_violation_data = LawViolationDataEdit(
        law_name=request.law_name,
        category=request.category,
        effective_date=effparsed_date,
        upload_date=upparsed_date,
        publisher=request.publisher,
        summary=request.summary,
    )

    return law_violation_function.edit_file(
        id_violation,
        law_violation_data,
        db,
    )


@law_violation_module.delete("/delete_file/{id_violation}")
def delete_file(
    id_violation: int,
    db: Session = Depends(get_db),
) -> dict:
    """Delete a law violation file."""
    return law_violation_function.delete_file(id_violation, db)
