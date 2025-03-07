import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text
from db.db import Base
from log_mongo import logger

load_dotenv()

# # Declare the base class for SQLAlchemy
# Base = declarative_base()


class TablesName:
    """Configuration class for table names loaded from environment variables."""

    analysis_table_name: str = os.getenv("table_name_output_1")
    if not analysis_table_name:
        logger.error("table_name_output_1 not defined in env")

    mapped_table_name: str = os.getenv("table_name_output_2")
    if not mapped_table_name:
        logger.error("table_name_output_2 not defined in env")

    comments_table_name: str = os.getenv("table_name_output_3")
    if not comments_table_name:
        logger.error("table_name_output_3 not defined in env")

    tiktok_table_name: str = os.getenv("table_name_output_4")
    if not tiktok_table_name:
        logger.error("table_name_output_4 not defined in env")


class MappedTableSchemaOut(Base):
    __tablename__ = TablesName.mapped_table_name
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)  # Incremental ID
    category_id = Column(Integer)
    sub_category_id = Column(Integer)
    video_id = Column(String(50), nullable=False)
    preprocessed_unbiased_id = Column(Integer)
    analysis_id = Column(Integer)


# Define the table schema for sentiment_table
class AnalysisTableSchema(Base):
    __tablename__ = TablesName.analysis_table_name
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, nullable=True)
    sub_category_id = Column(Integer, nullable=True)
    video_id = Column(String(50), nullable=True)  # Associated video ID
    preprocessed_unbiased_id = Column(Integer)
    # agent_name = Column(String(50), nullable=True)  # Agent that provided the data
    sentiment = Column(String(255), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    api_sentiment = Column(String(255), nullable=True)
    api_sentiment_score = Column(Float, nullable=True)
    eng_justification = Column(Text, nullable=True)
    malay_justification = Column(Text, nullable=True)
    risk_status = Column(String(255), nullable=True)
    irrelevant_score = Column(String(255), nullable=True)
    law_regulated = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=True, default=datetime.utcnow)
    process_time = Column(Float, nullable=True)


# Define the table schema class
class CommentsTableSchemaOut(Base):
    __tablename__ = TablesName.comments_table_name
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)  # Incremental ID
    comment_mongodb_id = Column(String(50), nullable=False)  # MongoDB ID
    video_comment_id = Column(String(50), nullable=False)
    video_id = Column(String(255), nullable=False)
    text = Column(Text)
    comment_posted_timestamp = Column(DateTime)
    comment_like_count = Column(Integer)
    crawling_timestamp = Column(DateTime)
    request_id = Column(Integer)
    user_handle = Column(String(50))
    category = Column(String(255), nullable=True)
    subcategory = Column(String(255), nullable=True)
    video_summary = Column(Text)
    agent_name = Column(String(255))
    eng_justification = Column(Text, nullable=True)
    malay_justification = Column(Text, nullable=True)
    risk_status = Column(String(50), nullable=True)
    irrelevant_score = Column(String(50), nullable=True)
    timestamp = Column(DateTime, nullable=True, default=datetime.utcnow)
    process_time = Column(Float, nullable=True)


# Define the table schema class
class TikTokTableSchemaOut(Base):
    __tablename__ = TablesName.tiktok_table_name
    __table_args__ = {"extend_existing": True}

    # Columns definition
    platform = Column(String(255), nullable=True)
    _id = Column(String(50), primary_key=True)
    video_id = Column(String(255), nullable=True)
    ai_dynamic_cover = Column(Text, nullable=True)
    anchors = Column(Text, nullable=True)
    anchors_extras = Column(Text, nullable=True)
    author = Column(JSON, nullable=True)
    aweme_id = Column(String(255), nullable=True)
    comment_count = Column(Integer, nullable=True)
    commerce_info = Column(JSON, nullable=True)
    commercial_video_info = Column(Text, nullable=True)
    cover = Column(Text, nullable=True)
    create_time = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    digg_count = Column(Integer, nullable=True)
    download_count = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    is_ad = Column(Boolean, nullable=True)
    is_flagged = Column(Boolean, nullable=True)
    is_top = Column(Boolean, nullable=True)
    item_comment_settings = Column(Text, nullable=True)
    music = Column(Text, nullable=True)
    music_info = Column(JSON, nullable=True)
    origin_cover = Column(Text, nullable=True)
    play = Column(Text, nullable=True)
    play_count = Column(Integer, nullable=True)
    region = Column(String(255), nullable=True)
    share_count = Column(Integer, nullable=True)
    size = Column(Integer, nullable=True)
    title = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    video_source = Column(String(255), nullable=True)
    wm_size = Column(Integer, nullable=True)
    wmplay = Column(Text, nullable=True)
    request_id = Column(Text, nullable=True)
    collect_count = Column(Integer, nullable=True)
    images = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    perspective = Column(String(255), nullable=True)
    video_description = Column(Text, nullable=True)
    video_language = Column(Text, nullable=True)
    transcription = Column(Text, nullable=True)
    video_summary = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    subcategory = Column(String(255), nullable=True)
    sentiment = Column(String(255), nullable=True)
    sentiment_score = Column(Float, nullable=True)
    api_sentiment = Column(String(255), nullable=True)
    api_sentiment_score = Column(Float, nullable=True)
    eng_justification = Column(Text, nullable=True)
    malay_justification = Column(Text, nullable=True)
    risk_status = Column(String(255), nullable=True)
    irrelevant_score = Column(String(255), nullable=True)
    law_regulated = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=True, default=datetime.utcnow)
    process_time = Column(Float, nullable=True)


# # Define the table schema class
# class CommentsTableSchemaOut(Base):
#     __tablename__ = TablesName.comments_table_name

#     id = Column(Integer, primary_key=True, autoincrement=True)  # Incremental ID
#     comment_mongodb_id = Column(String(50), unique=True)  # MongoDB ID
#     video_comment_id = Column(String(50), nullable=False)
#     video_id = Column(String(255), nullable=False)
#     text = Column(Text)
#     comment_posted_timestamp = Column(DateTime)
#     comment_like_count = Column(Integer)
#     crawling_timestamp = Column(DateTime)
#     request_id = Column(Integer)
#     user_handle = Column(String(50))
#     video_summary = Column(Text)
#     eng_justification = Column(Text, nullable=True)
#     malay_justification = Column(Text, nullable=True)
#     risk_status = Column(String(50), nullable=True)
#     irrelevant_score = Column(String(50), nullable=True)


# # Define the table schema for ss_output
# class SsOutputTableSchema(Base):
#     __tablename__ = 'ss_output_table_test'

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     video_mongodb_id = Column(String(255), unique=True)
#     video_id = Column(String(255))
#     region = Column(String(10))
#     title = Column(LONGTEXT)
#     video_screenshot = Column(String(2083))  # URL length # Cover image URL
#     video_duration_seconds = Column(Integer)  # Video duration in seconds
#     video_path = Column(String(2083))  # URL path to blob
#     video_url = Column(String(2083)) # Watermarked tiktok play url
#     video_view_count = Column(Integer)
#     video_like_count = Column(Integer) # number of "likes" / hearts
#     comment_count = Column(Integer)
#     video_share_count = Column(Integer)
#     video_download_count = Column(Integer) # Download count
#     video_posted_timestamp = Column(DateTime)
#     request_id = Column(Integer)
#     crawling_timestamp = Column(DateTime)
#     video_source = Column(String(255))
#     video_save_count = Column(Integer) # number of times a video has been added to favorites or collection
#     profile_id = Column(String(255)) # creator's id
#     user_handle = Column(String(255)) # creator username
#     creator_photo_link = Column(LONGTEXT)
#     video_hashtags = Column(String(1000))
#     user_followers_count = Column(Integer)
#     user_following_count = Column(Integer)
#     user_total_videos = Column(Integer)
#     comments = Column(Text)
#     tiktok = Column(Boolean)
#     news = Column(Boolean)
#     value = Column(String(255))
#     video_description = Column(LONGTEXT)
#     video_language = Column(String(50))
#     transcription = Column(LONGTEXT)
#     video_summary = Column(LONGTEXT)
#     analysis_table_id = Column(String(255), nullable=True)  # ForeignKey to sentiment_table
