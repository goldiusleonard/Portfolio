"""Main module for Topic Keyword Generator.

Generate the topic keyword from video summary.
"""

from __future__ import annotations

import ast
from datetime import datetime

import pandas as pd
from zoneinfo import ZoneInfo

from utils.connections import DatabaseHandler
from utils.llm_handler import LLMHandler
from utils.logger import Logger

pd.set_option("display.max_columns", None)

# Constants
MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")
THRESHOLD = 20
BATCH_SIZE = 50
QUERY_LIMIT = None  # Set to None to process all
MAX_CATEGORIES = 10
DEFAULT_NUM_CATEGORIES = 5


class TopicKeywordGenerator:
    """Orchestrates topic & keyword generation, categorization, reassignment, and database persistence."""

    def __init__(self) -> None:
        """Initialize dependencies and load initial data."""
        # Initialize dependency classes
        self.logger = Logger(name="log.log", log_dir="app/logs/")
        self.db_handler = DatabaseHandler(logger=self.logger)
        self.llm_handler = LLMHandler(logger=self.logger)

        # Load category and subcategory mappings
        self.category_id_to_name = self.db_handler.get_category_id_mapping()
        self.sub_category_id_to_name = self.db_handler.get_subcategory_id_mapping()

        # Load initial data
        self.df = self.db_handler.load_video_data(limit=QUERY_LIMIT)

        self._map_category_sub_category_id_names()
        # DataFrames for intermediate results
        self.df_topic_keywords: pd.DataFrame = pd.DataFrame()
        self.df_topic_categorized: pd.DataFrame = pd.DataFrame()

    def run(self) -> tuple[int, int]:
        """Run the entire topic keyword generation and categorization process.

        Checks if the output table exists and has any rows. If it does not exist
        or is empty, processes all video IDs. If it exists and has rows, only
        processes new video IDs.

        Returns:
            tuple[int, int]: The number of new video IDs and the number of new
            IDs inserted.

        """
        self.logger.info("Starting TopicKeywordGeneration process.")

        # Check if output table exists and count rows
        table_exists, row_count = self.db_handler.table_exists_and_count()
        self.logger.info(
            "Output table exists: %s, Row count: %s",
            table_exists,
            row_count,
        )

        if table_exists and row_count == 0:
            # If the output table exists but has no rows, process all video IDs
            self.logger.info(
                "Output table exists but has no rows. Processing all video IDs.",
            )
            number_of_new_ids, number_of_new_ids_inserted = (
                self._process_all_video_ids()
            )
            if number_of_new_ids_inserted == 0:
                self.logger.info("No new IDs to insert. Exiting.")
            return number_of_new_ids, number_of_new_ids_inserted

        # If the output table exists and has rows, only process new video IDs
        self.logger.info("Output table exists and has rows. Processing new video IDs.")
        return self._process_new_video_ids()

    # ------------------------- High-Level Processes -------------------------
    def process_on_the_fly(self, payload: dict | str) -> dict:
        """Generate topics and keywords for each video using the LLM."""
        if isinstance(payload, str):
            payload = ast.literal_eval(payload)
        video_summary = payload.get("video_summary")
        video_id = payload.get("video_id")

        llm_prompt = self.llm_handler.get_prompt_topic_keywords(
            video_summary=video_summary,
        )
        response = self.llm_handler.call_llm_with_retry(
            llm_prompt,
            video_id=None,
        )

        if response:
            response = response.replace("'", '"')
            try:
                if response.startswith("{") and response.endswith("}"):
                    response_dict = ast.literal_eval(response)
                    # Add video_id to the response
                    response_dict["video_id"] = video_id
                    self.db_handler.insert_to_db_on_the_fly(response_dict)
                    return response_dict

            except ValueError:
                self.logger.exception("LLM output invalid")
        return "Error Processing Video(s)"

    def _process_all_video_ids(self) -> None:
        """Process all videos when the output table is empty.

        This method generates topics and categories for the entire dataset
        and inserts the categorized data into the database.

        Returns:
            tuple[int, int]: The number of video IDs processed and the number
            of records inserted into the database.

        """
        # Log the start of processing for the entire dataset
        self.logger.info("No existing data. Processing entire dataset.")
        supported_language = ["en", "ms"]
        supported_region = ["MY"]
        filtered_df = self.df[
            (self.df["region"].isin(supported_region))  # Dynamic filtering for region
            & (
                self.df["video_language"].isin(supported_language)
            )  # Filter for languages
        ]
        # Generate topics and keywords for each video in the dataset
        self.df_topic_keywords = self._generate_topics_keywords(filtered_df)

        # Assign categories to the generated topics
        self.df_topic_categorized = (
            self._generate_topic_categories_per_subcategory_and_assign(
                self.df_topic_keywords,
            )
        )

        # Reassign topics categorized as 'Others' if needed
        self._reassign_others_if_needed(
            self.df_topic_categorized,
            target_attr="df_topic_categorized",
        )

        # Insert the categorized data into the database and return the count of processed IDs
        return len(filtered_df), self._insert_data_into_db(self.df_topic_categorized)

    def _process_new_video_ids(self) -> tuple[int, int]:
        """Process only newly identified videos.

        This method filters the input DataFrame for only newly identified video IDs,
        generates topics and categories for these new videos, and inserts the categorized
        data into the database.

        Returns:
            tuple[int, int]: The number of new IDs processed and the number of records
            inserted into the database.

        """
        # Check if there are any new IDs to process
        new_ids = self.db_handler.check_new_ids(self.df)
        if not new_ids:
            self.logger.info("No new IDs to process. Exiting.")
            return 0, 0

        self.logger.info("Processing new IDs only.")
        # Filter the DataFrame for only newly identified video IDs
        self.df = self.df[self.df["id"].isin(new_ids)]

        # Generate topics and keywords for the new videos
        self.df_topic_keywords = self._generate_topics_keywords(self.df)

        # Update newly generated topics with previously known categories, if available
        self._update_topics_with_existing_categories()

        # Reassign topics categorized as 'Others' if needed
        self._reassign_others_if_needed(
            self.df_topic_categorized,
            target_attr="df_topic_categorized",
        )

        # Map category and subcategory IDs to names
        self.df_topic_categorized = self._map_category_sub_category_names(
            self.df_topic_categorized,
        )

        # Insert the categorized data into the database and return the count of processed IDs
        return len(new_ids), self._insert_data_into_db(self.df_topic_categorized)

    def _update_topics_with_existing_categories(self) -> None:
        """Update newly generated topics with previously known categories, if available.

        This function enriches 'df_topic_keywords' with category and subcategory names,
        retrieves existing categories from the database, and assigns these categories
        to the new topics if possible.
        """
        # Enrich DataFrame with category and subcategory names
        self.df_topic_keywords = (
            self.db_handler.insert_category_subcategory_names_into_df(
                self.df_topic_keywords,
            )
        )

        # Remove the 'id' column as it is no longer needed
        self.df_topic_keywords = self.df_topic_keywords.drop("id", axis=1)

        # Retrieve existing categories from the database
        existing_categories_map = self.db_handler.retrieve_existing_categories()
        self.logger.debug("Existing category map: %s", existing_categories_map)

        # Check if there are new topics or existing categories to assign
        if self.df_topic_keywords.empty or not existing_categories_map:
            self.logger.info(
                "No existing categories to assign or no new topics generated.",
            )
            return

        # Assign existing categories to the new topics
        self.df_topic_categorized = self._assign_existing_topic_categories(
            self.df_topic_keywords,
            existing_categories_map,
        )

    def _reassign_others_if_needed(self, df: pd.DataFrame, target_attr: str) -> None:
        """Check if 'Others' category in subcategories exceeds threshold and reassign if needed.

        This function analyzes the percentage of topics categorized as 'Others' in the
        given DataFrame. If the percentage exceeds a predefined threshold for any subcategory,
        it reassigns the topics to reduce the 'Others' percentage.

        Args:
            df (pd.DataFrame): The DataFrame containing categorized topics.
            target_attr (str): The attribute name of the DataFrame to update with reassigned topics.

        """
        # Query existing data from the database
        df_existing = self.db_handler.query_existing_data()
        # Store the existing data for further analysis
        self.df_existing = df_existing

        # Combine existing and new categorized data
        df_combined = pd.concat(
            [df_existing, self.df_topic_categorized],
            ignore_index=True,
            sort=False,
        )

        # Analyze the percentage of 'Others' in the given DataFrame
        others_analysis = self._analyze_others_percentage(df)
        # Identify subcategories where 'Others' exceeds the threshold
        subcategories_to_update = (
            others_analysis.loc[
                others_analysis["percentage"] > THRESHOLD,
                "sub_category",
            ]
            .unique()
            .tolist()
        )

        if subcategories_to_update:
            # Log information about 'Others' exceeding the threshold
            self.logger.info(
                "'Others' > %s%% for subcategories %s. Reassigning...",
                THRESHOLD,
                subcategories_to_update,
            )
            # Reassign topics for identified subcategories
            updated_df = self._reassign_topic_subcategories(
                df_combined,
                subcategories_to_update,
            )
            # Update the target attribute with the reassigned DataFrame
            setattr(self, target_attr, updated_df)
            # Update the df_topic_categorized with the reassigned topics
            self.df_topic_categorized = updated_df

    # ------------------------- LLM-Related Methods -------------------------

    def _generate_topics_keywords(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate topics and keywords for each video using the LLM."""
        if df.empty:
            self.logger.info("No data to generate topics for.")
            return pd.DataFrame()

        responses = []
        total_duration = 0.0
        for _, row in df.iterrows():
            start_time = datetime.now(MALAYSIA_TZ)
            video_id = row["video_id"]
            record_id = row["id"]

            video_summary = row.get("video_summary", "No description provided")
            video_category = row.get("category", "No category provided")
            video_sub_category = row.get("sub_category", "No sub_category provided")

            llm_prompt = self.llm_handler.get_prompt_topic_keywords(
                video_summary=video_summary,
            )
            response = self.llm_handler.call_llm_with_retry(
                llm_prompt,
                video_id=video_id,
            )

            if response:
                response = response.replace("'", '"')
                responses.append(
                    {
                        "preprocessed_unbiased_id": record_id,
                        "video_id": video_id,
                        "category": video_category,
                        "sub_category": video_sub_category,
                        "topic": response,
                    },
                )
            total_duration += (datetime.now(MALAYSIA_TZ) - start_time).total_seconds()

        self.logger.info(
            "Total duration for topic keyword generation: '%s' seconds.",
            total_duration,
        )
        return self._process_raw_responses(responses)

    def _generate_topic_categories_per_subcategory_and_assign(
        self,
        df_topic_keywords: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate categories per subcategory and assign topics to them.

        This function takes a DataFrame of topics and generates categories per subcategory
        using the LLM. It then assigns the topics to the generated categories and returns
        the DataFrame with the assigned categories.

        Args:
            df_topic_keywords (pd.DataFrame): A DataFrame of topics.

        Returns:
            pd.DataFrame: A DataFrame with the assigned categories.

        """
        if df_topic_keywords.empty:
            self.logger.info("No topics to categorize.")
            return pd.DataFrame()

        # Enrich DataFrame with category and subcategory names
        df_topic_keywords = self.db_handler.insert_category_subcategory_names_into_df(
            df_topic_keywords,
        )

        # Remove the 'id' column as it is no longer needed
        df_topic_keywords = df_topic_keywords.drop("id", axis=1)

        # Get unique subcategories grouped by category
        unique_subcategories = df_topic_keywords.groupby("category")[
            "sub_category"
        ].unique()
        all_assigned = []

        # Iterate over each category and subcategory
        for category, subcategories in unique_subcategories.items():
            # Filter the DataFrame for the current category and subcategory
            df_category = df_topic_keywords[df_topic_keywords["category"] == category]
            for subcat in subcategories:
                df_sub = df_category[df_category["sub_category"] == subcat]
                if df_sub.empty:
                    continue

                # Generate and assign categories for the current subcategory
                assigned_df = self._generate_and_assign_categories(
                    df_sub,
                    category,
                    subcat,
                    num_categories=2,
                )
                all_assigned.append(assigned_df)

        if not all_assigned:
            return pd.DataFrame()

        # Concatenate all assigned categories
        df_topic_categorized = pd.concat(all_assigned, ignore_index=True)

        # Drop columns that are no longer needed
        df_topic_keywords = df_topic_keywords.drop(
            [
                "video_id",
                "topic_summary",
                "relates_to",
                "purpose",
                "execution_method",
                "target_person",
            ],
            axis=1,
        )

        # Create a lookup dictionary from df_topic_keywords
        lookup = df_topic_keywords.set_index(
            ["preprocessed_unbiased_id", "category", "sub_category"],
        ).to_dict(orient="index")

        # Define a function to update each row in df_topic_categorized
        def add_columns(row: pd.Series) -> pd.Series:
            """Add columns to a row of df_topic_categorized based on a lookup dictionary.

            Args:
                row (pd.Series): A row of df_topic_categorized.

            Returns:
                pd.Series: The updated row with added columns.

            """
            key = (
                row["preprocessed_unbiased_id"],
                row["category"],
                row["sub_category"],
            )
            if key in lookup:
                for col, value in lookup[key].items():
                    if col not in row or pd.isna(row[col]):
                        row[col] = value
            return row

        # Apply the update function row-wise
        return df_topic_categorized.apply(add_columns, axis=1)

    def _generate_and_assign_categories(
        self,
        df_sub: pd.DataFrame,
        category: str,
        sub_category: str,
        num_categories: int,
    ) -> pd.DataFrame:
        """Generate and assign topic categories for a given subcategory.

        This function takes a DataFrame of topics and generates categories for the given
        subcategory using the LLM. It then assigns the topics to the generated categories
        and returns the DataFrame with the assigned categories.

        Args:
            df_sub (pd.DataFrame): A DataFrame of topics for the given subcategory.
            category (str): The category of the subcategory.
            sub_category (str): The subcategory.
            num_categories (int): The number of categories to generate.

        Returns:
            pd.DataFrame: A DataFrame with the assigned categories.

        """
        topics = df_sub["topic_summary"].tolist()
        cat_list = self._get_categories_from_llm(
            topics,
            category,
            sub_category,
            num_categories,
        )
        cat_list = cat_list[:MAX_CATEGORIES]
        return self._assign_topic_categories_per_subcategory(df_sub, cat_list)

    def _assign_topic_categories_per_subcategory(
        self,
        df_sub: pd.DataFrame,
        topic_categories_list: list[str],
    ) -> pd.DataFrame:
        """Assign topic categories for each topic in a subcategory.

        This function takes a DataFrame of topics for a subcategory and assigns
        each topic to a category using the LLM.

        Args:
            df_sub (pd.DataFrame): A DataFrame of topics for the subcategory.
            topic_categories_list (list[str]): The list of categories to assign topics to.

        Returns:
            pd.DataFrame: A DataFrame with the assigned categories.

        """

        def process_row(row: pd.Series) -> dict:
            """Process a single row in the DataFrame."""
            # Get the topic summary and categories from the row
            topic_summary = row["topic_summary"]
            categories = topic_categories_list

            # Get the LLM prompt for topic assignment
            llm_prompt = self.llm_handler.get_prompt_topic_assignment(
                topic=topic_summary,
                categories=categories,
            )

            # Call the LLM with the prompt
            response = self.llm_handler.call_llm_with_retry(llm_prompt)

            # Extract the category from the LLM response
            raw_category = response.split(":", 1)[-1].strip() if response else "Others"

            # Map the category to the category ID using the topic category mapping
            topic_category_mapping = self.db_handler.get_topic_category_mapping()
            topic_category = raw_category if raw_category in categories else "Others"
            topic_category_id = topic_category_mapping.get(topic_category, None)

            # Return the processed row
            return {
                "preprocessed_unbiased_id": row["preprocessed_unbiased_id"],
                "video_id": row["video_id"],
                "topic_category": topic_category,
                "topic_category_id": topic_category_id,
                "category": row["category"],
                "sub_category": row["sub_category"],
                "topic_summary": row["topic_summary"],
                "relates_to": row["relates_to"],
                "purpose": row["purpose"],
                "execution_method": row["execution_method"],
                "target_person": row["target_person"],
            }

        # Apply the process_row function to each row in the DataFrame
        return pd.DataFrame(df_sub.apply(process_row, axis=1).tolist())

    def _get_categories_from_llm(
        self,
        topics: list[str],
        category: str,
        sub_category: str,
        num_categories: int,
    ) -> list[str]:
        """Get categories from LLM for the given topics.

        This function generates a prompt to request category suggestions from the LLM
        for a list of topics. It postprocesses the LLM's output and prioritizes the new
        categories against existing ones in the database.

        Args:
            topics (list[str]): A list of topic summaries.
            category (str): The main category for context.
            sub_category (str): The sub-category for context.
            num_categories (int): Number of categories to generate.

        Returns:
            list[str]: A list of prioritized category names.

        """
        # Generate the LLM prompt for topic category generation
        llm_prompt = self.llm_handler.get_prompt_topic_categories(
            topics=topics,
            categories=[category],
            subcategories=[sub_category],
            number_of_categories=num_categories,
        )

        # Call the LLM and retrieve the output
        categories_output = self.llm_handler.call_llm_with_retry(llm_prompt)

        # Postprocess the LLM output to filter and clean the categories
        new_categories = self.llm_handler.postprocess_llm_output(
            prompt=llm_prompt,
            output=categories_output,
            category=[category],
            sub_category=[sub_category],
        )

        # Retrieve existing categories from the database
        existing_categories_map = self.db_handler.retrieve_existing_categories()
        existing_categories = existing_categories_map.get(sub_category, [])

        # Prioritize and return the new categories against existing ones
        return self._prioritize_new_categories(
            existing_categories,
            new_categories,
            MAX_CATEGORIES,
        )

    # ------------------------- Category Assignment & Reassignment -------------------------

    def _assign_existing_topic_categories(
        self,
        df_topic_keywords: pd.DataFrame,
        existing_categories_map: dict[str, list[str]],
    ) -> pd.DataFrame:
        """Assign existing categories to new topics if possible.

        This function takes a DataFrame of categorized topics and assigns
        existing categories to new topics if possible. If the topic does not
        have a category, it will be assigned to "Others".

        Args:
            df_topic_keywords (pd.DataFrame): A DataFrame of categorized topics.
            existing_categories_map (dict[str, list[str]]): A dictionary mapping
                subcategory to a list of existing categories.

        Returns:
            pd.DataFrame: A DataFrame with assigned categories.

        """
        if df_topic_keywords.empty:
            return pd.DataFrame()

        def process_group(df_sub: pd.DataFrame) -> pd.DataFrame:
            """Process a subcategory group and assign existing categories.

            Args:
                df_sub (pd.DataFrame): A subcategory group of topics.

            Returns:
                pd.DataFrame: A DataFrame with assigned categories.

            """
            subcat = df_sub["sub_category"].iloc[0]
            # Get the existing categories for the subcategory
            cat_list = existing_categories_map.get(subcat, ["Others"])[:MAX_CATEGORIES]
            # Assign the categories to the topics
            return self._assign_topic_categories_per_subcategory(df_sub, cat_list)

        # Group the DataFrame by subcategory and apply the process_group function
        return df_topic_keywords.groupby("sub_category").apply(process_group)

    def _analyze_others_percentage(self, df_to_analyze: pd.DataFrame) -> pd.DataFrame:
        """Analyze percentage of 'Others' category.

        This function takes a DataFrame of categorized topics and analyzes
        the percentage of topics assigned to 'Others' category. It returns
        a DataFrame with the results of the analysis.

        Args:
            df_to_analyze (pd.DataFrame): A DataFrame of categorized topics.

        Returns:
            pd.DataFrame: A DataFrame with the results of the analysis.

        """
        if df_to_analyze.empty:
            self.logger.info("No categorized data available in memory.")
            return pd.DataFrame(
                columns=[
                    "category",
                    "sub_category",
                    "topic_category_id",
                    "count",
                    "total_category_subcategory_count",
                    "percentage",
                ],
            )

        df_to_analyze = df_to_analyze.reset_index(drop=True)
        if "sub_category" not in df_to_analyze.columns:
            err_msg = "No 'sub_category' column available."
            raise ValueError(err_msg)

        # Group the DataFrame by category and subcategory and count the number of topics
        grouped = (
            df_to_analyze.groupby(["category", "sub_category", "topic_category_id"])
            .size()
            .reset_index(name="count")
        )

        # Calculate the total count of topics for each category and subcategory
        grouped["total_category_sub_category_count"] = grouped.groupby(
            ["category", "sub_category"],
        )["count"].transform("sum")

        # Calculate the percentage of topics assigned to 'Others' category
        grouped["percentage"] = (
            grouped["count"] / grouped["total_category_sub_category_count"] * 100
        )

        # Get the topic category mapping
        topic_category_mapping = self.db_handler.get_topic_category_mapping()

        # Filter the results to only include the 'Others' category
        others_id = topic_category_mapping.get("Others")

        return grouped[grouped["topic_category_id"] == others_id]

    def _reassign_topic_subcategories(
        self,
        df_topic_categorized: pd.DataFrame,
        subcategories_to_update: list[str],
    ) -> pd.DataFrame:
        """Reassign subcategories exceeding 'Others' threshold.

        This function takes a DataFrame of categorized topics and a list of
        subcategories that need reassignment. It reassigns the topics to reduce
        the 'Others' category and makes sure that the 'Others' category is
        within the threshold.

        Args:
            df_topic_categorized (pd.DataFrame): A DataFrame of categorized topics.
            subcategories_to_update (list[str]): A list of subcategories that need reassignment.

        Returns:
            pd.DataFrame: The reassigned DataFrame of categorized topics.

        """
        df_filtered = df_topic_categorized[
            df_topic_categorized["sub_category"].isin(subcategories_to_update)
        ]

        if df_filtered.empty:
            self.logger.info("No topics found for reassignment.")
            return df_topic_categorized
        # Start with default number of categories and increment if needed
        num_categories = DEFAULT_NUM_CATEGORIES

        while True:
            df_topic_categorized = self._reassign_for_given_categories(
                df_topic_categorized,
                df_filtered,
                num_categories,
            )
            # Analyze the percentage of 'Others' for the reassigned topics
            others_analysis = self._analyze_others_percentage(df_topic_categorized)
            # Filter the results to only include the subcategories that need reassignment
            others_filtered = others_analysis[
                others_analysis["sub_category"].isin(subcategories_to_update)
            ]

            if others_filtered.empty:
                self.logger.info("No 'Others' category found after reassignment.")
                break

            # Get the subcategories with 'Others' exceeding the threshold
            high_others = others_filtered.loc[
                others_filtered["percentage"] > THRESHOLD,
                "sub_category",
            ].unique()
            if len(high_others) == 0:
                self.logger.info(
                    "All subcategories have 'Others' < %s. Stopping.",
                    THRESHOLD,
                )
                break

            if num_categories < MAX_CATEGORIES:
                num_categories += 1
                self.logger.info(
                    "Increasing categories to '%s' since 'Others' still > %s for '%s'.",
                    num_categories,
                    THRESHOLD,
                    high_others,
                )
            else:
                self.logger.info(
                    "Maximum categories (%s) reached. One final reassignment attempt.",
                    MAX_CATEGORIES,
                )
                df_topic_categorized = self._reassign_for_given_categories(
                    df_topic_categorized,
                    df_filtered,
                    num_categories,
                )
                # Analyze the final 'Others' category
                final_others = self._analyze_others_percentage(df_topic_categorized)
                # Filter the results to only include the subcategories that need reassignment
                final_high_others = final_others[
                    final_others["sub_category"].isin(subcategories_to_update)
                ]
                self.logger.info(
                    "Final 'Others' after max categories:\n%s",
                    final_high_others,
                )
                break

        return df_topic_categorized

    def _reassign_for_given_categories(
        self,
        df_topic_categorized: pd.DataFrame,
        df_filtered: pd.DataFrame,
        num_categories: int,
    ) -> pd.DataFrame:
        """Reassign topics for given subcategories and a specified number of categories.

        :param df_topic_categorized: DataFrame of topics with existing categorization.
        :param df_filtered: DataFrame of topics to be reassigned.
        :param num_categories: Number of categories to generate for the subcategory.
        :return: DataFrame of topics with updated categorization.
        """
        # For each subcategory that needs reassignment, generate new topic assignments
        all_assigned = []
        for _, df_sub in df_filtered.groupby("sub_category"):
            category = df_sub["category"].iloc[0]
            sub_category = df_sub["sub_category"].iloc[0]
            assigned_df = self._generate_and_assign_categories(
                df_sub,
                category,
                sub_category,
                num_categories,
            )
            all_assigned.append(assigned_df)

        # Concatenate all newly assigned topics
        df_new_assignments = (
            pd.concat(all_assigned, ignore_index=True)
            if all_assigned
            else pd.DataFrame()
        )
        # If no new assignments, return the original DataFrame
        if df_new_assignments.empty:
            return df_topic_categorized

            # Create a composite unique identifier
        df_new_assignments["composite_id"] = (
            df_new_assignments["preprocessed_unbiased_id"].astype(str)
            + "_"
            + df_new_assignments["category"].astype(str)
            + "_"
            + df_new_assignments["sub_category"].astype(str)
        )

        df_topic_categorized["composite_id"] = (
            df_topic_categorized["preprocessed_unbiased_id"].astype(str)
            + "_"
            + df_topic_categorized["category"].astype(str)
            + "_"
            + df_topic_categorized["sub_category"].astype(str)
        )

        # Ensure unique index by aggregating or deduplicating
        df_new_assignments = df_new_assignments.groupby("composite_id").first()

        # Convert to dictionary for row-wise updates
        updates = df_new_assignments.to_dict(orient="index")

        # Iterate through rows in df_topic_categorized and apply updates
        def update_row(row: pd.Series) -> pd.Series:
            """Update a row with values from the updates dictionary if key exists.

            Args:
                row (pd.Series): Row to be updated.

            Returns:
                pd.Series: Updated row.

            """
            key = row["composite_id"]
            if key in updates:
                for col, value in updates[key].items():
                    if pd.notna(value):  # Update only if value is not NaN
                        row[col] = value
            return row

        # Apply updates row-wise
        df_topic_categorized = df_topic_categorized.apply(update_row, axis=1)

        # Drop the composite ID column if not needed for further processing

        return df_topic_categorized.drop(
            columns=["composite_id"],
            errors="ignore",
        )

    # ------------------------- Utility Methods -------------------------

    def _process_raw_responses(self, responses: list[dict]) -> pd.DataFrame:
        """Process raw LLM responses into a DataFrame.

        This method takes in a list of dictionaries, where each dictionary represents a video's topic
        and keywords. It processes the responses, extracts the useful information, and returns a DataFrame
        containing the topic and keywords for each video.
        """
        processed = []

        for item in responses:
            result = None
            try:
                # Attempt to parse the raw response as a dictionary
                dictionary = ast.literal_eval(item["topic"])
                # Add the preprocessed unbiased ID, video ID, category, and subcategory to the dictionary
                dictionary.update(
                    {
                        "preprocessed_unbiased_id": item["preprocessed_unbiased_id"],
                        "video_id": item["video_id"],
                        "category": item["category"],
                        "sub_category": item["sub_category"],
                    },
                )
                result = dictionary
            except (ValueError, SyntaxError):
                # Log specific exceptions for better error tracking
                self.logger.exception(
                    "Error processing response for video_id %s:",
                    item.get("video_id", "Unknown"),
                )
            except KeyError:
                self.logger.exception(
                    "Missing key in response item for video_id %s",
                    item.get("video_id", "Unknown"),
                )

            if result:
                processed.append(result)

        # Create a DataFrame only if processing is successful
        if processed:
            self.logger.info("Topics and keywords generated successfully.")
            return pd.DataFrame(processed)

        self.logger.warning("No topics or keywords were generated.")
        return pd.DataFrame(
            columns=[
                "preprocessed_unbiased_id",
                "video_id",
                "category",
                "sub_category",
            ],
        )

    def _prioritize_new_categories(
        self,
        existing_categories: list,
        new_categories: list,
        max_categories: int,
    ) -> list:
        """Prioritize new categories over existing and always include 'Others'.

        Args:
            existing_categories (list): A list of existing category names.
            new_categories (list): A list of new category names to prioritize.
            max_categories (int): The maximum number of categories to return.

        Returns:
            list: A sorted list of categories with new categories prioritized,
            always including 'Others' last.

        """
        # Combine existing and new categories, ensuring all are unique
        combined = list(set(existing_categories + new_categories))

        # Ensure "Others" is included in the combined list
        if "Others" not in combined:
            combined.append("Others")

        def sort_key(cat: str) -> tuple[int, str]:
            """Determine the sort key for categories.

            The sort key is a tuple consisting of:
            - An integer indicating priority:
              - 0 for "Others"
              - 1 for new categories
              - 2 for existing categories
            - The category name in lowercase for alphabetical sorting.

            Args:
                cat (str): The category name.

            Returns:
                tuple[int, str]: The sorting key for the category.

            """
            # Assign priority based on category type
            if cat == "Others":
                return (0, cat.lower())
            return (1 if cat in new_categories else 2, cat.lower())

        # Sort categories using the defined sort key and limit to max_categories
        return sorted(combined, key=sort_key)[:max_categories]

    def _map_category_sub_category_id_names(self) -> None:
        """Map category_id and sub_category_id to their respective names.

        This function updates the DataFrame by mapping the category IDs and
        subcategory IDs to their corresponding names using the provided mappings.
        It assumes that the DataFrame has columns 'category_id' and 'sub_category_id'.

        The resulting DataFrame will have additional columns 'category' and 'sub_category'
        populated with the names corresponding to the IDs.

        Preconditions:
            - The DataFrame 'self.df' must not be empty.
            - The columns 'category_id' and 'sub_category_id' must exist in the DataFrame.

        Effects:
            - Modifies 'self.df' in place by adding 'category' and 'sub_category' columns.
        """
        if (
            not self.df.empty
            and "category_id" in self.df.columns
            and "sub_category_id" in self.df.columns
        ):
            # Map category_id to category names
            self.df["category"] = self.df["category_id"].map(self.category_id_to_name)
            # Map sub_category_id to subcategory names
            self.df["sub_category"] = self.df["sub_category_id"].map(
                self.sub_category_id_to_name,
            )

    def _map_category_sub_category_names(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame | None:
        """Map category and sub_category to their ids.

        This function takes a DataFrame as input and maps the category and subcategory
        names to their corresponding IDs using the provided mappings. It assumes that
        the DataFrame has columns 'category' and 'sub_category'.

        Args:
            df (pd.DataFrame): The DataFrame to be processed.

        Returns:
            pd.DataFrame | None: The processed DataFrame with category_id and sub_category_id columns added.

        """
        if not df.empty and "category" in df.columns and "sub_category" in df.columns:
            # Map category to category_id
            cat_map = self.db_handler.get_category_mapping()
            df["category_id"] = df["category"].map(cat_map)

            # Map sub_category to sub_category_id
            subcat_map = self.db_handler.get_subcategory_mapping()
            df["sub_category_id"] = df["sub_category"].map(subcat_map)

        return df

    def _insert_data_into_db(self, df: pd.DataFrame) -> int | None:
        """Insert final categorized data into the database.

        This function takes the processed DataFrame as input and inserts the data
        into the database. It maps the category and subcategory names to IDs using
        the provided mappings and then inserts the data into the database.

        Args:
            df (pd.DataFrame): The processed DataFrame to be inserted.

        Returns:
            int | None: The number of unique video IDs inserted or None if no data is inserted.

        """
        if df.empty:
            self.logger.info("No data to insert.")
            return None

        self.logger.info("Mapping categories/subcategories to IDs and inserting data.")

        # Map category names to IDs
        df["category_id"] = (
            df["category"]
            .map({v: k for k, v in self.category_id_to_name.items()})
            .fillna(0)
            .astype(int)
        )

        # Map subcategory names to IDs
        df["sub_category_id"] = (
            df["sub_category"]
            .map({v: k for k, v in self.sub_category_id_to_name.items()})
            .fillna(0)
            .astype(int)
        )

        if not self.df_existing.empty:
            # Reinsert data if existing data is found
            self.db_handler.reinsert_all_data(df)
        else:
            # Insert data if no existing data is found
            self.db_handler.insert_data(df)

        self.logger.info("Data inserted successfully.")
        return len(df["video_id"].unique())


if __name__ == "__main__":
    orchestrator = TopicKeywordGenerator()
    input_payload = {"video_summary": "The video shows chickens", "video_id": 1}
    orchestrator.process_on_the_fly(input_payload)
