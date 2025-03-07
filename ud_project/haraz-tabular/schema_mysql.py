from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.declarative import declarative_base

# Base class for SQLAlchemy models
Base = declarative_base()


class Comment(Base):
    # __tablename__ = 'comments_cat_subcat'
    # __tablename__ = 'comments'
    # __tablename__ = 'z_comments_test'
    __tablename__ = "test_comments_cat_subcat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_mongodb_id = Column(String(255), unique=True)  # MongoDB ID
    video_comment_id = Column(String(255), nullable=False)
    video_id = Column(String(255), nullable=False)
    text = Column(LONGTEXT)
    comment_posted_timestamp = Column(DateTime)
    comment_like_count = Column(Integer)
    crawling_timestamp = Column(DateTime)
    request_id = Column(Integer)
    user_handle = Column(String(255))
    category = Column(String(45), nullable=False)
    subcategory = Column(String(45), nullable=False)
    video_summary = Column(LONGTEXT)


class Replies(Base):
    # __tablename__ = 'replies'
    __tablename__ = "test_replies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_mongodb_id = Column(String(255))
    video_comment_id = Column(String(255), nullable=False)
    reply_id = Column(String(255), nullable=False)
    video_id = Column(String(255), nullable=False)
    text = Column(LONGTEXT)
    reply_posted_timestamp = Column(DateTime)
    reply_like_count = Column(Integer)
    user_id = Column(String(255))
    user_region = Column(String(50))
    user_handle = Column(String(255))
    user_avatar = Column(String(1000))


class PreprocessedUnbiased(Base):
    # __tablename__ = 'preprocessed_unbiased'
    __tablename__ = "test_preprocessed_unbiased"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_mongodb_id = Column(String(255), unique=True)
    video_id = Column(String(255))
    region = Column(String(10))
    title = Column(LONGTEXT)
    video_screenshot = Column(String(2083))  # URL length # Cover image URL
    video_duration_seconds = Column(Integer)  # Video duration in seconds
    video_path = Column(String(2083))  # URL path to blob
    video_url = Column(String(2083))  # Watermarked tiktok play url
    video_view_count = Column(Integer)
    video_like_count = Column(Integer)  # number of "likes" / hearts
    comment_count = Column(Integer)
    video_share_count = Column(Integer)
    video_download_count = Column(Integer)  # Download count
    video_posted_timestamp = Column(DateTime)
    request_id = Column(String(255))
    crawling_timestamp = Column(DateTime)
    video_source = Column(String(255))
    video_save_count = Column(
        Integer
    )  # number of times a video has been added to favorites or collection
    profile_id = Column(String(255))  # creator's id
    user_handle = Column(String(255))  # creator username
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


class MappedCatSub(Base):
    # __tablename__ = 'mapped_cat_sub'
    __tablename__ = "test_mapped_cat_sub"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, nullable=False)
    sub_category_id = Column(Integer, nullable=False)
    video_id = Column(String(45), nullable=False)
    preprocessed_unbiased_id = Column(Integer, nullable=False)


class RequestID(Base):
    __tablename__ = "test_user_requestid"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_mongodb_id = Column(String(255), nullable=False)
    request_id = Column(Integer, nullable=False)
    video_id = Column(String(45), nullable=False)
    category = Column(String(45), nullable=False)
    subcategory = Column(String(45), nullable=False)
    crawling_timestamp = Column(DateTime)
    video_source = Column(String(255))
    value = Column(String(255))


# ----- DIRECT LINK SCHEMAS ----- #


class DirectLinkComment(Base):
    __tablename__ = "directlink_comments_test"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_mongodb_id = Column(String(255), unique=True)  # MongoDB ID
    video_comment_id = Column(String(255), nullable=False)
    video_id = Column(String(255), nullable=False)
    text = Column(LONGTEXT)
    comment_posted_timestamp = Column(DateTime)
    comment_like_count = Column(Integer)
    crawling_timestamp = Column(DateTime)
    request_id = Column(Integer)
    user_handle = Column(String(255))
    # category = Column(String(45), nullable=False)
    # subcategory = Column(String(45), nullable=False)
    video_summary = Column(LONGTEXT)


class DirectLinkReplies(Base):
    __tablename__ = "directlink_replies_test"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_mongodb_id = Column(String(255))
    video_comment_id = Column(String(255), nullable=False)
    reply_id = Column(String(255), nullable=False)
    video_id = Column(String(255), nullable=False)
    text = Column(LONGTEXT)
    reply_posted_timestamp = Column(DateTime)
    reply_like_count = Column(Integer)
    user_id = Column(String(255))
    user_region = Column(String(50))
    user_handle = Column(String(255))
    user_avatar = Column(String(1000))


class DirectLinkRequestID(Base):
    __tablename__ = "directlink_user_requestid_test"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_mongodb_id = Column(String(255), nullable=False)
    request_id = Column(Integer, nullable=False)
    video_id = Column(String(45), nullable=False)
    # category = Column(String(45), nullable=False)
    # subcategory = Column(String(45), nullable=False)
    crawling_timestamp = Column(DateTime)
    video_source = Column(String(255))
    value = Column(String(255))


class DirectLinkPreprocessed(Base):
    __tablename__ = "directlink_preprocessed_test"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_mongodb_id = Column(String(255), unique=True)
    video_id = Column(String(255))
    region = Column(String(10))
    title = Column(LONGTEXT)
    video_screenshot = Column(String(2083))  # URL length # Cover image URL
    video_duration_seconds = Column(Integer)  # Video duration in seconds
    video_path = Column(String(2083))  # URL path to blob
    video_url = Column(String(2083))  # Watermarked tiktok play url
    video_view_count = Column(Integer)
    video_like_count = Column(Integer)  # number of "likes" / hearts
    comment_count = Column(Integer)
    video_share_count = Column(Integer)
    video_download_count = Column(Integer)  # Download count
    video_posted_timestamp = Column(DateTime)
    request_id = Column(String(255))
    crawling_timestamp = Column(DateTime)
    video_source = Column(String(255))
    video_save_count = Column(
        Integer
    )  # number of times a video has been added to favorites or collection
    profile_id = Column(String(255))  # creator's id
    user_handle = Column(String(255))  # creator username
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
