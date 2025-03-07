"""Engagement Functions."""

from __future__ import annotations


def calculate_total_engagement(
    share_count: int,
    saved_count: int,
    comment_count: int,
    like_count: int,
) -> int:
    """Calculate total engagement by summing up all engagement metrics.

    Args:
        share_count (int): Number of shares.
        saved_count (int): Number of saves.
        comment_count (int): Number of comments.
        like_count (int): Number of likes.

    Returns:
        int: Total engagement score.

    """
    return share_count + saved_count + comment_count + like_count


def calculate_engagement_score(
    share_count: int,
    saved_count: int,
    comment_count: int,
    like_count: int,
    video_count: int,
) -> float:
    """Calculate the engagement score based on various interaction metrics.

    Args:
        share_count (int): The number of times the content was shared.
        saved_count (int): The number of times the content was saved.
        comment_count (int): The number of comments on the content.
        like_count (int): The number of likes on the content.
        video_count (int): The number of videos associated with the content.

    Returns:
        float: The calculated engagement score.

    Raises:
        ValueError: If video_count is zero, as it would result in division by zero.

    """
    if video_count == 0:
        error_msg = "video_count cannot be zero to calculate engagement score."
        raise ValueError(error_msg)
    return (share_count + saved_count + comment_count + like_count) / video_count
