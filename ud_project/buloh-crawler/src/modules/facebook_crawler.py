import os
import time
import json
import requests
from fastapi import Query, APIRouter
from ..crawlers.facebook.base import FacebookCrawler
from typing import Dict, Any, List

router = APIRouter()

facebook_crawler = FacebookCrawler()

@router.get("/group")
def get_facebook_group_data(
    group_handle: str = Query(..., description="Facebook group handle or ID"),
):
    result = facebook_crawler.scrape_facebook_group(group_handle)

    if result is None:
        return {
            ""
        }

    return result


@router.get("/page")
def get_facebook_page_data(
    page_handle: str = Query(..., description="Facebook page handle or ID"),
):
    url = f"https://www.facebook.com/{page_handle}/"
    result = fetch_facebook_data(url, "facebook-page")
    if result:
        return standardize_page_data(result, "crawlbase")

    apify_result = fallback_scrape_page(page_handle)
    if isinstance(apify_result, list):
        for res_idx, res in enumerate(apify_result):
            apify_result[res_idx] = standardize_page_data(res, "apify")

        return apify_result

    return standardize_page_data(apify_result, "scrapingbot")


@router.get("/profile")
def get_facebook_profile_data(
    username: str = Query(..., description="Facebook username or ID"),
):
    url = f"https://www.facebook.com/{username}"
    result = fetch_facebook_data(url, "facebook-profile")
    if result:
        return standardize_profile_data(result, "crawlbase")

    apify_result = fallback_scrape_profile(username)
    if isinstance(apify_result, list):
        for res_idx, res in enumerate(apify_result):
            apify_result[res_idx] = standardize_profile_data(res, "apify")

        return apify_result

    return standardize_profile_data(apify_result, "scrapingbot")


@router.get("/hashtag")
def get_facebook_hashtag_posts(
    hashtag: str = Query(..., description="Facebook hashtag without # symbol"),
):
    url = f"https://www.facebook.com/hashtag/{hashtag}"

    result = fetch_facebook_data(url, "facebook-hashtag")
    if result:
        return standardize_hashtag_data(result, "crawlbase")

    apify_result = fallback_scrape_hashtag(hashtag)
    if isinstance(apify_result, list):
        for res_idx, res in enumerate(apify_result):
            apify_result[res_idx] = standardize_hashtag_data(res, "apify")

        return apify_result

    return standardize_hashtag_data(apify_result, "scrapingbot")


# Define standard keys that we want in the output
STANDARD_POST_KEYS = {
    "id": "",
    "text": "",
    "user_name": "",
    "url": "",
    "timestamp": "",
    "likes": 0,
    "shares": 0,
    "comments": 0,
    "hashtags": [],
    "media": [],
}

STANDARD_PROFILE_KEYS = {
    "name": "",
    "bio": "",
    "profile_image": "",
    "cover_image": "",
    "friend_count": 0,
    "other_profiles": [],
    "work": [],
    "education": [],
    "photos": [],
}

# Extended API mappings for all data types
API_MAPPINGS = {
    "crawlbase": {
        # Post mappings
        "userName": "user_name",
        "text": "text",
        "url": "url",
        "dateTime": "timestamp",
        "likesCount": "likes",
        "sharesCount": "shares",
        "commentsCount": "comments",
        "links": "hashtags",
        # Profile mappings
        "name": "name",
        "bio": "bio",
        "profileImage": "profile_image",
        "coverImage": "cover_image",
        "friendCount": "friend_count",
        "othersWithName": "other_profiles",
        # Page and Group mappings
        "title": "title",
        "type": "type",
        "membersCount": "members_count",
        "description": "description",
        "image": "image",
        "feeds": "posts",
    },
    "apify": {
        # Post mappings
        "author": "user_name",
        "content": "text",
        "postUrl": "url",
        "created_time": "timestamp",
        "reactions_count": "likes",
        "shares_count": "shares",
        "comments_count": "comments",
        "hashtags": "hashtags",
        # Profile mappings
        "fullName": "name",
        "aboutInfo": "bio",
        "profilePicture": "profile_image",
        "coverPicture": "cover_image",
        "friendsCount": "friend_count",
        "similarProfiles": "other_profiles",
        # Page and Group mappings
        "pageTitle": "title",
        "pageType": "type",
        "subscriberCount": "members_count",
        "pageDescription": "description",
        "pageImage": "image",
        "posts": "posts",
    },
    "scrapingbot": {
        # Post mappings
        "user_name": "user_name",
        "message": "text",
        "link": "url",
        "date": "timestamp",
        "likes": "likes",
        "shares": "shares",
        "comments": "comments",
        "tags": "hashtags",
        # Profile mappings
        "userName": "name",
        "userBio": "bio",
        "profileImg": "profile_image",
        "coverImg": "cover_image",
        "friends": "friend_count",
        "similarUsers": "other_profiles",
        # Page and Group mappings
        "pageName": "title",
        "pageCategory": "type",
        "followerCount": "members_count",
        "pageInfo": "description",
        "pageImg": "image",
        "feed": "posts",
    },
}


def standardize_hashtag_data(data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Standardizes hashtag data from any source into a consistent format.

    Args:
        data: Raw data from the API
        source: API source ('crawlbase', 'apify', or 'scrapingbot')

    Returns:
        Dict with standardized keys
    """
    if source not in API_MAPPINGS:
        raise ValueError(f"Unsupported source: {source}")

    mapping = API_MAPPINGS[source]

    # Initialize standard structure
    standardized: dict = {"hashtag": "", "posts": []}

    # Extract hashtag and posts
    if isinstance(data, dict):
        standardized["hashtag"] = data.get("hashtag", "")
        posts = data.get("posts", [])
    else:
        posts = data if isinstance(data, list) else []

    # Standardize each post
    for post in posts:
        standardized_post = STANDARD_POST_KEYS.copy()

        # Map keys according to standard format
        for old_key, new_key in mapping.items():
            if old_key in post:
                standardized_post[new_key] = post[old_key]

        standardized["posts"].append(standardized_post)

    return standardized


def standardize_profile_data(data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Standardizes profile data from any source into a consistent format.

    Args:
        data: Raw data from the API
        source: API source ('crawlbase', 'apify', or 'scrapingbot')

    Returns:
        Dict with standardized keys
    """
    if not isinstance(data, dict):
        raise ValueError("Invalid data format. Expected a dictionary.")

    if source not in API_MAPPINGS:
        raise ValueError(f"Unsupported source: {source}")

    mapping = API_MAPPINGS[source]

    # Initialize with explicit typing for lists
    standardized: Dict[str, Any] = {
        "name": "",
        "bio": "",
        "profile_image": "",
        "cover_image": "",
        "friend_count": 0,
        "work": [],
        "education": [],
        "photos": [],
        "other_profiles": [],
    }

    # Map basic fields using source-specific mappings
    for api_key, std_key in mapping.items():
        if api_key in data and std_key in standardized:
            standardized[std_key] = data.get(api_key, standardized[std_key])

    # Handle nested structures like work and education
    about_sections = data.get("about", [])
    if isinstance(about_sections, list):
        for section in about_sections:
            if not isinstance(section, dict):
                continue

            section_type = section.get("type")
            if section_type == "Work":
                work_items: List[Dict[str, str]] = []
                for item in section.get("items", []):
                    if isinstance(item, dict):
                        work_items.append(
                            {
                                "organization": str(item.get("organisation", "")),
                                "url": str(item.get("page_url", "")),
                            }
                        )
                standardized["work"] = work_items
            elif section_type in ["College", "High School"]:
                items = section.get("items", [])
                if isinstance(items, list):
                    education_list: List[Dict[str, str]] = standardized["education"]
                    for item in items:
                        if isinstance(item, dict):
                            new_entry = {
                                "institution": str(item.get("organisation", "")),
                                "url": str(item.get("page_url", "")),
                            }
                            # Check for duplicates using explicit list comprehension
                            existing_entries = [
                                entry
                                for entry in education_list
                                if (
                                    isinstance(entry, dict)
                                    and entry.get("institution")
                                    == new_entry["institution"]
                                    and entry.get("url") == new_entry["url"]
                                )
                            ]

                            if not existing_entries:
                                education_list.append(new_entry)

    # Ensure numeric values are properly typed
    friend_count = standardized.get("friend_count")
    try:
        if isinstance(friend_count, (int, float, str)):
            standardized["friend_count"] = int(float(str(friend_count)))
        else:
            standardized["friend_count"] = 0
    except (ValueError, TypeError):
        standardized["friend_count"] = 0

    return standardized


def standardize_page_data(data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """
    Standardizes page data from any source into a consistent format.
    """
    if source not in API_MAPPINGS:
        raise ValueError(f"Unsupported source: {source}")

    mapping = API_MAPPINGS[source]
    standardized = {
        "title": "",
        "type": "",
        "members_count": 0,
        "url": "",
        "description": "",
        "image": "",
        "posts": [],
    }

    # Map basic fields using source-specific mappings
    for api_key, std_key in mapping.items():
        if api_key in data and std_key in standardized:
            standardized[std_key] = data.get(api_key, standardized[std_key])

    # Handle posts
    posts_key = mapping.get("feeds", "posts")  # Default to "posts" if no mapping
    posts = data.get(posts_key, [])
    standardized_posts = []

    if isinstance(posts, list):
        for post in posts:
            if isinstance(post, dict):
                standardized_post = STANDARD_POST_KEYS.copy()
                for api_key, std_key in mapping.items():
                    if api_key in post and std_key in standardized_post:
                        standardized_post[std_key] = post.get(
                            api_key, standardized_post[std_key]
                        )

                # Ensure numeric values are integers
                for key in ["likes", "shares", "comments"]:
                    value = standardized_post.get(key)
                    try:
                        if isinstance(value, (int, float, str)):
                            standardized_post[key] = int(float(str(value)))
                        else:
                            standardized_post[key] = 0
                    except (ValueError, TypeError):
                        standardized_post[key] = 0

                images = post.get("images", [])
                standardized_post["media"] = (
                    list(images) if isinstance(images, list) else []
                )
                standardized_posts.append(standardized_post)

    standardized["posts"] = standardized_posts

    # Ensure numeric values are properly typed
    members_count = standardized.get("members_count")
    try:
        if isinstance(members_count, (int, float, str)):
            standardized["members_count"] = int(float(str(members_count)))
        else:
            standardized["members_count"] = 0
    except (ValueError, TypeError):
        standardized["members_count"] = 0

    return standardized



