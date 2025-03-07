from typing import Optional, Dict
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv
from .base import Crawler
from ..database.connection import MongoDBClient
from ..utils import helpers, Logger, get_env_variable

load_dotenv()

log = Logger(name="ProfileCrawler")

bucket_name: str = get_env_variable(
    "AWS_BUCKET_NAME", "AWS_BUCKET_NAME is not provided!"
)


class ProfileCrawler(Crawler):
    def crawl(self, userid: str, username: str) -> Optional[Dict]:
        """Fetch profile information and update or insert into the database.

        Args:
            username (str): TikTok username.

        Returns:
            Optional[Dict]: The profile document after upsert or None in case of error.
        """
        cprint(f"Fetching profile for [{username}]...", "green", attrs=["bold"])
        log.info(f"Fetching profile for [{username}]...")
        url = "https://tiktok-scraper7.p.rapidapi.com/user/info"
        querystring = {"user_id": userid, "unique_id": username}
        response = self._fetch_profile_info(url=url, params=querystring)

        if not response:
            return None

        response = self._update_or_insert_profile(username, response)
        print(f"Profile for {username} stored in the database")
        log.info(f"Profile for {username} stored in the database")
        return response

    def _fetch_profile_info(self, url: str, params: Dict[str, str]) -> Optional[Dict]:
        """Send API request to fetch profile information.

        Args:
            url (str): The API endpoint URL.
            params (Dict[str, str]): The query parameters for the request.

        Returns:
            Optional[Dict]: The API response or None in case of error.
        """
        response: dict = helpers.send_api_request(
            url=url, headers=self.headers, params=params
        )
        if "error" in response:
            print(response["error"])
            log.error(response["error"])
            return None

        return response

    def _update_or_insert_profile(self, username: str, profile_data: Dict) -> Dict:
        """Update or insert the profile data into the MongoDB collection.

        Args:
            username (str): The TikTok username.
            profile_data (Dict): The profile data to be inserted or updated.

        Returns:
            Dict: The updated or inserted profile document.
        """
        profile_data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with MongoDBClient() as db:
            # Check if the profile already exists
            profile_doc = db["profile"].find_one({"username": username})
            if profile_doc is None:
                profile_data["created_at"] = profile_data["updated_at"]

                # Store profile into Azure Blob and set blob url
                profile_photo = helpers.download_file(
                    profile_data["data"]["user"]["avatarLarger"]
                )

                if not profile_photo:
                    raise RuntimeError("Profile photo download failed!")

                profile_data["data"]["user"]["avatarLarger"] = helpers.upload_s3_file(
                    bucket_name=bucket_name,
                    filename=username,
                    data=profile_photo,
                    extension="jpg",
                    folder="profile-photos",
                )

            # Upsert the document
            profile_doc = db["profile"].find_one_and_update(
                {"username": username}, {"$set": profile_data}, upsert=True
            )

        return profile_doc
