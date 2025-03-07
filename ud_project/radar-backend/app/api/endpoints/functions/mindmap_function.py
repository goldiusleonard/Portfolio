"""CROSS CATEGORY INSIGHT MINDMAP ."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

import pandas as pd
from fastapi import APIRouter
from sqlalchemy import text

from app.core.vm_db import Session_Vm
from app.core.vm_mongo_db import MongoClient  # noqa: TCH001

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Create an API router
filter_label_router = APIRouter()


async def generate_json_by_category(
    df: pd.DataFrame,
    db: MongoClient,
) -> list[dict[str, Any]]:
    """Structure the JSON from the input DataFrame."""
    # Initialize the list for mind map data
    mind_map_data = []

    # Group by category
    grouped_categories = df.groupby("category")

    for category, category_group in grouped_categories:
        # Get category ID from the DataFrame
        category_id = str(category_group["category_id"].iloc[0])

        # Calculate aiFlaggedCount for the category
        category_ai_flagged_count = len(category_group)

        # Initialize the top-level JSON structure for each category
        category_node = {
            "id": category_id,
            "label": category,
            "aiFlaggedCount": str(category_ai_flagged_count),
            "newsCount": str(
                await news_count(category, db),
            ),  # getting news count from the mongoDB news_articles
            "key": "category",
            "children": [],
        }

        # Group by sub_category within each category
        grouped_sub_categories = category_group.groupby("sub_category")

        for sub_category, sub_category_group in grouped_sub_categories:
            # Get sub-category ID from the DataFrame
            sub_category_id = str(sub_category_group["sub_category_id"].iloc[0])

            # Initialize subcategory node
            sub_category_node = {
                "id": sub_category_id,
                "label": sub_category,
                "key": "subCategory",
                "children": [],
            }

            # Add topics under each subcategory
            topic_counts = (
                sub_category_group.groupby(["topic", "topic_id"])["video_id"]
                .count()
                .reset_index()
            )
            topic_counts = topic_counts.rename(columns={"video_id": "topic_count"})

            unique_topics = topic_counts.drop_duplicates(subset=["topic"])

            for _, topic_row in unique_topics.iterrows():
                topic_node = {
                    "id": str(topic_row["topic_id"]),
                    "label": topic_row["topic"],
                    "key": "topic",
                    "aiFlaggedCount": str(
                        topic_row["topic_count"],
                    ),  # Use topic_count as aiFlaggedCount
                }
                sub_category_node["children"].append(topic_node)

            # Add subcategory node to category's children
            category_node["children"].append(sub_category_node)

        # Append the category node to mind map data
        mind_map_data.append(category_node)

    return mind_map_data


async def news_count(category: str, db: type[MongoClient]) -> int:
    """Get the news count for the specific category."""
    query = {"category": {"$in": [category]}} if category else {}

    return await db.news_articles.count_documents(query)


def sqltodf(session_vm: Callable[[], Session] = Session_Vm) -> pd.DataFrame:
    """Fetch data from the database using the given session and return a processed DataFrame.

    Args:
        session_vm (Any): The session factory for database interaction.

    Returns:
        pd.DataFrame: A processed DataFrame containing the data.

    """
    query = """
    SELECT t.video_id, t.category, t.category_id, t.sub_category, t.sub_category_id, c.risk_status,
           tc.topic_category_name AS topic, t.topic_category_id AS topic_id, t.topic_summary
    FROM mcmc_business_agent.topic_keywords_details t
    LEFT JOIN mcmc_business_agent.ba_content_data_asset c ON t.video_id = c.video_id
    LEFT JOIN mcmc_business_agent.topic_category tc ON tc.id = t.topic_category_id
    WHERE c.risk_status IN ('low', 'medium', 'high')
    """
    with session_vm() as session:  # Using the passed session factory
        result = session.execute(text(query))
        rows = result.fetchall()
        # Get column names
        columns = result.keys()
        # Create a DataFrame
        data_frame = pd.DataFrame(rows, columns=columns)

    # Group the data to calculate topic counts
    grouped_df = (
        data_frame.groupby(["category", "sub_category", "topic"])["video_id"]
        .count()
        .reset_index()
    )
    grouped_df = grouped_df.rename(columns={"video_id": "topic_count"})

    # Merge the grouped data back to the original DataFrame
    return data_frame.merge(
        grouped_df,
        on=["category", "sub_category", "topic"],
        how="left",
    )


def find_node(data: list[dict[str, Any]], label: str) -> dict[str, Any] | None:
    """Find a node in the data list by its label.

    Args:
        data (List[Dict[str, Any]]): A list of nodes, each represented as a dictionary.
        label (str): The label to search for.

    Returns:
        Optional[Dict[str, Any]]: The node dictionary if found, otherwise `None`.

    """
    for node in data:
        if node["label"].lower().strip() == label.lower().strip():
            return node
    return None
