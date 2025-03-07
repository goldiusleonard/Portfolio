"""User Functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import aliased
from sqlalchemy.sql import case, func

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.models.analysis_output_table import AnalysisOutput
from app.models.category_table import Category
from app.models.content_data_asset_table import BAContentDataAsset
from app.models.profile_data_asset_table import BAProfileDataAsset


def get_heatmap_by_username(
    username: str,
    db: Session,
) -> dict:
    """Retrieve a heatmap and profile details for a given username.

    Args:
        username (str): The username of the profile to retrieve the heatmap for.
        db (Session): The database session to use for queries.

    Returns:
        dict: A dictionary containing the profile details and heatmap data. The dictionary includes:
            - id (str): The unique identifier of the profile.
            - creator (dict): A dictionary containing details about the profile creator, including:
                - name (str): The name of the creator.
                - engagement (int): The engagement count of the creator.
                - following (int): The number of users the creator is following.
                - followers (int): The number of followers the creator has.
                - posts (int): The number of posts the creator has made.
                - lastPostDate (str): The date of the creator's last post.
                - profilePicture (str): The URL of the creator's profile picture.
                - categories (list): A list of categories associated with the creator.
                - chartData (dict): A dictionary containing heatmap data, including:
                    - total (int): The total count of activities in the heatmap.
                    - creator_id (str): The unique identifier of the creator.
                    - calendar (list): A list of calendar data points representing the heatmap.

    """
    calendar = get_heatmap_calendar_by_username(username, db).get("calendar", [])

    profile_details = get_profile_details(username, db)
    categories = get_categories_by_username(username, db)

    return {
        "id": profile_details["id"],
        "creator": {
            "name": profile_details["name"],
            "engagement": profile_details["engagement"],
            "following": profile_details["following"],
            "followers": profile_details["followers"],
            "posts": profile_details["posts"],
            "lastPostDate": profile_details["lastPostDate"],
            "profilePicture": profile_details["profilePicture"],
            "categories": categories,
            "chartData": {
                "total": sum(item.get("count", 0) for item in calendar),
                "creator_id": profile_details["creator_id"],
                "calendar": calendar,
            },
        },
    }


def get_categories_by_username(username: str, db: Session) -> list:
    """Retrieve a list of categories associated with a given username, along with their risk status and count.

    Args:
        username (str): The username for which to retrieve the categories.
        db (Session): The database session to execute the query.

    Returns:
        list: A list of dictionaries, each containing the category name, risk status, and count.

    """
    bca = aliased(BAContentDataAsset)
    ao = aliased(AnalysisOutput)
    c = aliased(Category)

    category_risk_subquery = (
        db.query(
            c.category_name,
            func.lower(ao.risk_status).label("risk_status"),
            func.count().over(partition_by=c.category_name).label("category_count"),
            func.row_number()
            .over(
                partition_by=c.category_name,
                order_by=case(
                    (func.lower(ao.risk_status) == "high", 1),
                    (func.lower(ao.risk_status) == "medium", 2),
                    (func.lower(ao.risk_status) == "low", 3),
                    (func.lower(ao.risk_status) == "irrelevant", 4),
                    else_=5,
                ),
            )
            .label("rn"),
        )
        .select_from(bca)
        .outerjoin(ao, ao.video_id == bca.video_id)
        .outerjoin(c, c.id == ao.category_id)
        .filter(bca.user_handle == username)
        .subquery()
    )

    results = (
        db.query(
            category_risk_subquery.c.category_name,
            func.coalesce(category_risk_subquery.c.risk_status, "unknown").label(
                "risk_status",
            ),
            category_risk_subquery.c.category_count,
        )
        .filter(category_risk_subquery.c.rn == 1)
        .all()
    )

    return [
        {
            "name": row.category_name,
            "risk": row.risk_status,
            "count": row.category_count,
        }
        for row in results
    ]


def get_profile_details(username: str, db: Session) -> dict:
    """Retrieve profile details for a given username from the database.

    Args:
        username (str): The username to search for in the database.
        db (Session): The database session to execute the query.

    Returns:
        dict: A dictionary containing the profile details. If no profile is found,
        returns a dictionary with default values.
              The dictionary includes the following keys:
                - id: The profile ID.
                - name: The user handle.
                - engagement: The profile engagement score.
                - following: The number of users the profile is following.
                - followers: The number of followers the profile has.
                - posts: The total number of videos posted by the user.
                - lastPostDate: The date of the latest post.
                - profilePicture: The link to the profile picture.
                - creator_id: The profile API ID.

    """
    profile = (
        db.query(
            BAProfileDataAsset.id,
            BAProfileDataAsset.user_handle,
            BAProfileDataAsset.profile_engagement_score,
            BAProfileDataAsset.user_following_count,
            BAProfileDataAsset.user_followers_count,
            BAProfileDataAsset.user_total_videos,
            BAProfileDataAsset.latest_posted_date,
            BAProfileDataAsset.creator_photo_link,
            BAProfileDataAsset.profile_api_id,
        )
        .filter(
            func.lower(BAProfileDataAsset.user_handle).like(f"%{username.lower()}%"),
        )
        .first()
    )

    if not profile:
        return {
            "id": 0,
            "name": "",
            "engagement": "0%",
            "following": "0",
            "followers": "0",
            "posts": "0",
            "lastPostDate": "",
            "profilePicture": "",
            "creator_id": "",
        }

    return {
        "id": f"{profile.id}" if profile.id else "",
        "name": profile.user_handle if profile.user_handle else "",
        "engagement": f"{profile.profile_engagement_score}"
        if profile.profile_engagement_score
        else "0",
        "following": f"{profile.user_following_count}"
        if profile.user_following_count
        else "0",
        "followers": f"{profile.user_followers_count}"
        if profile.user_followers_count
        else "0",
        "posts": f"{profile.user_total_videos:,}" if profile.user_total_videos else "0",
        "lastPostDate": profile.latest_posted_date.strftime("%Y-%m-%d")
        if profile.latest_posted_date
        else "",
        "profilePicture": profile.creator_photo_link
        if profile.creator_photo_link
        else "",
        "creator_id": profile.profile_api_id if profile.profile_api_id else "",
    }


def get_heatmap_calendar_by_username(username: str, db: Session) -> dict:
    """Retrieve a heatmap calendar for a specific user based on their username.

    Args:
        username (str): The username of the user for whom the heatmap calendar is to be retrieved.
        db (Session): The database session used to execute the query.

    Returns:
        dict: A dictionary containing the heatmap calendar data in the format:
              {"calendar": [{"date": str, "count": int}, ...]}
              where each entry represents a date and the count of videos posted on that date.

    """
    result = [
        {"date": row[0], "count": row[1]}
        for row in db.query(
            func.date(BAContentDataAsset.video_posted_timestamp),
            func.count(),
        )
        .outerjoin(
            AnalysisOutput,
            AnalysisOutput.video_id == BAContentDataAsset.video_id,
        )
        .filter(BAContentDataAsset.user_handle == username)
        .group_by(func.date(BAContentDataAsset.video_posted_timestamp))
        .order_by(func.date(BAContentDataAsset.video_posted_timestamp))
        .all()
    ]
    return {"calendar": result}
