import os
import json
import requests
import time

from typing import Dict, Any
from apify_client import ApifyClient

class FacebookCrawler:
    def __init__(self):
        # Environment variables
        self.CRAWLBASE_URL = os.getenv("FACEBOOK_CRAWLBASE_URL")
        self.CRAWLBASE_API_TOKEN = os.getenv("FACEBOOK_CRAWLBASE_API_TOKEN")
        self.APIFY_API_KEY = os.getenv("FACEBOOK_APIFY_API_TOKEN")
        self.SCRAPINGBOT_USERNAME = os.getenv("FACEBOOK_SCRAPINGBOT_USERNAME")
        self.SCRAPINGBOT_API_KEY = os.getenv("FACEBOOK_SCRAPINGBOT_API_KEY")
        self.APIFY_API_TOKEN = os.getenv("FACEBOOK_APIFY_API_TOKEN")

        if not self.CRAWLBASE_API_TOKEN:
            raise ValueError(
                "FACEBOOK_CRAWLBASE_API_TOKEN is not set in the environment variables"
            )
        
        if not self.APIFY_API_TOKEN:
            raise ValueError("FACEBOOK_APIFY_API_TOKEN is not set in the environment variables")

        self.apify_client = ApifyClient(self.APIFY_API_TOKEN)

        # Define standard keys that we want in the output
        self.STANDARD_POST_KEYS = {
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

        self.STANDARD_PROFILE_KEYS = {
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

        self.API_MAPPINGS = {
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


    def scrape_facebook_group(
        self,
        group_handle: str,
    ) -> Dict | None:
        """Fetch Facebook data using Crawlbase API.
        
        args:
            group_handle (str): facebook group handle or id
        """
        url = f"https://www.facebook.com/groups/{group_handle}"

        result = self._scrape_facebook_crawlbase(
            url,
            "facebook-group",
        )

        if result:
            return self._standardize_group_data(
                result,
                "crawlbase",
            )
        
        apify_result = self._fallback_scrape_facebook_group_apify(group_handle)
        if isinstance(apify_result, list):
            for res_idx, res in enumerate(apify_result):
                apify_result[res_idx] = self._standardize_group_data(res, "apify")

            return apify_result
        
        return None

    def _scrape_facebook_crawlbase(
        self,
        url: str,
        scraper_type: str
    ):
        """Fetch Facebook data using Crawlbase API."""
        params = {"url": url, "scraper": scraper_type, "token": self.CRAWLBASE_API_TOKEN}
        try:
            response = requests.get(self.CRAWLBASE_URL, params=params)
            response.raise_for_status()
            result = response.json()
            return result if result and isinstance(result, dict) else None
        except requests.RequestException:
            return None
        
    def _fallback_scrape_facebook_profile_apify(
        self,
        username: str,
    ):
        """Use Apify if Crawlbase fails for profiles, then new ScrapingBot if Apify fails"""
        try:
            run_input = {
                "maxDelay": 10,
                "minDelay": 1,
                "profileUrls": [f"https://www.facebook.com/{username}"],
                "proxy": {"useApifyProxy": True, "apifyProxyCountry": "US"},
            }
            run = self.apify_client.actor("curious_coder/facebook-profile-scraper").call(
                run_input=run_input
            )
            return list(self.apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        except Exception:
            return self._scrape_facebook_scrapingbot(
                f"https://www.facebook.com/{username}", "profile"
            )


    def _fallback_scrape_facebook_group_apify(
        self,
        group_handle: str,
    ):
        """Use Apify if Crawlbase fails for groups, then new ScrapingBot if Apify fails"""
        try:
            run_input = {
                "startUrls": [{"url": f"https://www.facebook.com/groups/{group_handle}"}],
                "resultsLimit": 20,
                "viewOption": "CHRONOLOGICAL",
            }
            run = self.apify_client.actor("apify/facebook-groups-scraper").call(run_input=run_input)
            return list(self.apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        except Exception as e:
            return {"error": str(e)}


    def _fallback_scrape_facebook_page_apify(
        self,
        page_name: str,
    ):
        """Use Apify if Crawlbase fails for Facebook pages, then new ScrapingBot if Apify fails"""
        try:
            run_input = {
                "startUrls": [
                    {"url": f"https://www.facebook.com/{page_name}/", "method": "GET"}
                ]
            }
            run = self.apify_client.actor("apify/facebook-pages-scraper").call(run_input=run_input)
            return list(self.apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        except Exception as e:
            return {"error": str(e)}


    def _fallback_scrape_facebook_hashtag_apify(
        self,
        hashtag: str,
    ):
        """Use Apify if Crawlbase fails for hashtags, then new ScrapingBot if Apify fails"""
        try:
            run_input = {
                "keywordList": [hashtag],
                "resultsLimit": 50,
            }
            run = self.apify_client.actor("apify/facebook-hashtags-scraper").call(run_input=run_input)
            return list(self.apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        except Exception as e:
            return {"error": str(e)}

    def _standardize_group_data(
        self,
        data: Dict[str, Any],
        source: str
    ) -> Dict[str, Any]:
        """
        Standardizes group data from any source into a consistent format.
        """
        if not isinstance(data, dict):
            raise ValueError("Invalid data format. Expected a dictionary.")

        if source not in self.API_MAPPINGS:
            raise ValueError(f"Unsupported source: {source}")

        mapping = self.API_MAPPINGS[source]
        standardized = {
            "group_name": "",
            "group_type": "",
            "members_count": 0,
            "group_url": "",
            "description": "",
            "group_image": "",
            "posts": [],
        }

        # Map basic fields using source-specific mappings
        for api_key, std_key in mapping.items():
            if api_key in data and std_key in standardized:
                value = data.get(api_key, standardized[std_key])
                # Convert specific fields to proper types
                if std_key == "members_count":
                    try:
                        if isinstance(value, (int, float, str)):
                            standardized[std_key] = int(float(str(value)))
                        else:
                            standardized[std_key] = 0
                    except (ValueError, TypeError):
                        standardized[std_key] = 0
                else:
                    standardized[std_key] = str(value) if value is not None else ""

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

                    # Handle comments
                    comments = post.get("comments", [])
                    comment_list = []
                    if isinstance(comments, list):
                        for c in comments:
                            if isinstance(c, dict):
                                comment_list.append(
                                    {
                                        "user_name": str(
                                            c.get(mapping.get("userName", "userName"), "")
                                        ),
                                        "text": str(c.get(mapping.get("text", "text"), "")),
                                    }
                                )
                    standardized_post["comments"] = comment_list

                    images = post.get("images", [])
                    standardized_post["media"] = (
                        list(images) if isinstance(images, list) else []
                    )
                    standardized_posts.append(standardized_post)

        standardized["posts"] = standardized_posts
        return standardized