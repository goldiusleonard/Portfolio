"""Module to define models for the sql tables."""

from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

# Base class for models
Base = declarative_base()


class TopicTable(Base):
    """TopicTable model class representing the topic_keywords_and_categories table in the database.

    The table stores the output of the topic keyword generation process.
    """

    __tablename__ = "topic_keywords_details"  # Name of the SQL table

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(255), nullable=False)
    category = Column(String(255), nullable=True)
    sub_category = Column(String(255), nullable=True)
    topic_category_id = Column(String(255), nullable=False)
    topic_summary = Column(String(255), nullable=False)
    relates_to = Column(String(255), nullable=True)
    purpose = Column(String(255), nullable=True)
    execution_method = Column(
        String(255),
        nullable=True,
    )
    target_person = Column(String(255), nullable=True)
    topic_updated_time = Column(String(255), nullable=False)
    category_id = Column(Integer, nullable=True, default=1)
    sub_category_id = Column(Integer, nullable=True, default=2)
    preprocessed_unbiased_id = Column(Integer, nullable=False, default=3)


class Category(Base):
    """Category model class representing the Category table in the database."""

    __tablename__ = "category"  # Or full path: marketplace_dev.category
    id = Column(Integer, primary_key=True)
    category_name = Column(String)


class SubCategory(Base):
    """Subcategory model class representing the SubCategory table in database."""

    __tablename__ = "sub_category"  # Or marketplace_dev.sub_category
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer)
    sub_category_name = Column(String)


class TopicCategory(Base):
    """TopicCategory model class representing the TopicCategory table in database."""

    __tablename__ = "topic_category"  # Or mcmc_business_agent.topic_category
    id = Column(Integer, primary_key=True)
    topic_category_name = Column(String)


class MappedCatSubcat(Base):
    """MappedCatSubcat model class representing the MappedCatSubcat table in database."""

    __tablename__ = "mapped_cat_sub"  # Or marketplace_dev.mapped_cat_sub
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer)
    sub_category_id = Column(Integer)
    video_id = Column(Integer)
    preprocessed_unbiased_id = Column(Integer)


class TopicsOnTheFly(Base):
    """TopicsOnTheFly model class representing the TopicsOnTheFly table in database."""

    __tablename__ = "topics_on_the_fly"  # Or mcmc_business_agent.TopicsOnTheFly
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer)
    topic_summary = Column(String(255), nullable=False)
    relates_to = Column(String(255), nullable=True)
    purpose = Column(String(255), nullable=True)
    execution_method = Column(
        String(255),
        nullable=True,
    )
    target_person = Column(String(255), nullable=True)
    topic_updated_time = Column(String(255), nullable=False)
