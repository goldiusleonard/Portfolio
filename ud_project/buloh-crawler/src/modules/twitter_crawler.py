from typing import Union

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from ..twitter_crawler.apify import get_recent_tweets_apify, get_user_details_apify
from ..twitter_crawler.tweepy import get_recent_tweets_tweepy, get_user_details_tweepy
from ..utils.standardizer import standardize_tweets, standardize_profile

load_dotenv()

router = APIRouter()


@router.get(
    "/tweets",
    summary="Search recent tweets",
    description="Fetch recent tweets based on a query.",
)
def get_recent_tweets(
    query: str,
    start_time: Union[str, None] = None,
    end_time: Union[str, None] = None,
    max_results: int = 10,
):
    """
    Search for recent tweets using a query string.

    Args:
        query (str): The search keyword or hashtag.
        start_time (str): The start time filter for searching.
        end_time (str): The end time filter for searching.
        max_results (int): The number of tweets to retrieve (max 100).

    Return:
        tweets: list
    """
    tweets, source = get_recent_tweets_tweepy(
        query,
        start_time,
        end_time,
        max_results,
    )

    # Fallback to Apify
    if (
        tweets is None
        or tweets["tweets"] == "No tweets found for the given query"
        or "Error retrieving tweets: " in tweets["tweets"]
    ):
        tweets, source = get_recent_tweets_apify(
            query,
            start_time,
            end_time,
            max_results,
        )

    if (
        tweets is None
        or tweets["tweets"] == "No tweets found for the given query"
        or "Error retrieving tweets: " in tweets["tweets"]
    ):
        raise HTTPException(status_code=500, detail="No Tweets Retrieved")

    tweets = standardize_tweets(tweets, source)

    return tweets


@router.get(
    "/user",
    summary="Get Twitter user details",
    description="Fetch details of a Twitter user by username.",
)
def get_user_details(
    username: str,
):
    """
    Search for recent tweets using a query string.

    Args:
        username (str): The x/twitter username to search.
        start_time (str): The start time filter for searching.
        end_time (str): The end time filter for searching.
        max_results (int): The number of tweets to retrieve (max 100).

    Return:
        tweets: list
    """
    user_detail, source = get_user_details_tweepy(
        username,
    )

    # Fallback to Apify
    if (
        user_detail is None
        or user_detail["user_detail"] == "User not found."
        or "Error retrieving user details: " in user_detail["user_detail"]
    ):
        user_detail, source = get_user_details_apify(
            username,
        )

    if (
        user_detail is None
        or user_detail["user_detail"] == "User not found."
        or "Error retrieving user details: " in user_detail["user_detail"]
    ):
        raise HTTPException(status_code=500, detail="No User Detail Retrieved")

    user_detail = standardize_profile(user_detail, source)

    return user_detail
