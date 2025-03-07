import json
import re
import pandas as pd
from logging_section import setup_logging
from text_cleaning import TextCleaner
pd.options.mode.chained_assignment = None  # Disable the warning
pd.set_option("future.no_silent_downcasting", True)

logger = setup_logging()

class DataPreprocessor:
    @staticmethod
    def process_profile_data(profile_df: pd.DataFrame) -> pd.DataFrame:
        # Extract user's following, followers and total video count
        columns_extract = ["followerCount", "followingCount", "videoCount"]
        for i in columns_extract:
            profile_df[i] = profile_df["data"].apply(
                lambda x: x.get("stats", {}).get(i) if isinstance(x, dict) else None
            )

        profile_df = profile_df[
            ["username", "followerCount", "followingCount", "videoCount"]
        ]

        # Rename column
        profile_df.rename(
            columns={
                "followerCount": "user_followers_count",
                "followingCount": "user_following_count",
                "videoCount": "user_total_videos",
            },
            inplace=True,
        )

        logger.info(f"Processed profile data. Records: {len(profile_df)}")
        return profile_df

    @staticmethod
    def process_video_data(video_df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess raw video data and return a cleaned DataFrame."""
        logger.info("Starting preprocessing of video metadata.")
        try:
            # to be removed later
            # video_df = video_df[video_df['request_id'] > 363]

            # Clean title
            cleaner = TextCleaner()
            video_df = cleaner.clean(video_df, "title")
            video_df.drop(columns="id", inplace=True, errors="ignore")

            ## Feature Extraction ##
            # Extract user_handle, user_id, avatar from author field
            columns_extract = ["id", "unique_id", "avatar"]
            for i in columns_extract:
                video_df[i] = video_df["author"].apply(
                    lambda x: x.get(i) if isinstance(x, dict) else None
                )

            # Extract hashtags
            video_df["video_hashtags"] = video_df["title"].apply(
                lambda text: (
                    ", ".join(re.findall(r"#\w+", text))
                    if isinstance(text, str)
                    else ""
                )
            )

            # Convert Unix timestamp to human-readable datetime
            video_df["create_time"] = pd.to_datetime(
                video_df["create_time"], unit="s"
            ).dt.strftime("%Y-%m-%d %H:%M:%S")

            # Rename column
            video_df.rename(
                columns={
                    "_id": "video_mongodb_id",
                    "cover": "video_screenshot",
                    "duration": "video_duration_seconds",
                    "play": "video_path",
                    "wmplay": "video_url",
                    "play_count": "video_view_count",
                    "digg_count": "video_like_count",
                    "download_count": "video_download_count",
                    "comment_count": "comment_count",
                    "share_count": "video_share_count",
                    "create_time": "video_posted_timestamp",
                    "id": "profile_id",
                    "unique_id": "user_handle",
                    "created_at": "crawling_timestamp",
                    "avatar": "creator_photo_link",
                    "collect_count": "video_save_count",
                },
                inplace=True,
            )

            # Drop unnecessary columns
            drop_cols = [
                "aweme_id",
                "ai_dynamic_cover",
                "origin_cover",
                "author",
                "music",
                "music_info",
                "anchors",
                "anchors_extras",
                "is_ad",
                "commerce_info",
                "commercial_video_info",
                "item_comment_settings",
                "size",
                "mentioned_users",
                "location",
                "month",
                "year",
                "day",
                "images",
                "updated_at",
                "is_top",
                "is_flagged",
                "hdplay",
                "hd_size",
                "wm_size",
                "video_source",
            ]

            video_df.drop(columns=drop_cols, inplace=True, errors="ignore")
            logger.info(f"Processed video data. Records: {len(video_df)}")
            return video_df

        except Exception as e:
            logger.error(f"Error processing video data: {e}")
            raise

    @staticmethod
    def process_replies(comments_raw: pd.DataFrame) -> pd.DataFrame:
        logger.info("Starting preprocessing of comments' reply data.")
        try:
            # to be removed later
            # comments_raw = comments_raw[comments_raw['request_id'] > 363]

            # Filter rows where 'replies' is not empty or an empty list
            filtered_comments = comments_raw.loc[
                comments_raw["replies"].apply(
                    lambda x: isinstance(x, list) and len(x) > 0
                )
            ]

            # Explode 'replies' and normalize directly
            exploded_replies = filtered_comments.explode("replies", ignore_index=True)
            replies_df = pd.json_normalize(exploded_replies["replies"])

            # Add 'comment_id' and reorder columns efficiently
            replies_df.insert(0, "_id", exploded_replies["_id"])
            replies_df.insert(1, "comment_id", exploded_replies["comment_id"])

            keep_columns = [
                "_id",
                "comment_id",
                "id",
                "video_id",
                "text",
                "create_time",
                "digg_count",
                "user.id",
                "user.region",
                "user.unique_id",
                "user.avatar",
            ]

            # Keep only relevant columns and rename them
            column_mapping = {
                "_id": "comment_mongodb_id",
                "id": "reply_id",
                "comment_id": "video_comment_id",
                "user.unique_id": "user_handle",
                "create_time": "reply_posted_timestamp",
                "digg_count": "reply_like_count",
                "user.id": "user_id",
                "user.region": "user_region",
                "user.avatar": "user_avatar",
            }

            replies_df = replies_df[keep_columns].rename(columns=column_mapping)

            # Add an incremental 'id' column starting from 1
            replies_df.insert(0, "id", range(1, len(replies_df) + 1))

            # Convert Unix timestamp to human-readable datetime
            replies_df["reply_posted_timestamp"] = pd.to_datetime(
                replies_df["reply_posted_timestamp"], unit="s"
            ).dt.strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Processed comments reply data. Records: {len(replies_df)}")

            return replies_df

        except Exception as e:
            logger.error(f"Error processing replies data: {e}")
            raise

    @staticmethod
    def process_comment_data(comments_df: pd.DataFrame) -> pd.DataFrame:
        """Preprocess raw comment data, return cleaned_comments dataframe and the replies dataframe"""
        logger.info("Starting preprocessing of comments data.")

        try:
            # to be removed later
            # comments_df = comments_df[comments_df['request_id'] > 363]

            # Clean specified columns
            cleaner = TextCleaner()
            comments_df = cleaner.clean(comments_df, "text")
            # x = len(comments_df)
            comments_df = cleaner.filter_latin_word(comments_df, "text")
            # logger.info(f"Rows removed (non-latin): {x - len(comments_df)}") # check how many rows removed

            ## Feature Extraction ##
            # Extract user_handle from user field
            comments_df["user_handle"] = comments_df["user"].apply(
                lambda x: x.get("unique_id") if isinstance(x, dict) else None
            )

            # Convert Unix timestamp to human-readable datetime
            comments_df["create_time"] = pd.to_datetime(
                comments_df["create_time"], unit="s"
            ).dt.strftime("%Y-%m-%d %H:%M:%S")

            # Drop unnecessary columns
            drop_cols = [
                "user",
                "status",
                "reply_total",
                "is_flagged",
                "updated_at",
                "comment_id",
                "replies",
            ]
            comments_df.drop(columns=drop_cols, inplace=True)

            comments_df.rename(
                columns={
                    "_id": "comment_mongodb_id",
                    "id": "video_comment_id",
                    "unique_id": "user_handle",
                    "create_time": "comment_posted_timestamp",
                    "digg_count": "comment_like_count",
                    "created_at": "crawling_timestamp",
                },
                inplace=True,
            )
            # handle nan to 0 for MySQL
            comments_df = comments_df.fillna(0)
            # convert Objectid datatype in comments_df
            comments_df["comment_mongodb_id"] = comments_df[
                "comment_mongodb_id"
            ].astype(str)
            logger.info(f"Processed comment data. Records: {len(comments_df)}")

            return comments_df

        except Exception as e:
            logger.error(f"Error processing comment data: {e}")
            raise

    @staticmethod
    def preprocess_crawl_tags(mysql_data: dict) -> pd.DataFrame:
        """Preprocess crawling_data and tags loaded from mysql"""
        logger.info("Starting preprocessing of crawling_data and tags.")
        try:
            # drop uneeded column
            drop_cols = ["created_at", "from_date", "to_date"]
            crawling_data = mysql_data["crawling_data"].copy()
            crawling_data.drop(columns=drop_cols, inplace=True)
            tags = mysql_data["tags"].copy()
            tags.drop(columns=["id"], inplace=True)
            tags.rename(columns={"type": "video_source"}, inplace=True)

            # drop previous used data redundant request id
            # # start take from request_id 364
            # crawling_data = crawling_data[crawling_data['id'] > 363]

            # merge on request_id
            crawl_tags_df = pd.merge(
                crawling_data, tags, left_on="id", right_on="request_id", how="inner"
            ).drop(columns=["id"])

            # agent_name, agent_id, created_by, description
            return crawl_tags_df

        except Exception as e:
            logger.error(f"Error merging video and comment data: {e}")
            raise

    @staticmethod
    def merge_data(video_df, comments_df, profile_df, crawl_tags_df) -> pd.DataFrame:
        """Merge video and comment data based on video_id and request_id."""
        logger.info("Start merging dataframe... ")

        try:
            # Merge video and profile data
            video_profile_df = pd.merge(
                video_df,
                profile_df,
                left_on="user_handle",
                right_on="username",
                how="inner",
            ).drop(columns=["username"])

            # Group comments
            grouped_comments = (
                comments_df.groupby(["video_id", "request_id"], group_keys=False)
                .apply(lambda x: x.to_dict(orient="records"), include_groups=False)
                .reset_index(name="comments")
            )

            # Merge with comments
            video_profile_comments_df = pd.merge(
                video_profile_df,
                grouped_comments,
                on=["video_id", "request_id"],
                how="left",
            )

            # Aggregate crawling and tags
            # Combines all the values in the group into a single string, separated by commas
            crawl_tags_agg = crawl_tags_df.groupby(
                [
                    "request_id",
                    "tiktok",
                    "news",
                    "category",
                    "subcategory",
                    "video_source",
                    "agent_name",
                    "agent_id",
                    "created_by",
                    "description",
                ],
                as_index=False,
            ).agg(
                {
                    "value": lambda x: ", ".join(x),
                }
            )

            # Merge with crawl tags
            video_profile_comments_crawl_tags = pd.merge(
                video_profile_comments_df, crawl_tags_agg, on="request_id", how="left"
            )

            # Replace NaN with 0 for MySQL compatibility
            video_profile_comments_crawl_tags.fillna(0, inplace=True)

            # # Merge with transcription and description, change id to string for merging
            # video_profile_comments_crawl_tags["video_mongodb_id"] = (
            #     video_profile_comments_crawl_tags["video_mongodb_id"].astype(str)
            # )
            # merged_df = pd.merge(
            #     video_profile_comments_crawl_tags,
            #     description_df,
            #     left_on="video_mongodb_id",
            #     right_on="_id",
            #     how="inner",
            # ).drop(columns=["_id"])
            # merged_df = pd.merge(
            #     merged_df,
            #     transcription_df,
            #     left_on="video_mongodb_id",
            #     right_on="_id",
            #     how="left",
            # ).drop(columns=["_id"])


            logger.info(f"Merged data. Total records: {len(video_profile_comments_crawl_tags)}")
            return video_profile_comments_crawl_tags

        except Exception as e:
            logger.error(f"Error merging video and comment data: {e}")
            raise

    @staticmethod
    def convert_datatype(df: pd.DataFrame) -> pd.DataFrame:
        """Convert necessary datatype for MySQL compatibility"""
        # Convert the list to a JSON string
        df["comments"] = df["comments"].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else str(x)
        )
        df["video_description"] = df["video_description"].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else str(x)
        )
        return df

    # @staticmethod
    # def process_desc_transc(mysql_data: dict) -> pd.DataFrame:
    #     # convert datatype and merge with description and transcription
    #     description_df = mysql_data["description_df"].copy()
    #     transcription_df = mysql_data["transcription_df"].copy()
    #     description_df["_id"] = description_df["_id"].astype(str)
    #     transcription_df["_id"] = transcription_df["_id"].astype(str)
    #     return description_df, transcription_df

    @staticmethod
    def map_cat_subcat(mysql_data: dict, df: pd.DataFrame) -> pd.DataFrame:
        """Map 'category' and 'subcategory' columns in the DataFrame to their respective IDs
        df : The DataFrame containing 'category' and 'subcategory' columns.
        mapping_df (str): The name of the table where the mapped DataFrame will be written.
        Returns: pd.DataFrame: The updated DataFrame with mapped IDs.
        """
        try:
            # print(mysql_data.keys())
            category_df = mysql_data["category_df"].copy()
            subcategory_df = mysql_data["sub_category_df"].copy()

            # Create mapping dictionaries for category and subcategory
            category_mapping = dict(
                zip(category_df["category_name"], category_df["id"])
            )
            subcategory_mapping = dict(
                zip(subcategory_df["sub_category_name"], subcategory_df["id"])
            )

            # Map 'category' and 'subcategory' columns to IDs
            df["category"] = df["category"].map(category_mapping)
            df["subcategory"] = df["subcategory"].map(subcategory_mapping)

            # Testing purposes:Remove rows where either 'category' or 'subcategory' is NaN
            df = df.dropna(subset=["category", "subcategory"])

            ### Create the mapped_cat_subcat ###
            # Extract the category and subcategory_id for
            cat_mappingID_df = df[["category", "subcategory", "video_id"]]
            # Rename 'category' and 'subcategory'
            cat_mappingID_df = cat_mappingID_df.rename(
                columns={"category": "category_id", "subcategory": "sub_category_id"}
            )

            ### Create the preprocessed_unbiased table with video_id unique ###
            # remove the category and subcat category
            df.drop(columns="category", inplace=True)
            df.drop(columns="subcategory", inplace=True)

            # Remove duplicates of video_id in preprocessed_unbiased table
            df = (
                df.groupby("video_id")
                .agg(
                    {
                        col: "last"
                        if col != "request_id"
                        else lambda x: ", ".join(map(str, x))
                        for col in df.columns
                        if col != "video_id"
                    },
                )
                .reset_index()
            )

            # map with the preprocessed_unbiased id
            df.insert(0, "id", range(1, len(df) + 1))

            # if video_id with same cat and same subcat in the mapping_df, drop them as it is redundant
            cat_mappingID_df = cat_mappingID_df.drop_duplicates(
                subset=["category_id", "sub_category_id", "video_id"], keep="first"
            )

            # Add preprocessed_unbiased_id based on index from df, +1 for MySQL ID starting at 1
            cat_mappingID_df = cat_mappingID_df.merge(
                df[["video_id", "id"]], on="video_id", how="left"
            ).rename(columns={"id": "preprocessed_unbiased_id"})

            # Add an incremental 'id' column starting from 1
            cat_mappingID_df.insert(0, "id", range(1, len(cat_mappingID_df) + 1))

            return cat_mappingID_df, df

        except Exception as e:
            logger.error(f"Error in mapping categories and subcategories: {e}")
            return None

    @staticmethod
    def user_request_id(df: pd.DataFrame) -> pd.DataFrame:
        """Create a table to store request_id (history)of each video_id.
        Returns:pd.DataFrame containing the request_id table.
        """
        request_id_df = df[
            [
                "video_mongodb_id",
                "request_id",
                "video_id",
                "category",
                "subcategory",
                "crawling_timestamp",
                "video_source",
                "value",
                "agent_name",
                "agent_id",
                "created_by",
                "description",
            ]
        ].copy()

        return request_id_df

    @staticmethod
    def preprocess_and_merge(mongo_data, mysql_data) -> pd.DataFrame:
        """Preprocess the raw data and merging tables"""
        try:
            video_df = DataPreprocessor.process_video_data(mongo_data["video"])
            comments_df = DataPreprocessor.process_comment_data(mongo_data["comment"])
            profile_df = DataPreprocessor.process_profile_data(mongo_data["profile"])
            crawl_tags_df = DataPreprocessor.preprocess_crawl_tags(mysql_data)
            replies_df = DataPreprocessor.process_replies(mongo_data["comment"])
            # description_df, transcription_df = DataPreprocessor.process_desc_transc(
            #     mysql_data
            # )

            # keep for debugging
            video_df.to_csv("csv_file/video_df.csv", index=False)
            comments_df.to_csv("csv_file/comments_df.csv", index=False)
            profile_df.to_csv("csv_file/profile_df.csv", index=False)
            crawl_tags_df.to_csv("csv_file/crawl_tags_df.csv", index=False)
            replies_df.to_csv("csv_file/replies_df.csv", index=False)
            # description_df.to_csv("csv_file/description_df.csv", index=False)

            # merging all the tables
            # merged_df = DataPreprocessor.merge_data(
            #     video_df,
            #     comments_df,
            #     profile_df,
            #     crawl_tags_df,
            #     description_df,
            #     transcription_df,
            # )

            merged_df = DataPreprocessor.merge_data(
                video_df,
                comments_df,
                profile_df,
                crawl_tags_df
            )

            # create a dataframe to keep user request_id with duplicates video_id
            request_id_df = DataPreprocessor.user_request_id(merged_df)

            # remove these columns, may use agent_name only for agent's details. -tbc
            merged_df = merged_df.drop("agent_id", "created_by", "description")

            # Perform the merge to add category and subcategory into comments table based on video_id and request_id
            comments_df = pd.merge(
                comments_df,
                request_id_df[["video_id", "request_id", "category", "subcategory"]],
                on=["video_id", "request_id"],
                how="inner",
            )

            # Map the merged_df to category and subcategory IDs
            mappingID_df, preprocessed_df = DataPreprocessor.map_cat_subcat(
                mysql_data, merged_df
            )

            # convert datatype for MySQL
            preprocessed_df = DataPreprocessor.convert_datatype(preprocessed_df)

            logger.info("Done preprocessing all tables.")

            # keep for debugging
            video_df.to_csv("csv_file/video_df.csv", index=False)
            comments_df.to_csv(
                "csv_file/comments_category_subcategory_df.csv", index=False
            )
            profile_df.to_csv("csv_file/profile_df.csv", index=False)
            crawl_tags_df.to_csv("csv_file/crawl_tags_df.csv", index=False)
            replies_df.to_csv("csv_file/replies_df.csv", index=False)
            merged_df.to_csv("csv_file/merged_df.csv", index=False)
            preprocessed_df.to_csv("csv_file/preprocessed_df.csv", index=False)

            return preprocessed_df, comments_df, replies_df, mappingID_df, request_id_df

        except Exception as e:
            logger.error(f"Data preprocessing failed: {e}")
            raise

    @staticmethod
    def directlink_preprocess(mongo_data, mysql_data) -> pd.DataFrame:
        """Preprocess for direct url"""
        try:
            video_df = DataPreprocessor.process_video_data(mongo_data["video"])
            comments_df = DataPreprocessor.process_comment_data(mongo_data["comment"])
            profile_df = DataPreprocessor.process_profile_data(mongo_data["profile"])
            crawl_tags_df = DataPreprocessor.preprocess_crawl_tags(mysql_data)
            replies_df = DataPreprocessor.process_replies(mongo_data["comment"])
            # description_df, transcription_df = DataPreprocessor.process_desc_transc(
            #     mysql_data
            # )

            # # merging all the tables
            # merged_df = DataPreprocessor.merge_data(
            #     video_df,
            #     comments_df,
            #     profile_df,
            #     crawl_tags_df,
            #     description_df,
            #     transcription_df,
            # )

            merged_df = DataPreprocessor.merge_data(
                video_df,
                comments_df,
                profile_df,
                crawl_tags_df
            )

            merged_df = merged_df.drop("category", "subcategory", "agent_name", "agent_id", "created_by", "description")

            # create a dataframe to keep user request_id with duplicates video_id
            request_id_df = DataPreprocessor.user_request_id(merged_df)

            # convert datatype for MySQL
            preprocessed_df = DataPreprocessor.convert_datatype(merged_df)

            logger.info("Done preprocessing all tables.")

            return preprocessed_df, comments_df, replies_df, request_id_df

        except Exception as e:
            logger.error(f"Data preprocessing failed: {e}")
            raise
