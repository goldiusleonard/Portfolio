import datetime
import os
import traceback

from typing import Union, Tuple
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_API_TOKEN = os.getenv("TWITTER_APIFY_API_TOKEN")
if not APIFY_API_TOKEN:
    raise ValueError("Twitter Apify API token is not valid!")

# Initialize the ApifyClient with your API token
client = ApifyClient(APIFY_API_TOKEN)


def get_recent_tweets_apify(
    query: str,
    start_time: Union[str, None],
    end_time: Union[str, None],
    max_results: int = 10,
):
    # Function to validate and format date
    def format_date(date_str):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            return dt.strftime("%Y-%m-%d")  # Ensure correct format
        except ValueError:
            raise ValueError(
                f"Invalid date format: {date_str}. Use 'YYYY-MM-DDTHH:mm:ssZ'."
            )

    try:
        # Validate and format optional date parameters
        formatted_start_time = format_date(start_time) if start_time else None
        formatted_end_time = format_date(end_time) if end_time else None

        # Prepare the Actor input
        run_input = {
            "searchTerms": [query],
            "maxItems": max_results,
            "sort": "Latest",
            "tweetLanguage": "en",
            "start": formatted_start_time,
            "end": formatted_end_time,
        }

        # Run the Actor and wait for it to finish
        run = client.actor("61RPP7dywgiy0JPD0").call(run_input=run_input)

        results = []

        # Fetch and print Actor results from the run's dataset (if there are any)
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            parsed_item = {
                "id": item["id"],
                "url": item["url"],
                "text": item["text"],
                "retweetCount": item["retweetCount"],
                "replyCount": item["replyCount"],
                "likeCount": item["likeCount"],
                "quoteCount": item["quoteCount"],
                "bookmarkCount": item["bookmarkCount"],
                "createdAt": item["createdAt"],
                "isRetweet": item["isRetweet"],
                "isQuotes": item["isQuotes"],
            }
            results.append(parsed_item)

        if results == []:
            print(traceback.format_exc())
            return {"tweets": "No tweets found for the given query."}, "tweepy"
            # raise HTTPException(
            #     status_code=404, detail="No tweets found for the given query."
            # )

        # # Save results to file
        # with open("/Users/goldiusleonard/Documents/new_code/buloh-crawler/apify_output.json", "w") as f:
        #     json.dump({"tweets": results}, f)

    except Exception as e:
        print(traceback.format_exc())
        return {"tweets": f"Error retrieving tweets: {str(e)}"}, "apify"

    return results, "apify"


# get_recent_tweets_apify Sample Output
# [
#     {
#         "url": "https://x.com/MyEdifier/status/1889622782222201233",
#         "twitterUrl": "https://twitter.com/MyEdifier/status/1889622782222201233",
#         "id": "1889622782222201233",
#         "text": "🔥 BUY 1 FREE 1 DEAL! 🔥 🎧 Purchase the X3 Lite or X5 Pro and get a FREE PVC Pouch! 🎁\n\n⏰ Limited Time Only!\n📦 Limited Stocks Available – While Stocks Last!\n🚀 Promotion starts on 13 Feb 2025!\n\n👉 Shop Now: https://t.co/5mO9y1pLay\n\n#EdifierxShopeeMall #Buy1Free1 #X3Lite #X5Pro https://t.co/LdmZNNfqRG",
#         "retweetCount": 0,
#         "replyCount": 0,
#         "likeCount": 0,
#         "quoteCount": 0,
#         "createdAt": "Wed Feb 12 10:29:13 +0000 2025",
#         "bookmarkCount": 0,
#         "isRetweet": false,
#         "isQuote": false
#     },
#     {
#         "url": "https://x.com/sirshibaninja/status/1889622743877873854",
#         "twitterUrl": "https://twitter.com/sirshibaninja/status/1889622743877873854",
#         "id": "1889622743877873854",
#         "text": "@derbluex @Starknet This is bullish",
#         "retweetCount": 0,
#         "replyCount": 0,
#         "likeCount": 0,
#         "quoteCount": 0,
#         "createdAt": "Wed Feb 12 10:29:04 +0000 2025",
#         "bookmarkCount": 0,
#         "isRetweet": false,
#         "isQuote": false
#     }
# ]


def get_user_details_apify(
    user_handle: str,
) -> Tuple[dict, str]:
    """
    Retrieve Twitter user details by keyword.

    Args:
        user_handle (str): The twitter or x username to get user details.

    Return:
        user_details: dict
    """
    try:
        # Initialize the ApifyClient with your API token
        client = ApifyClient(APIFY_API_TOKEN)

        # Prepare the Actor input
        run_input = {
            "getFollowers": True,
            "getFollowing": True,
            "getRetweeters": True,
            "includeUnavailableUsers": False,
            "maxItems": 1,
            "twitterHandles": [user_handle],
        }

        # Run the Actor and wait for it to finish
        run = client.actor("V38PZzpEgOfeeWvZY").call(run_input=run_input)

        dataset = client.dataset(run["defaultDatasetId"])

        if len(dataset.iterate_items()) < 1:
            print(traceback.format_exc())
            return {"user_detail": "User not found."}, "apify"
            # raise HTTPException(status_code=404, detail="User not found.")

        result = dataset.iterate_items()[0]

        user_detail = {
            result["id"],
            result["name"],
            result["userName"],
            result["description"],
            result["location"],
            result["profilePicture"],
            result["coverPicture"],
            result["status"],
            result["isVerified"],
            result["followers"],
            result["following"],
        }

        return {"user_detail": user_detail}, "apify"

    except Exception as e:
        print(traceback.format_exc())
        return {"user_detail": f"Error retrieving user details: {str(e)}"}, "apify"
        # raise HTTPException(
        #     status_code=500, detail=f"Error retrieving user details: {str(e)}"
        # )


# get_user_details_tweepy Sample Output
# {
#     "data": {
#             "id": "44196397",
#             "name": "Elon Musk",
#             "userName": "elonmusk",
#             "description": "",
#             "location": "",
#             "profilePicture": "https://pbs.twimg.com/profile_images/1874558173962481664/8HSTqIlD_normal.jpg",
#             "coverPicture": "https://pbs.twimg.com/profile_banners/44196397/1726163678",
#             "status": "",
#             "isVerified": true,
#             "followers": 217538566,
#             "following": 1021
#         },
# }
