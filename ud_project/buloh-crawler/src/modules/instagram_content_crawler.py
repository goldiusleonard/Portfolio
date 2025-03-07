from fastapi import APIRouter, HTTPException
from apify_client import ApifyClient
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional
from ..utils import Logger
from ..crawlers.instagram.post import (
    extract_fields_from_instaloader_for_post,
    extract_fields_from_apify_for_post,
    extract_fields_from_apify_for_post_url,
)
from ..crawlers.instagram.profile import (
    extract_fields_from_instaloader_for_profile,
    extract_fields_from_apify_for_profile,
    extract_fields_from_apify_for_profile_url,
)
from ..crawlers.instagram.comment import (
    extract_fields_from_instaloader_for_comments,
    extract_fields_from_apify_for_comments,
)
import instaloader
import logging
import json
import os


log = Logger(name="database_logger")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter()

user = os.getenv("INSTAGRAM_USERNAME")
csrftoken = os.getenv("INSTAGRAM_CSRFTOKEN")
sessionid = os.getenv("INSTAGRAM_SESSIONID")
ds_user_id = os.getenv("INSTAGRAM_DS_USER_ID")
mid = os.getenv("INSTAGRAM_MID")
ig_did = os.getenv("INSTAGRAM_IG_DID")
apify_api_token = os.getenv("INSTAGRAM_APIFY_API_TOKEN")


@router.get("/profile")
def get_instagram_profile(username: str):
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        compress_json=False,
        download_comments=False,
        save_metadata=True,
        post_metadata_txt_pattern="",
    )

    loader.load_session(
        user,
        {
            "csrftoken": csrftoken,
            "sessionid": sessionid,
            "ds_user_id": ds_user_id,
            "mid": mid,
            "ig_did": ig_did,
        },
    )

    try:
        loader.download_profile(
            profile_name=username,
            profile_pic=False,
        )

        folder_path = f"./{username}/"
        if os.path.exists(folder_path):
            for file_name in os.listdir(folder_path):
                if file_name.startswith(username) and file_name.endswith(".json"):
                    file_path = os.path.join(folder_path, file_name)
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        profile_data = extract_fields_from_instaloader_for_profile(data)
                    os.remove(file_path)
                elif file_name.endswith("_UTC.json"):
                    file_path = os.path.join(folder_path, file_name)
                    os.remove(file_path)
                elif file_name.endswith("_profile_pic.jpg"):
                    file_path = os.path.join(folder_path, file_name)
                    os.remove(file_path)
                elif file_name.endswith("id"):
                    file_path = os.path.join(folder_path, file_name)
                    os.remove(file_path)

        return {"profile": profile_data}

    except Exception as e:
        logger.info(f"Instaloader failed: {e}, trying Apify instead...")

        # Fallback to Apify
        client = ApifyClient(apify_api_token)
        run_profile_input = {"usernames": [username]}

        try:
            run = client.actor("apify/instagram-profile-scraper").call(
                run_input=run_profile_input
            )

            for data in client.dataset(run["defaultDatasetId"]).iterate_items():
                profile_data = extract_fields_from_apify_for_profile(data)

            return {
                "profile": profile_data,
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch data from both sources. Error: {str(e)}",
            )


@router.get("/posts")
def get_instagram_posts(
    username: str,
    max_posts: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        compress_json=False,
        download_comments=True,
        save_metadata=True,
        post_metadata_txt_pattern="",
    )

    loader.load_session(
        user,
        {
            "csrftoken": csrftoken,
            "sessionid": sessionid,
            "ds_user_id": ds_user_id,
            "mid": mid,
            "ig_did": ig_did,
        },
    )

    try:
        if start_date and end_date:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%SZ")

            loader.download_profile(
                profile_name=username,
                profile_pic=False,
                post_filter=lambda post: start_date_dt <= post.date_utc <= end_date_dt,
            )
        elif start_date:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")

            loader.download_profile(
                profile_name=username,
                profile_pic=False,
                post_filter=lambda post: post.date_utc >= start_date_dt,
            )
        else:
            loader.download_profile(profile_name=username, profile_pic=False)

        posts_data = []
        comments_data = []

        folder_path = f"./{username}/"
        if os.path.exists(folder_path):
            posts_files = [
                file for file in os.listdir(folder_path) if file.endswith("_UTC.json")
            ]
            comments_files = [
                file
                for file in os.listdir(folder_path)
                if file.endswith("_UTC_comments.json")
            ]

            for file_name in os.listdir(folder_path):
                if file_name.startswith(username) and file_name.endswith(".json"):
                    file_path = os.path.join(folder_path, file_name)
                    os.remove(file_path)

            for file_name in posts_files:
                file_path = os.path.join(folder_path, file_name)
                with open(file_path, "r") as file:
                    data = json.load(file)
                    extracted_data = extract_fields_from_instaloader_for_post(data)
                    posts_data.append(extracted_data)
                os.remove(file_path)

            for file_name in comments_files:
                file_path = os.path.join(folder_path, file_name)
                with open(file_path, "r") as file:
                    data = json.load(file)
                    extracted_data = extract_fields_from_instaloader_for_comments(data)
                    comments_data.append(extracted_data)
                os.remove(file_path)

            file_path = os.path.join(folder_path, "id")
            if os.path.exists(file_path):
                os.remove(file_path)

        return {"posts": posts_data, "comments": comments_data}

    except Exception as e:
        logger.info(f"Instaloader failed: {e}, trying Apify instead...")

        # Fallback to Apify
        client = ApifyClient(apify_api_token)
        run_post_input = {
            "directUrls": [f"https://www.instagram.com/{username}/"],
            "resultsType": "posts",
            "resultsLimit": max_posts,
            "addParentData": True,
        }

        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
            start_date_str = start_date_obj.strftime("%Y-%m-%d")
            run_post_input["onlyPostsNewerThan"] = start_date_str

        try:
            run = client.actor("apify/instagram-api-scraper").call(
                run_input=run_post_input
            )

            posts_data = []
            comments_data = []
            for post in client.dataset(run["defaultDatasetId"]).iterate_items():
                extracted_post_data = extract_fields_from_apify_for_post(post)
                posts_data.append(extracted_post_data)

                extracted_comments_data = extract_fields_from_apify_for_comments(post)
                comments_data.append(extracted_comments_data)

            return {
                "posts": posts_data,
                "comments": comments_data,
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch data from both sources. Error: {str(e)}",
            )


@router.get("/trending/hashtags")
def get_instagram_trending_hashtags(maxHashtags: int):
    client = ApifyClient(apify_api_token)
    run_profile_input = {"country": "MY", "maxHashtags": maxHashtags}

    try:
        run = client.actor("hung.ad4gate/intagram-trend-crawler-pay-per-result").call(
            run_input=run_profile_input
        )

        hashtags_data = []
        for data in client.dataset(run["defaultDatasetId"]).iterate_items():
            hashtags_data.append(data)

        return {
            "hashtags": hashtags_data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data. Error: {str(e)}",
        )


@router.get("/trending/posts/search/by-hashtag")
def get_instagram_posts_search_by_hashtag(
    hashtag: str, start_date: Optional[str] = None
):
    client = ApifyClient(apify_api_token)
    run_top_post_input = {
        "addParentData": True,
        "enhanceUserSearchWithFacebookPage": False,
        "isUserReelFeedURL": False,
        "isUserTaggedFeedURL": False,
        "search": hashtag,
        "searchLimit": 1,
        "resultsType": "posts",
        "searchType": "hashtag",
    }

    if start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
        start_date_dt = start_date_obj.strftime("%Y-%m-%d")
        run_top_post_input["onlyPostsNewerThan"] = start_date_dt

    try:
        run = client.actor("apify/instagram-api-scraper").call(
            run_input=run_top_post_input
        )

        posts_url = []
        for result in client.dataset(run["defaultDatasetId"]).iterate_items():
            posts_url = extract_fields_from_apify_for_post_url(result)

        run_post_input = {
            "addParentData": True,
            "directUrls": posts_url,
            "enhanceUserSearchWithFacebookPage": False,
            "isUserReelFeedURL": False,
            "isUserTaggedFeedURL": False,
            "resultsType": "posts",
        }

        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
            start_date_dt = start_date_obj.strftime("%Y-%m-%d")
            run_post_input["onlyPostsNewerThan"] = start_date_dt

        run = client.actor("apify/instagram-api-scraper").call(run_input=run_post_input)

        posts_data = []
        comments_data = []
        for post in client.dataset(run["defaultDatasetId"]).iterate_items():
            extracted_post_data = extract_fields_from_apify_for_post(post)
            posts_data.append(extracted_post_data)

            extracted_comments_data = extract_fields_from_apify_for_comments(post)
            comments_data.append(extracted_comments_data)

        return {
            "posts": posts_data,
            "comments": comments_data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data. Error: {str(e)}",
        )


@router.get("/posts/search/by-username")
def get_instagram_posts_search_by_username(
    username: str,
    max_username: int,
    max_posts_per_username: int,
    start_date: Optional[str] = None,
):
    client = ApifyClient(apify_api_token)
    run_top_post_input = {
        "addParentData": True,
        "enhanceUserSearchWithFacebookPage": False,
        "isUserReelFeedURL": False,
        "isUserTaggedFeedURL": False,
        "search": username,
        "searchLimit": max_username,
        "searchType": "user",
    }

    if start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
        start_date_dt = start_date_obj.strftime("%Y-%m-%d")
        run_top_post_input["onlyPostsNewerThan"] = start_date_dt

    try:
        run = client.actor("apify/instagram-api-scraper").call(
            run_input=run_top_post_input
        )

        user_url = []
        for result in client.dataset(run["defaultDatasetId"]).iterate_items():
            url = extract_fields_from_apify_for_profile_url(result)
            user_url.append(url)

        run_post_input = {
            "addParentData": True,
            "directUrls": user_url,
            "enhanceUserSearchWithFacebookPage": False,
            "isUserReelFeedURL": False,
            "isUserTaggedFeedURL": False,
            "resultsType": "posts",
            "resultsLimit": max_posts_per_username,
        }

        if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
            start_date_dt = start_date_obj.strftime("%Y-%m-%d")
            run_post_input["onlyPostsNewerThan"] = start_date_dt

        run = client.actor("apify/instagram-api-scraper").call(run_input=run_post_input)

        posts_data = []
        comments_data = []
        for post in client.dataset(run["defaultDatasetId"]).iterate_items():
            extracted_post_data = extract_fields_from_apify_for_post(post)
            posts_data.append(extracted_post_data)

            extracted_comments_data = extract_fields_from_apify_for_comments(post)
            comments_data.append(extracted_comments_data)

        return {
            "posts": posts_data,
            "comments": comments_data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data. Error: {str(e)}",
        )
