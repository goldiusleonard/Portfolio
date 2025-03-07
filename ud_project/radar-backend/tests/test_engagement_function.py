"""Unit tests for engagement calculation functions."""

import pytest

from app.api.endpoints.functions.engagement_function import (
    calculate_engagement_score,
    calculate_total_engagement,
)

# Constants for test values
TOTAL_ENGAGEMENT_RESULT = 38
NEGATIVE_TOTAL_ENGAGEMENT_RESULT = -20
ENGAGEMENT_SCORE_RESULT = 19.0
NEGATIVE_ENGAGEMENT_SCORE_RESULT = -19.0


def test_calculate_total_engagement() -> None:
    """Test the calculation of total engagement."""
    # Test with valid inputs
    result = calculate_total_engagement(10, 5, 3, 20)
    assert result == TOTAL_ENGAGEMENT_RESULT  # noqa: S101

    # Test with zero values
    result = calculate_total_engagement(0, 0, 0, 0)
    assert result == 0  # noqa: S101

    # Test with negative values (if allowed)
    result = calculate_total_engagement(-5, -3, -2, -10)
    assert result == NEGATIVE_TOTAL_ENGAGEMENT_RESULT  # noqa: S101


def test_calculate_engagement_score() -> None:
    """Test the calculation of engagement score."""
    # Test with valid inputs
    result = calculate_engagement_score(10, 5, 3, 20, 2)
    assert result == ENGAGEMENT_SCORE_RESULT  # noqa: S101

    # Test with zero video_count (should raise ValueError)
    with pytest.raises(
        ValueError,
        match="video_count cannot be zero to calculate engagement score.",
    ):
        calculate_engagement_score(10, 5, 3, 20, 0)

    # Test with zero engagement metrics
    result = calculate_engagement_score(0, 0, 0, 0, 5)
    assert result == 0.0  # noqa: S101

    # Test with negative values (if allowed)
    result = calculate_engagement_score(-10, -5, -3, -20, 2)
    assert result == NEGATIVE_ENGAGEMENT_SCORE_RESULT  # noqa: S101
