"""Docstring."""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, func, inspect
from zoneinfo import ZoneInfo

# Your existing imports for these:
from app.core.dependencies import get_input_db, get_output_db
from utils.models.models import (
    Category,
    MappedCatSubcat,
    SubCategory,
    TopicCategory,
    TopicsOnTheFly,
    TopicTable,
)

if TYPE_CHECKING:
    from logger import Logger
    from sqlalchemy.orm import Session

# Constants
malaysia_tz = ZoneInfo("Asia/Kuala_Lumpur")
BATCH_SIZE = 50


class DatabaseHandler:
    """Handles all database interactions.

    connecting, loading data, querying, and inserting/updating records.
    """

    def __init__(self, logger: Logger) -> None:
        """Initialize the DatabaseHandler instance."""
        self.logger: Logger = logger
        load_dotenv(override=True)

        # Environment variable for table name
        self.marketplace_table: str | None = os.getenv("MARKETPLACE_TABLE")

        # Metadata objects
        self.input_metadata: MetaData = MetaData()
        self.output_metadata: MetaData = MetaData()

    # ------------------------------------------------------------------------
    # Helpers to handle optional Sessions
    # ------------------------------------------------------------------------

    def _get_or_create_input_db_session(self, db: Session | None) -> Session:
        """Return the given `db` if not None, else create a new session from get_input_db()."""
        if db is not None:
            return db
        return next(get_input_db())  # calls the generator and returns a fresh session

    def _get_or_create_output_db_session(self, db: Session | None) -> Session:
        """Return the given `db` if not None, else create a new session from get_output_db()."""
        if db is not None:
            return db
        return next(get_output_db())

    # ------------------------------------------------------------------------
    # Session-Injected / Session-Optional Methods
    # ------------------------------------------------------------------------

    def _reflect_table_schema(
        self,
        db: Session | None = None,
    ) -> Table | None:
        """Reflect the SQL table schema for the marketplace table (input DB)."""
        db = self._get_or_create_input_db_session(db)

        try:
            self.input_metadata.clear()
            table = Table(
                self.marketplace_table,
                self.input_metadata,
                autoload_with=db.bind,
            )
        except Exception:
            self.logger.exception("Error while reflecting table schema")
            return None
        else:
            return table

    def _get_all_existing_topics(
        self,
        db: Session | None = None,
    ) -> pd.DataFrame:
        """Fetch all existing data from TopicTable as a DataFrame (output DB)."""
        db = self._get_or_create_output_db_session(db)
        existing_data = db.query(TopicTable).all()
        df_existing = pd.DataFrame([row.__dict__ for row in existing_data])
        if "_sa_instance_state" in df_existing.columns:
            df_existing = df_existing.drop("_sa_instance_state", axis=1)
        return df_existing

    def load_video_data(
        self,
        limit: int | None = None,
        db: Session | None = None,
    ) -> pd.DataFrame:
        """Load video data from the input SQL database for processing."""
        db = self._get_or_create_input_db_session(db)
        sql_table = self._reflect_table_schema(db=db)
        if sql_table is None:
            self.logger.error("No SQL table schema found.")
            return pd.DataFrame()

        try:
            query = sql_table.select()
            if limit:
                query = query.limit(limit)

            result = db.execute(query)
            df_vid_data = pd.DataFrame(result.fetchall(), columns=result.keys())
            self.logger.debug("Data fetched from SQL:\n%s", df_vid_data)
        except Exception:
            self.logger.exception("Error while loading data from MySQL")
            return pd.DataFrame()
        else:
            return df_vid_data

    def table_exists_and_count(
        self,
        db: Session | None = None,
    ) -> tuple[bool, int]:
        """Check if the TopicTable exists and return the row count (output DB)."""
        db = self._get_or_create_output_db_session(db)
        inspector = inspect(db.bind)
        table_exists = inspector.has_table(TopicTable.__tablename__)
        row_count = db.query(func.count()).select_from(TopicTable).scalar()
        return table_exists, row_count

    def query_existing_data(
        self,
        db: Session | None = None,
    ) -> pd.DataFrame:
        """Fetch all existing data from TopicTable as a DataFrame (output DB)."""
        return self._get_all_existing_topics(db=db)

    def insert_data(
        self,
        df_to_insert: pd.DataFrame,
        db: Session | None = None,
        batch_size: int = BATCH_SIZE,
    ) -> None:
        """Insert new categorized data into TopicCategory and TopicTable."""
        if df_to_insert.empty:
            self.logger.info("No data to insert.")
            return

        db = self._get_or_create_output_db_session(db)

        # Step 1: Insert unique topic categories into TopicCategory
        unique_categories = df_to_insert["topic_category"].unique().tolist()
        self._insert_topic_categories(unique_categories, db=db)

        # Step 2: Fetch topic_category_name-to-id mapping
        category_mapping = self.get_topic_category_mapping(db=db)

        # Step 3: Map topic_category_name -> topic_category_id
        df_to_insert["topic_category_id"] = df_to_insert["topic_category"].map(
            category_mapping,
        )
        df_to_insert = df_to_insert.drop("topic_category", axis=1)

        # Step 4: Ensure table is created, set updated time, and insert
        self._create_topic_table_if_not_exists(db=db)
        df_to_insert["topic_updated_time"] = datetime.now(malaysia_tz)
        data_to_insert = df_to_insert.to_dict(orient="records")
        self._bulk_insert(data=data_to_insert, db=db, batch_size=batch_size)

        self.logger.info(
            "Data inserted successfully into both TopicCategory and TopicTable.",
        )

    def reinsert_all_data(
        self,
        input_df: pd.DataFrame,
        db: Session | None = None,
        batch_size: int = BATCH_SIZE,
    ) -> None:
        """Re-insert or update all data to the database (output DB), handling topic categories."""
        db = self._get_or_create_output_db_session(db)

        existing_df = self._get_all_existing_topics(db=db)
        self.logger.debug("Existing data: %d records.", len(existing_df))
        self.logger.debug("Input data: %d records.", len(input_df))

        # Identify new and changed records
        new_records, updates = self._identify_records_to_update_or_insert(
            input_df,
            existing_df,
        )

        # Step 2: Process topic categories for new records
        if not new_records.empty:
            unique_categories = new_records["topic_category"].unique().tolist()
            self._insert_topic_categories(unique_categories, db=db)

            category_mapping = self.get_topic_category_mapping(db=db)
            new_records["topic_category_id"] = new_records["topic_category"].map(
                category_mapping,
            )
            new_records = new_records.drop("topic_category", axis=1)

        # Step 3: Process updates
        if updates:
            self._bulk_update(updates=updates, db=db, batch_size=batch_size)
            self.logger.debug("Batch updates completed successfully.")

        # Step 4: Process inserts
        if not new_records.empty:
            new_records["topic_updated_time"] = datetime.now(malaysia_tz)
            new_data = new_records.to_dict(orient="records")
            self._bulk_insert(data=new_data, db=db, batch_size=batch_size)
            self.logger.debug("Inserted %d new records.", len(new_data))

        db.commit()
        self.logger.info("Database updated successfully.")

    def check_new_ids(
        self,
        df: pd.DataFrame,
        db: Session | None = None,
    ) -> list[int]:
        """Check for new preprocessed_unbiased_ids not yet processed in TopicTable (output DB)."""
        db = self._get_or_create_output_db_session(db)
        inspector = inspect(db.bind)
        table_exists = inspector.has_table(TopicTable.__tablename__)

        # Filter for region & language
        supported_language = ["en", "ms"]
        supported_region = ["MY"]
        filtered_df = df[
            df["region"].isin(supported_region)
            & df["video_language"].isin(supported_language)
        ]

        if not table_exists:
            self.logger.info("Table does not exist. Returning all filtered ids.")
            return filtered_df["preprocessed_unbiased_id"].tolist()

        existing_ids_set = {
            row.preprocessed_unbiased_id
            for row in db.query(TopicTable.preprocessed_unbiased_id).distinct().all()
        }

        input_ids_set = set(filtered_df["id"].tolist())
        new_ids = list(input_ids_set - existing_ids_set)
        self.logger.info("Found '%s' new IDs that meet the criteria.", len(new_ids))
        return new_ids

    # ---------------------------
    # Category / Subcategory Mappings (Input DB)
    # ---------------------------
    def get_category_id_mapping(
        self,
        db: Session | None = None,
    ) -> dict[int, str]:
        """Retrieve category (id -> name) mapping from 'category' table (input DB)."""
        db = self._get_or_create_input_db_session(db)
        categories = db.query(Category).all()
        mapping = {c.id: c.category_name for c in categories}
        self.logger.debug("Fetched category mapping: %s", mapping)
        return mapping

    def get_subcategory_id_mapping(
        self,
        db: Session | None = None,
    ) -> dict[int, str]:
        """Retrieve subcategory (id -> name) mapping from 'sub_category' table (input DB)."""
        db = self._get_or_create_input_db_session(db)
        subcategories = db.query(SubCategory).all()
        mapping = {sc.id: sc.sub_category_name for sc in subcategories}
        self.logger.debug("Fetched subcategory mapping: %s", mapping)
        return mapping

    def get_category_mapping(
        self,
        db: Session | None = None,
    ) -> dict[str, int]:
        """Retrieve category (name -> id) mapping from 'category' table (input DB)."""
        db = self._get_or_create_input_db_session(db)
        categories = db.query(Category).all()
        mapping = {c.category_name: c.id for c in categories}
        self.logger.debug("Fetched category mapping: %s", mapping)
        return mapping

    def get_subcategory_mapping(
        self,
        db: Session | None = None,
    ) -> dict[str, int]:
        """Retrieve subcategory (name -> id) mapping from 'sub_category' table (input DB)."""
        db = self._get_or_create_input_db_session(db)
        subcategories = db.query(SubCategory).all()
        return {sc.sub_category_name: sc.id for sc in subcategories}

    def insert_category_subcategory_names_into_df(
        self,
        df: pd.DataFrame,
        db: Session | None = None,
    ) -> pd.DataFrame:
        """Enrich a DataFrame with category/subcategory names (input DB)."""
        if df.empty:
            self.logger.info("DataFrame is empty. No enrichment performed.")
            return df

        db = self._get_or_create_input_db_session(db)

        # Determine join key
        if "preprocessed_unbiased_id" in df.columns:
            key_column = "preprocessed_unbiased_id"
            mapped_key = MappedCatSubcat.preprocessed_unbiased_id
        elif "video_id" in df.columns:
            key_column = "video_id"
            mapped_key = MappedCatSubcat.video_id
        else:
            self.logger.error(
                "DataFrame must contain 'video_id' or 'preprocessed_unbiased_id' to proceed.",
            )
            return df

        unique_ids = df[key_column].dropna().unique().tolist()
        if not unique_ids:
            self.logger.info("No valid IDs found in the DataFrame for enrichment.")
            return df

        mappings = db.query(MappedCatSubcat).filter(mapped_key.in_(unique_ids)).all()
        map_df = pd.DataFrame([m.__dict__ for m in mappings])
        if "_sa_instance_state" in map_df.columns:
            map_df = map_df.drop("_sa_instance_state", axis=1)

        if key_column == "preprocessed_unbiased_id":
            map_df = map_df.drop(["video_id"], axis=1)

        merged_df = df.merge(map_df, how="left", on=key_column)

        # Map IDs to names
        cat_mapping = self.get_category_id_mapping(db=db)
        subcat_mapping = self.get_subcategory_id_mapping(db=db)
        merged_df["category"] = merged_df["category_id"].map(cat_mapping)
        merged_df["sub_category"] = merged_df["sub_category_id"].map(subcat_mapping)
        return merged_df

    # ---------------------------
    # Topic Category Mappings (Output DB)
    # ---------------------------
    def retrieve_existing_categories(
        self,
        db: Session | None = None,
    ) -> dict[str, list[str]]:
        """Retrieve existing categories from the output DB for category assignment."""
        db = self._get_or_create_output_db_session(db)

        try:
            topic_category_mapping = self.get_topic_category_mapping(db=db)
            inverted_mapping = {v: k for k, v in topic_category_mapping.items()}
        except Exception:
            self.logger.exception("Error retrieving category mappings")
            return {}

        try:
            query = (
                db.query(TopicTable.sub_category, TopicTable.topic_category_id)
                .distinct()
                .all()
            )
            df_existing = pd.DataFrame(
                query,
                columns=["sub_category", "topic_category_id"],
            )

            if df_existing.empty:
                return {}

            df_existing["topic_category_name"] = df_existing["topic_category_id"].map(
                inverted_mapping,
            )
            grouped = (
                df_existing.groupby("sub_category")["topic_category_name"]
                .apply(lambda x: sorted(set(x)))
                .to_dict()
            )
        except Exception:
            self.logger.exception("Error retrieving existing categories")
            return {}
        else:
            return grouped

    def get_topic_category_mapping(
        self,
        db: Session | None = None,
    ) -> dict[str, int]:
        """Retrieve mapping of topic_category_name -> id from TopicCategory (output DB)."""
        db = self._get_or_create_output_db_session(db)
        categories = db.query(TopicCategory.id, TopicCategory.topic_category_name).all()
        mapping = {cat.topic_category_name: cat.id for cat in categories}
        self.logger.debug("Fetched topic category mapping: %s", mapping)
        return mapping

    def get_video_to_cat_subcat_id_mapping(
        self,
        db: Session | None = None,
    ) -> pd.DataFrame:
        """Retrieve video-to-category-subcategory mappings from mapped_cat_sub_for_aiman (input DB)."""
        db = self._get_or_create_input_db_session(db)
        mappings = db.query(MappedCatSubcat).all()
        df_mappings = pd.DataFrame([m.__dict__ for m in mappings])
        if "_sa_instance_state" in df_mappings.columns:
            df_mappings = df_mappings.drop("_sa_instance_state", axis=1)
        return df_mappings

    # ------------------------------------------------------------------------
    # Private Helper Methods
    # ------------------------------------------------------------------------

    def _create_topic_table_if_not_exists(
        self,
        db: Session | None = None,
    ) -> None:
        """Create TopicTable if it doesn't exist (output DB)."""
        db = self._get_or_create_output_db_session(db)
        inspector = inspect(db.bind)
        if not inspector.has_table(TopicTable.__tablename__):
            self.logger.info(
                "Table '%s' does not exist. Creating the table...",
                TopicTable.__tablename__,
            )
            TopicTable.__table__.create(db.bind)

    def _bulk_insert(
        self,
        data: list[dict[str, Any]],
        db: Session | None = None,
        batch_size: int = BATCH_SIZE,
    ) -> None:
        """Perform bulk insert of data into TopicTable (output DB)."""
        db = self._get_or_create_output_db_session(db)
        total_records = len(data)
        self.logger.debug("Total records to insert: %d", total_records)

        for i in range(0, total_records, batch_size):
            batch = data[i : i + batch_size]
            self.logger.debug(
                "Inserting batch %d - %d of %d records.",
                i + 1,
                min(i + batch_size, total_records),
                total_records,
            )
            db.bulk_insert_mappings(TopicTable, batch)
        db.commit()

    def _bulk_update(
        self,
        updates: list[dict[str, Any]],
        db: Session | None = None,
        batch_size: int = BATCH_SIZE,
    ) -> None:
        """Perform bulk updates of existing records in TopicTable (output DB)."""
        db = self._get_or_create_output_db_session(db)
        total_updates = len(updates)
        self.logger.debug("Performing %d updates.", total_updates)

        for i in range(0, total_updates, batch_size):
            batch = updates[i : i + batch_size]
            self.logger.debug(
                "Updating batch %d - %d of %d records.",
                i + 1,
                min(i + batch_size, total_updates),
                total_updates,
            )
            db.bulk_update_mappings(TopicTable, batch)
        db.commit()

    def _identify_records_to_update_or_insert(
        self,
        input_df: pd.DataFrame,
        existing_df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, list[dict]]:
        """Identify new and changed records by comparing input_df with existing_df."""
        # Mark new records
        input_df["is_new"] = ~input_df["preprocessed_unbiased_id"].isin(
            existing_df["preprocessed_unbiased_id"].to_numpy(),
        )
        new_records = input_df[input_df["is_new"]]
        existing_records = input_df[~input_df["is_new"]]

        self.logger.debug(
            "New records: %d, Existing records: %d.",
            len(new_records),
            len(existing_records),
        )

        updates = []
        if not existing_records.empty:
            merged_df = existing_records.merge(
                existing_df,
                on="preprocessed_unbiased_id",
                suffixes=("_new", "_old"),
            )
            exclude_columns = {
                "preprocessed_unbiased_id",
                "topic_updated_time",
                "is_new",
            }
            columns_to_compare = [
                col for col in existing_records.columns if col not in exclude_columns
            ]

            # If "topic_category" is in input, use "topic_category_id" for comparison
            if "topic_category" in columns_to_compare:
                columns_to_compare.remove("topic_category")
            if "topic_category_id" not in columns_to_compare:
                columns_to_compare.append("topic_category_id")

            try:
                changed_rows = merged_df[
                    (
                        merged_df[
                            [f"{col}_new" for col in columns_to_compare]
                        ].to_numpy()
                        != merged_df[
                            [f"{col}_old" for col in columns_to_compare]
                        ].to_numpy()
                    ).any(axis=1)
                ]

                self.logger.debug("Number of changed rows: %d", len(changed_rows))

                # Build update dict
                updates = [
                    {
                        **{col: row[f"{col}_new"] for col in columns_to_compare},
                        "id": row["id_old"],
                        "topic_updated_time": datetime.now(malaysia_tz),
                    }
                    for _, row in changed_rows.iterrows()
                ]
            except KeyError:
                self.logger.exception(
                    "KeyError occurred while comparing DataFrame columns: %s",
                    merged_df.columns.tolist(),
                )
                raise

        # Return new records (dropping ephemeral columns) and updates
        return new_records.drop(columns=["is_new", "id"], errors="ignore"), updates

    def _insert_topic_categories(
        self,
        categories: list[str],
        db: Session | None = None,
    ) -> None:
        """Insert unique topic categories into TopicCategory (output DB)."""
        db = self._get_or_create_output_db_session(db)
        category_set = set(categories)
        if not category_set:
            self.logger.info("No category names provided.")
            return

        existing = (
            db.query(TopicCategory.topic_category_name)
            .filter(TopicCategory.topic_category_name.in_(category_set))
            .all()
        )
        existing_category_names = {x[0] for x in existing}
        new_category_names = category_set - existing_category_names

        if not new_category_names:
            self.logger.info("No new categories to insert.")
            return

        new_topic_categories = [
            TopicCategory(topic_category_name=name) for name in new_category_names
        ]

        db.add_all(new_topic_categories)
        db.commit()

        self.logger.info(
            "Inserted %d new topic category(ies).",
            len(new_topic_categories),
        )

    # ------------------------------------------------------------------------
    # On-The-Fly Table Insertion
    # ------------------------------------------------------------------------

    def insert_to_db_on_the_fly(
        self,
        response: dict,
        db: Session | None = None,
    ) -> None:
        """Insert a new record into the topics_on_the_fly table using data from the response dictionary."""
        db = self._get_or_create_output_db_session(db)
        try:
            new_topic = TopicsOnTheFly(
                video_id=response.get("video_id"),
                topic_summary=response.get("topic_summary"),
                relates_to=response.get("relates_to"),
                purpose=response.get("purpose"),
                execution_method=response.get("execution_method"),
                target_person=response.get("target_person"),
                topic_updated_time=datetime.now(malaysia_tz),
            )
            db.add(new_topic)
            db.commit()

            self.logger.info("Record successfully inserted into topics_on_the_fly.")
        except Exception:
            db.rollback()
            self.logger.exception("Error inserting record")
            raise
