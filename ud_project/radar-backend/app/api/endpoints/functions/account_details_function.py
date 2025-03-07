"""Functions for fetching account details from the mcmc database."""

from sqlalchemy import text
from sqlalchemy.orm import Session


def fetch_account_details_from_db(username: str, mcmc_db: Session) -> dict:
    """Fetch account details from multiple tables.

    Args:
        username: The username/user_handle to look up
        mcmc_db: MCMC database session

    Returns:
        dict: Account details dictionary with mapped field names

    """
    profile_query = text("""
        SELECT
            creator_photo_link as "profilePicUrl",
            user_following_count as "followingCount",
            user_followers_count as "followerCount",
            user_total_videos as "postCount"
        FROM ba_profile_data_asset
        WHERE user_handle = :username
        LIMIT 1
    """)

    content_query = text("""
        SELECT
            social_media_source as "socialMediaId",
            video_like_count as "likesCount",
            comment_count as "commentsCount",
            video_share_count as "shareCount",
            total_video_engagement as "enggamentCount"
        FROM ba_content_data_asset
        WHERE user_handle = :username
        LIMIT 1
    """)

    profile_result = mcmc_db.execute(profile_query, {"username": username}).first()
    content_result = mcmc_db.execute(content_query, {"username": username}).first()

    result = {}
    if profile_result:
        result.update(dict(profile_result._mapping))  # noqa: SLF001
    if content_result:
        result.update(dict(content_result._mapping))  # noqa: SLF001

    return result
