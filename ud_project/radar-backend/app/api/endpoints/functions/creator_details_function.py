"""Creator Details Functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import aliased
from sqlalchemy.sql import case, func

from app.enums.risk import Risk

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.models.analysis_output_table import AnalysisOutput
from app.models.category_table import Category


def get_category_post_status(db: Session) -> dict:
    """Get the category post status."""
    ranked_counts = (
        db.query(
            Category.category_name,
            func.sum(func.count(Category.category_name))
            .over(partition_by=Category.category_name)
            .label("value"),
            (
                func.count(Category.category_name)
                / func.sum(func.count(Category.category_name)).over(
                    partition_by=Category.category_name,
                )
            ).label("count_ratio"),
            func.row_number()
            .over(
                partition_by=Category.category_name,
                order_by=func.count(Category.category_name).desc(),
            )
            .label("rank"),
        )
        .join(AnalysisOutput, AnalysisOutput.category_id == Category.id, isouter=True)
        .group_by(Category.category_name, AnalysisOutput.risk_status)
        .subquery()
    )

    ranked_counts_alias = aliased(ranked_counts)

    results = (
        db.query(
            ranked_counts_alias.c.category_name,
            ranked_counts_alias.c.value,
            ranked_counts_alias.c.count_ratio,
            case(
                (ranked_counts_alias.c.count_ratio > 0.5, Risk.HIGH.value),  # noqa: PLR2004
                (ranked_counts_alias.c.count_ratio > 0.25, Risk.MEDIUM.value),  # noqa: PLR2004
                else_=Risk.LOW.value,
            ).label("ratio_category"),
        )
        .filter(ranked_counts_alias.c.rank == 1)
        .all()
    )

    data = [
        {
            "title": row.category_name,
            "value": row.value,
            "count_ratio": f"{row.count_ratio*100:.2f}%",
            "risk": row.ratio_category,
        }
        for row in results
    ]

    return {"data": data}
