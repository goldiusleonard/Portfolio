import os
import sys
from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import LONGTEXT
from db.db import Base
from log_mongo import logger

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()


class TablesName:
    """Configuration class for table names loaded from environment variables."""

    preprocessed_unbiased_table_name = os.getenv("table_name_input_1")
    comments_table_name = os.getenv("table_name_input_2")
    mapped_table_name = os.getenv("table_name_input_3")
    category_table_name = os.getenv("table_name_input_4")
    sub_category_table_name = os.getenv("table_name_input_5")
    tiktok_table_name = os.getenv("table_name_input_6")

    for var_name, value in (
        ("table_name_input_1", preprocessed_unbiased_table_name),
        ("table_name_input_2", comments_table_name),
        ("table_name_input_3", mapped_table_name),
        ("table_name_input_4", category_table_name),
        ("table_name_input_5", sub_category_table_name),
        ("table_name_input_6", tiktok_table_name),
    ):
        if not value:
            logger.error(f"{var_name} not defined in env")


class CategoryTableSchema(Base):
    __tablename__ = TablesName.category_table_name
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(50), nullable=False)


class SubCategoryTableSchema(Base):
    __tablename__ = TablesName.sub_category_table_name
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    sub_category_name = Column(String(50), nullable=False)
    category_id = Column(Integer, ForeignKey(CategoryTableSchema.id), nullable=False)


class CommentsTableSchemaIn(Base):
    __tablename__ = TablesName.comments_table_name
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_mongodb_id = Column(String(255), unique=True)
    video_comment_id = Column(String(255), nullable=False)
    video_id = Column(String(255), nullable=False)
    text = Column(LONGTEXT)
    comment_posted_timestamp = Column(DateTime)
    comment_like_count = Column(Integer)
    crawling_timestamp = Column(DateTime)
    request_id = Column(Integer)
    user_handle = Column(String(255))
    category = Column(String(255))
    subcategory = Column(String(255))
    video_summary = Column(LONGTEXT)
    agent_name = Column(String(255))


class MappedTableSchemaIn(Base):
    __tablename__ = TablesName.mapped_table_name
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer)
    sub_category_id = Column(Integer)
    video_id = Column(String(50), nullable=False)
    preprocessed_unbiased_id = Column(Integer)
    analysis_id = Column(Integer)


class PreUnbiasedTableSchema(Base):
    __tablename__ = TablesName.preprocessed_unbiased_table_name
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_mongodb_id = Column(String(255), unique=True)
    video_id = Column(String(255))
    region = Column(String(10))
    title = Column(LONGTEXT)
    video_screenshot = Column(String(2083))
    video_duration_seconds = Column(Integer)
    video_path = Column(String(2083))
    video_url = Column(String(2083))
    video_view_count = Column(Integer)
    video_like_count = Column(Integer)
    comment_count = Column(Integer)
    video_share_count = Column(Integer)
    video_download_count = Column(Integer)
    video_posted_timestamp = Column(DateTime)
    request_id = Column(Integer)
    crawling_timestamp = Column(DateTime)
    video_source = Column(String(255))
    video_save_count = Column(Integer)
    profile_id = Column(String(255))
    user_handle = Column(String(255))
    creator_photo_link = Column(LONGTEXT)
    video_hashtags = Column(String(1000))
    user_followers_count = Column(Integer)
    user_following_count = Column(Integer)
    user_total_videos = Column(Integer)
    comments = Column(Text)
    tiktok = Column(Boolean)
    news = Column(Boolean)
    value = Column(String(255))
    video_description = Column(LONGTEXT)
    video_language = Column(String(50))
    transcription = Column(LONGTEXT)
    video_summary = Column(LONGTEXT)
    agent_name = Column(String(255))


class TikTokTableSchemaIn(Base):
    __tablename__ = TablesName.tiktok_table_name
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_mongodb_id = Column(String(255), unique=True)
    video_id = Column(String(255))
    region = Column(String(10))
    title = Column(LONGTEXT)
    video_screenshot = Column(String(2083))
    video_duration_seconds = Column(Integer)
    video_path = Column(String(2083))
    video_url = Column(String(2083))
    video_view_count = Column(Integer)
    video_like_count = Column(Integer)
    comment_count = Column(Integer)
    video_share_count = Column(Integer)
    video_download_count = Column(Integer)
    video_posted_timestamp = Column(DateTime)
    request_id = Column(Integer)
    crawling_timestamp = Column(DateTime)
    video_source = Column(String(255))
    video_save_count = Column(Integer)
    profile_id = Column(String(255))
    user_handle = Column(String(255))
    creator_photo_link = Column(LONGTEXT)
    video_hashtags = Column(String(1000))
    user_followers_count = Column(Integer)
    user_following_count = Column(Integer)
    user_total_videos = Column(Integer)
    comments = Column(Text)
    tiktok = Column(Boolean)
    news = Column(Boolean)
    value = Column(String(255))
    video_description = Column(LONGTEXT)
    video_language = Column(String(50))
    transcription = Column(LONGTEXT)
    video_summary = Column(LONGTEXT)
    agent_name = Column(String(255))
