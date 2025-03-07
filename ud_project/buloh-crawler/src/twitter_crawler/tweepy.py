import datetime
import os
import traceback
import tweepy
from typing import Union, Tuple

from dotenv import load_dotenv

load_dotenv()

tweepy_bearer_token: str = os.getenv("TWEEPY_BEARER_TOKEN", "")
if tweepy_bearer_token == "":
    raise ValueError("Bearer token is not valid!")

# Initialize Tweepy Client
tweepy_client = tweepy.Client(bearer_token=tweepy_bearer_token, wait_on_rate_limit=True)


def get_recent_tweets_tweepy(
    query: str,
    start_time: Union[str, None],
    end_time: Union[str, None],
    max_results: int = 10,
) -> Tuple[dict, str]:
    def format_date(date_str):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")  # Ensure correct format
        except ValueError:
            raise ValueError(
                f"Invalid date format: {date_str}. Use 'YYYY-MM-DDTHH:mm:ssZ'."
            )

    try:
        # Prepare request parameters
        params = {
            "query": query,
            "max_results": max_results,
            "sort_order": "recency",
            "tweet.fields": [
                "article",
                "attachments",
                "author_id",
                "card_uri",
                "community_id",
                "context_annotations",
                "conversation_id",
                "created_at",
                "display_text_range",
                "edit_controls",
                "edit_history_tweet_ids",
                "entities",
                "geo",
                "id",
                "in_reply_to_user_id",
                "lang",
                "media_metadata",
                "non_public_metrics",
                "note_tweet",
                "organic_metrics",
                "possibly_sensitive",
                "promoted_metrics",
                "public_metrics",
                "referenced_tweets",
                "reply_settings",
                "scopes",
                "source",
                "text",
                "withheld",
            ],
        }

        # Add optional parameters only if provided
        if start_time:
            params["start_time"] = format_date(start_time)
        if end_time:
            params["end_time"] = format_date(end_time)

        tweets = tweepy_client.search_all_tweets(**params)

        if not tweets.data:
            print(traceback.format_exc())
            return {"tweets": "No tweets found for the given query."}, "tweepy"
            # raise HTTPException(
            #     status_code=404, detail="No tweets found for the given query."
            # )

        response = [
            {
                "id": tweet.id,
                "text": tweet.text,
                "author_id": tweet.author_id,
                "created_at": tweet.created_at,
                "username": tweet.username,
            }
            for tweet in tweets.data
        ]

        # with open("/Users/goldiusleonard/Documents/new_code/buloh-crawler/tweepy_output.json", "w") as f:
        #     json.dump({"tweets": response}, f)

        return {"tweets": response}, "tweepy"

    except Exception as e:
        print(traceback.format_exc())
        return {"tweets": f"Error retrieving tweets: {str(e)}"}, "tweepy"


# get_recent_tweets_tweepy Sample Output
# {
#     "tweets": [
#         {
#             "id": "1346889436626259968",
#             "text": "Learn how to use the user Tweet timeline and user mention timeline endpoints in the X API v2 to explore Tweet https://t.co/56a0vZUx7i",
#             "author_id": "2244994945",
#             "created_at": "Wed Jan 06 18:40:40 +0000 2021",
#             "username": "XDevelopers"
#         }
#     ]
# }


def get_user_details_tweepy(
    username: str,
) -> Tuple[dict, str]:
    """
    Retrieve Twitter user details.

    Args:
        username (str): The username to get user details.

    Return:
        user_details: dict
    """
    try:
        user = tweepy_client.get_user(
            username=username,
            user_fields=[
                "affiliation",
                "connection_status",
                "created_at",
                "description",
                "entities",
                "id",
                "is_identity_verified",
                "location",
                "most_recent_tweet_id",
                "name",
                "parody",
                "pinned_tweet_id",
                "profile_banner_url",
                "profile_image_url",
                "protected",
                "public_metrics",
                "receives_your_dm",
                "subscription",
                "subscription_type",
                "url",
                "username",
                "verified",
                "verified_followers_count",
                "verified_type",
                "withheld",
            ],
            tweet_fields=[
                "article",
                "attachments",
                "author_id",
                "card_uri",
                "community_id",
                "context_annotations",
                "conversation_id",
                "created_at",
                "display_text_range",
                "edit_controls",
                "edit_history_tweet_ids",
                "entities",
                "geo",
                "id",
                "in_reply_to_user_id",
                "lang",
                "media_metadata",
                "non_public_metrics",
                "note_tweet",
                "organic_metrics",
                "possibly_sensitive",
                "promoted_metrics",
                "public_metrics",
                "referenced_tweets",
                "reply_settings",
                "scopes",
                "source",
                "text",
                "withheld",
            ],
        )

        if not user.data:
            print(traceback.format_exc())
            return {"user_detail": "User not found."}, "tweepy"
            # raise HTTPException(status_code=404, detail="User not found.")

        user_detail = {
            "user_id": user.data.id,
            "name": user.data.name,
            "username": user.data.username,
            "created_at": user.data.created_at.isoformat(),
            "followers": user.data.public_metrics["followers_count"],
            "following": user.data.public_metrics["following_count"],
        }

        return {"user_detail": user_detail}, "tweepy"

    except Exception as e:
        print(traceback.format_exc())
        return {"user_detail": f"Error retrieving user details: {str(e)}"}, "tweepy"
        # raise HTTPException(
        #     status_code=500, detail=f"Error retrieving user details: {str(e)}"
        # )


# get_user_details_tweepy Sample Output
# {
#     "data": {
#         "created_at": "2013-12-14T04:35:55Z",
#         "id": "2244994945",
#         "name": "X Dev",
#         "protected": False,
#         "username": "TwitterDev"
#     },
# }
