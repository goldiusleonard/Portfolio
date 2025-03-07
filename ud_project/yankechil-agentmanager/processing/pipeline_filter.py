import concurrent.futures  # For parallel processing
import json
from datetime import datetime

import pandas as pd
from sqlalchemy import func, inspect

from config.config_num import Num
from config.config_risk_samples import risk_levels_general, risk_levels_sample

# from urllib.parse import quote_plus
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import create_engine
from log_mongo import logger
from schema.input_schemas import (
    CategoryTableSchema,
    SubCategoryTableSchema,
)
from schema.output_schemas import (
    AnalysisTableSchema,
    # SsOutputTableSchema,
    # TikTokTableSchemaOut,
    CommentsTableSchemaOut,
    MappedTableSchemaOut,
)


# Define a function to handle missing values
def handle_missing_value(value, default="None"):
    """Returns the value if it exists, otherwise returns the default value."""
    return value if value else default


def validate_columns(
    df_unbiased,
    df_comments,
    post_date_unbiased_column_name,
    post_date_comments_column_name,
    agent_builder_name,
):
    # """Validate the necessary columns in the data."""
    # if post_date_unbiased_column_name not in df_unbiased.columns or agent_builder_name not in df_unbiased.columns:
    #     raise ValueError(f"Dataframe must contain {post_date_unbiased_column_name} and {agent_builder_name} columns.")

    # if post_date_comments_column_name not in df_comments.columns or agent_builder_name not in df_comments.columns:
    #     raise ValueError(f"Dataframe must contain {post_date_comments_column_name} and {agent_builder_name} columns.")
    """Validate the necessary columns in the data."""
    if post_date_unbiased_column_name not in df_unbiased.columns:
        raise ValueError(f"Dataframe must contain {post_date_unbiased_column_name}.")

    if post_date_comments_column_name not in df_comments.columns:
        raise ValueError(f"Dataframe must contain {post_date_comments_column_name}.")


def filter_by_date(df, config, post_date_column_name):
    """Filter data based on start_date and end_date provided in the config.

    Args:
        df (pd.DataFrame): The DataFrame to filter.
        config (object): The configuration object containing start_date and end_date.
        post_date_column_name (str): The name of the date column to filter.

    Returns:
        pd.DataFrame: The filtered DataFrame.

    """
    # Ensure the DataFrame has a valid index
    df = df.reset_index(drop=True)

    # Ensure the date column is in datetime format
    if df[post_date_column_name].dtype != "datetime64[ns]":
        df[post_date_column_name] = pd.to_datetime(
            df[post_date_column_name],
            errors="coerce",
        )

    # Extract start_date and end_date from config
    start_date = pd.to_datetime(config.start_date) if config.start_date else None
    end_date = pd.to_datetime(config.end_date) if config.end_date else None

    # Adjust end_date to include the full day if provided
    if end_date:
        end_date = end_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    # Filter by start_date
    if start_date:
        df = df[df[post_date_column_name] >= start_date]
        logger.info(f"Filtered rows after start_date ({start_date}): {len(df)}")
    else:
        logger.info("No start_date provided.")

    # Filter by end_date
    if end_date:
        df = df[df[post_date_column_name] <= end_date]
        logger.info(f"Filtered rows after end_date ({end_date}): {len(df)}")
    else:
        logger.info("No end_date provided.")

    # Return the filtered DataFrame
    return df


# Function to get category and subcategory ID available
def get_available_category_and_subcategory_id(
    config,
    category_table,
    sub_category_table,
):
    try:
        # Create mappings for category and subcategory
        category_mapping = {
            row["category_name"]: row["id"] for _, row in category_table.iterrows()
        }
        subcategory_mapping = {
            (row["sub_category_name"], row["category_id"]): row["id"]
            for _, row in sub_category_table.iterrows()
        }

        # Initialize sets to store unique IDs
        category_ids = set()
        subcategory_ids = set()

        category_id = category_mapping.get(config.category)
        if category_id:
            category_ids.add(category_id)
        subcategory_id = subcategory_mapping.get((config.subcategory, category_id))
        if subcategory_id:
            subcategory_ids.add(subcategory_id)

        # Convert sets to sorted lists
        category_ids = sorted(list(category_ids))
        subcategory_ids = sorted(list(subcategory_ids))

        # Logging
        logger.info(f"Available Category IDs: {category_ids}")
        logger.info(f"Available Subcategory IDs: {subcategory_ids}")

        return category_ids, subcategory_ids

    except Exception as e:
        logger.error(f"Error in get_available_category_and_subcategory_ids: {e!s}")
        raise


def apply_filters(df_unbiased, df_mapped, df_sub_category, df_category, config):
    """Apply category and subcategory filters to the data.

    Args:
        df_unbiased (pd.DataFrame): The unbiased DataFrame.
        df_mapped (pd.DataFrame): The mapped DataFrame with category and subcategory info.
        df_sub_category (pd.DataFrame): The subcategory DataFrame.
        df_category (pd.DataFrame): The category DataFrame.
        risk_levels (Dict): The risk levels sample.

    Returns:
        tuple: A tuple containing filtered_unbiased and filtered_mapped DataFrames.

    """
    logger.info("Starting to apply filters...")

    # Retrieve available category and subcategory IDs
    logger.info("Fetching available category and subcategory IDs...")

    category_filter, subcategory_filter = get_available_category_and_subcategory_id(
        config,
        df_category,
        df_sub_category,
    )
    logger.info("Category filter: %s", category_filter)
    logger.info("Subcategory filter: %s", subcategory_filter)

    # Apply filters to the mapped DataFrame to fit with unbiased filtered by date
    df_mapped = df_mapped[df_mapped["video_id"].isin(df_unbiased["video_id"])]

    # Apply filters to the mapped DataFrame
    logger.info("Applying filters to df_mapped...")
    filtered_mapped = df_mapped[
        (df_mapped["category_id"].isin(category_filter))
        & (df_mapped["sub_category_id"].isin(subcategory_filter))
    ]
    logger.info("Filtered mapped DataFrame contains %d rows.", len(filtered_mapped))

    # print(filtered_mapped)

    # Apply filters to the unbiased DataFrame
    logger.info("Applying filters to df_unbiased based on filtered_mapped video IDs...")
    filtered_unbiased = df_unbiased[
        df_unbiased["video_id"].isin(filtered_mapped["video_id"])
    ]
    logger.info("Filtered unbiased DataFrame contains %d rows.", len(filtered_unbiased))

    logger.info("Finished applying filters.")
    return filtered_unbiased, filtered_mapped


def get_risk_levels(category, subcategory, risk_levels_dict):
    """Extract the list of risk levels for a given category and subcategory.

    Args:
        category (str): The category name (e.g., "Scam").
        subcategory (str): The subcategory name (e.g., "Gold").
        risk_levels_dict (dict): The nested dictionary containing risk levels.

    Returns:
        dict: A dictionary containing the risk levels and their associated lists.
        None: If the category or subcategory is not found.

    """
    # Check if category exists in the dictionary
    if category in risk_levels_dict:
        # Check if subcategory exists in the category
        if subcategory in risk_levels_dict[category]:
            logger.info(
                f"Successfully retrieved risk levels for '{subcategory}' in category '{category}'.",
            )
            return risk_levels_dict[category][subcategory]
        # Log the missing subcategory
        logger.warning(
            f"Subcategory '{subcategory}' not found in category '{category}'.",
        )
        return None
    # Log the missing category
    logger.warning(f"Category '{category}' not found.")
    return None


# Function to recursively remove quotes from string values
def remove_quotes(value):
    if isinstance(value, str):
        # Remove all double quotes from the string
        return value.replace('"', "")
    if isinstance(value, list):
        # If it's a list, process each item
        return [remove_quotes(item) for item in value]
    if isinstance(value, dict):
        # If it's a dictionary, apply the function to each key-value pair
        return {key: remove_quotes(val) for key, val in value.items()}
    # Return the value as is if it's neither a string, list, nor dictionary
    return value


def insert_data_in_batches(session, table, data, batch_size=5):
    """Insert data into a table in batches. Converts ORM objects to dictionaries if necessary."""
    if not isinstance(data, list):
        raise ValueError("Input data must be a list")

    # Convert ORM objects (like MappedTableSchemaOut) into dictionaries
    if data and not isinstance(data[0], dict):
        data = [
            {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}
            for obj in data
        ]

    # Process and insert the data in batches
    for i in range(0, len(data), batch_size):
        batch = data[i : i + batch_size]
        try:
            session.bulk_insert_mappings(table, batch)  # Perform bulk insert
            session.commit()  # Commit the batch
            logger.info(
                f"Inserted batch {i // batch_size + 1} ({len(batch)} records) into {table.__tablename__}",
            )
        except Exception as e:
            logger.error(
                f"Error inserting batch {i // batch_size + 1} into {table.__tablename__}: {e}",
            )
            session.rollback()  # Rollback in case of error


def get_justification_with_timeout(
    self,
    input_text,
    timeout=10,
):  # Adjust the timeout as needed
    try:
        # Run the function with a timeout
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                self.agentsprocess.get_justification_risk_output,
                input_text,
            )
            # Wait for the result with a timeout
            data = future.result(timeout=timeout)
            return data
    except concurrent.futures.TimeoutError:
        # If timeout occurs, log the event and return None
        logger.warning(
            f"get_justification_risk_output took too long and was timed out for input: {input_text}",
        )
        return None
    except Exception as e:
        # Handle other potential errors (e.g., network issues, etc.)
        logger.error(f"Error while processing input: {input_text}. Error: {e!s}")
        return None


class DataProcessorPipeline_v01:
    def __init__(self, agentsprocess, db, df, config=None):
        self.agentsprocess = agentsprocess
        self.db = db
        self.df = df.copy()
        self.config = config

    def process_sentiment(self, input_text):
        data = self.agentsprocess.get_sentiment_output(input_text)
        transformer_sentiment = handle_missing_value(
            data["transformer"][Num.SENTIMENT],
            default="None",
        )
        # transformer_sentiment = data["transformer"][Num.SENTIMENT]
        transformer_sentiment_score = handle_missing_value(
            data["transformer"][Num.SENTIMENT_SCORE],
            default=0.0,
        )
        # transformer_sentiment_score = data["transformer"][Num.SENTIMENT_SCORE]
        api_sentiment = handle_missing_value(
            data["api"][Num.SENTIMENT],
            default="None",
        )
        # api_sentiment = data["api"][Num.SENTIMENT]
        api_sentiment_score = handle_missing_value(
            data["api"][Num.SENTIMENT_SCORE],
            default=0.0,
        )

        return (
            transformer_sentiment,
            transformer_sentiment_score,
            api_sentiment,
            api_sentiment_score,
        )

    def process_justification(self, input_text):
        data = self.agentsprocess.get_justification_risk_output(
            input_text,
        )
        eng_justification = handle_missing_value(
            data[Num.ENGLISH_JUSTIFICATION],
            default="None",
        )
        malay_justification = handle_missing_value(
            data[Num.MALAY_JUSTIFICATION],
            default="None",
        )
        risk_status = handle_missing_value(data[Num.RISK_STATUS], default="None")

        irrelevant_score = handle_missing_value(
            data[Num.IRRELEVANT_SCORE],
            default="None",
        )

        return eng_justification, malay_justification, risk_status, irrelevant_score

    def process_law(self, input_text, files):
        # Do not put new line (\n) for this input

        input_text = remove_quotes(input_text)

        law = self.agentsprocess.get_law_regulated_output_v1(files, input_text)
        return law

    def process_comment_risk(self, input_text):
        data = self.agentsprocess.get_comment_risk_output(
            input_text,
        )
        eng_justification = handle_missing_value(
            data[Num.ENGLISH_JUSTIFICATION],
            default="None",
        )
        malay_justification = handle_missing_value(
            data[Num.MALAY_JUSTIFICATION],
            default="None",
        )
        risk_status = handle_missing_value(data[Num.RISK_STATUS], default="None")

        irrelevant_score = handle_missing_value(
            data[Num.IRRELEVANT_SCORE],
            default="None",
        )

        return eng_justification, malay_justification, risk_status, irrelevant_score

    def run_agents(self, index):
        category_ids = self.df.loc[index, "category"]
        category_ids = list(map(int, category_ids.split(",")))
        sub_category_ids = self.df.loc[index, "subcategory"]
        sub_category_ids = list(map(int, sub_category_ids.split(",")))

        mapped_pairs, results = self.get_mapped_category_subcategory_tuples(
            category_ids,
            sub_category_ids,
        )

        for category, sub_category in results:
            category_name = category.category_name
            sub_category_name = sub_category.sub_category_name
            # Fetch or create category_id and sub_category_id
            category_id = self.get_category_id(category_name)
            sub_category_id = self.get_sub_category_id(sub_category_name, category_id)

            for col in ["category_id", "sub_category_id"]:
                if col not in self.df.columns:
                    self.df[col] = None

            self.df.loc[index, "category_id"] = category_id
            self.df.loc[index, "sub_category_id"] = sub_category_id

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            start_time = datetime.now()

            # Now process sentiment, justification, and law
            self.process_sentiment(index)
            risk_level = str(
                get_risk_levels(
                    category_name,
                    sub_category_name,
                    self.config.risk_levels,
                ),
            )
            self.process_justification(
                index,
                category_name,
                sub_category_name,
                risk_level,
            )
            self.process_law(index, sub_category_name, self.config.files_name)

            self.df.loc[index, Num.TIMESTAMP] = timestamp
            processing_time = (datetime.now() - start_time).total_seconds()
            self.df.loc[index, Num.PROCESS_TIME] = processing_time

    def get_category_and_subcategory_names(self, category_id, subcategory_id):
        try:
            # Fetch category name
            category = (
                self.db.session.query(CategoryTableSchema)
                .filter(CategoryTableSchema.id == category_id)
                .first()
            )
            if not category:
                logger.error(f"Category with ID {category_id} not found.")
                raise ValueError(f"Category with ID {category_id} does not exist.")

            # Fetch subcategory name
            subcategory = (
                self.db.session.query(SubCategoryTableSchema)
                .filter(
                    SubCategoryTableSchema.id == subcategory_id,
                    SubCategoryTableSchema.category_id == category_id,
                )
                .first()
            )
            if not subcategory:
                logger.error(
                    f"Subcategory with ID {subcategory_id} not found under category ID {category_id}.",
                )
                raise ValueError(
                    f"Subcategory with ID {subcategory_id} does not exist under category ID {category_id}.",
                )

            # Return category and subcategory names
            return category.category_name, subcategory.sub_category_name

        except ValueError as ve:
            # Log detailed validation errors
            logger.warning(f"Validation error: {ve}")
            return None, None

        except Exception as e:
            # Catch unexpected errors
            logger.error(f"Unexpected error: {e}")
            return None, None

    def prefetch_category_and_subcategory_names(self, category_ids, subcategory_ids):
        # Prefetch categories and subcategories in bulk
        categories = (
            self.db.session.query(CategoryTableSchema)
            .filter(CategoryTableSchema.id.in_(category_ids))
            .all()
        )
        subcategories = (
            self.db.session.query(SubCategoryTableSchema)
            .filter(SubCategoryTableSchema.id.in_(subcategory_ids))
            .all()
        )
        # Create lookup dictionaries
        category_dict = {cat.id: cat.category_name for cat in categories}
        subcategory_dict = {sub.id: sub.sub_category_name for sub in subcategories}

        return category_dict, subcategory_dict

    def process_unbiased_data_and_store(self, mapped_df, batch_size = 5):
        try:
            # df_copy_1 = self.df.copy()
            # video_sentiment_map = {}  # Map video_id to sentiment IDs
            # ss_output_data_list = []

            session = self.db.get_session()
            # Check if the necessary columns exist in 'mapped_df' and 'self.df'
            if "category_id" not in mapped_df.columns:
                logger.error("The category_id is not a column name in mapped_df.")
                raise ValueError("category_id column is missing in mapped_df.")

            if "sub_category_id" not in mapped_df.columns:
                logger.error("The sub_category_id is not a column name in mapped_df.")
                raise ValueError("sub_category_id column is missing in mapped_df.")

            if "id" not in mapped_df.columns:
                logger.error("The id is not a column name in mapped_df.")
                raise ValueError("id column is missing in mapped_df.")

            if "preprocessed_unbiased_id" not in mapped_df.columns:
                logger.error(
                    "The preprocessed_unbiased_id is not a column name in mapped_df.",
                )
                raise ValueError(
                    "preprocessed_unbiased_id column is missing in mapped_df.",
                )

            if "video_summary" not in self.df.columns:
                logger.error("The video_summary is not a column name in self.df.")
                raise ValueError("video_summary column is missing in self.df.")

            if "video_id" not in self.df.columns:
                logger.error("The video_id is not a column name in self.df.")
                raise ValueError("video_id column is missing in self.df.")

            # Prefetch unique category and subcategory names
            category_ids = mapped_df["category_id"].unique()
            subcategory_ids = mapped_df["sub_category_id"].unique()

            # Step 1: Get analysis_id from TikTokTableSchema
            # Querying and ensuring the correct order in SQLAlchemy
            analysis_ids = self.df["id"].unique()
            # Step 2: Query the output table to find existing IDs (assuming you're using SQLAlchemy)
            existing_ids_query = (
                self.db.session.query(AnalysisTableSchema.id)
                .filter(AnalysisTableSchema.id.in_(analysis_ids))
                .all()
            )

            # Convert the result to a set of existing IDs for faster lookup
            existing_ids = {
                id_[0] for id_ in existing_ids_query
            }  # Unpack tuples to get the id value

            category_dict, subcategory_dict = (
                self.prefetch_category_and_subcategory_names(
                    category_ids,
                    subcategory_ids,
                )
            )

            # print("@@@@@@@@@ analysis_ids @@@@@@@@@@@@")
            # print(analysis_ids)
            # print(len(self.df))
            # print(len(mapped_df))
            # print(category_dict)
            # print(subcategory_dict)
            # print("@@@@@@@@@ analysis_ids @@@@@@@@@@@@")

            sentiment_data_list = []
            mapped_updates_list = []
            cnt = session.query(func.max(AnalysisTableSchema.id)).scalar()
            # Return 0 if no records are found
            cnt = cnt if cnt is not None else 0
            for k, analysis_id in enumerate(analysis_ids):
                # if analysis_id in existing_ids:
                #     logger.error('The data from input already available in ouput table.')
                #     raise
                # Find matching records in the mapped DataFrame
                mapped_records = mapped_df[
                    mapped_df["preprocessed_unbiased_id"] == analysis_id
                ]
                # HIGHLIGHTED: If no matching records are found for the given analysis_id, log a warning and continue
                if mapped_records.empty:
                    logger.warning(
                        f"No matching records found for analysis_id: {analysis_id}",
                    )  # HIGHLIGHTED
                    continue  # HIGHLIGHTED

                # print("@@@@@@@@@ mapped records @@@@@@@@@@@@")
                # print(mapped_records, analysis_id)

                for index, mapped_record in mapped_records.iterrows():
                    category_id = mapped_record["category_id"]
                    sub_category_id = mapped_record["sub_category_id"]
                    video_id = mapped_record["video_id"]
                    analysis_id_ = mapped_record["preprocessed_unbiased_id"]

                    # print("@@@@@@@@@ mapped index @@@@@@@@@@@@")
                    # print(mapped_record)

                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    start_time = datetime.now()

                    # Fetch names using prefetch dictionaries
                    category_name = category_dict.get(category_id)
                    sub_category_name = subcategory_dict.get(sub_category_id)

                    if category_name is None or sub_category_name is None:
                        logger.warning(
                            f"Invalid category/subcategory for row {index}: category_id={category_id}, sub_category_id={sub_category_id}",
                        )
                        # continue

                    # print("@@@@@@@@@ category @@@@@@@@@@@@")
                    # print(category_id)
                    # print(sub_category_id)
                    # print(category_name, sub_category_name)
                    # print(category_id, sub_category_id)
                    # print(k)

                    # HIGHLIGHTED: Ensure category_id and sub_category_id are not missing
                    if pd.isnull(category_id) or pd.isnull(
                        sub_category_id,
                    ):  # HIGHLIGHTED
                        logger.error(
                            f"Missing category or subcategory ID for row {index}: {category_id}, {sub_category_id}",
                        )  # HIGHLIGHTED

                    if (
                        pd.isnull(category_name)
                        or pd.isnull(sub_category_name)
                        or pd.isnull(video_id)
                    ):
                        logger.warning(
                            f"Skipping record due to missing data: category_name={category_name}, "
                            f"sub_category_name={sub_category_name}, video_id={video_id}",
                        )

                    # HIGHLIGHTED: Skip rows with missing or invalid category/subcategory
                    if (
                        category_name is None or sub_category_name is None
                    ):  # HIGHLIGHTED
                        logger.warning(
                            f"Skipping row {index} due to missing category or subcategory: "  # HIGHLIGHTED
                            f"category_id={category_id}, sub_category_id={sub_category_id}",
                        )  # HIGHLIGHTED

                    # Fetch additional data from self.df
                    summary = self.df.loc[
                        self.df["video_id"] == video_id,
                        Num.VIDEO_SUMMARY,
                    ].values
                    description = self.df.loc[
                        self.df["video_id"] == video_id,
                        Num.VIDEO_DESCRIPTION,
                    ].values
                    transcription = self.df.loc[
                        self.df["video_id"] == video_id,
                        Num.TRANSCRIPTION,
                    ].values

                    # HIGHLIGHTED: Skip rows with missing video-related fields
                    if (
                        not summary.size
                        or not description.size
                        or not transcription.size
                    ):  # HIGHLIGHTED
                        logger.warning(
                            f"Skipping row {index} due to missing summary/description/transcription for video_id={video_id}",
                        )  # HIGHLIGHTED

                    # Agents analysis
                    try:
                        print("Calling process_sentiment...")
                        input_text = "\n".join(
                            [
                                str(summary),
                                str(category_name),
                                str(sub_category_name),
                            ],
                        )
                        # sentiment, sentiment_score, api_sentiment, api_sentiment_score = "None", 0.0, "None", 0.0
                        (
                            sentiment,
                            sentiment_score,
                            api_sentiment,
                            api_sentiment_score,
                        ) = self.process_sentiment(input_text)
                        sentiment = sentiment if sentiment is not None else "None"
                        sentiment_score = (
                            sentiment_score if sentiment_score is not None else 0.0
                        )
                        api_sentiment = (
                            api_sentiment if api_sentiment is not None else "None"
                        )
                        api_sentiment_score = (
                            api_sentiment_score
                            if api_sentiment_score is not None
                            else 0.0
                        )
                        logger.info("Completed process_sentiment successfully.")
                    except Exception as e:
                        logger.error(f"Error in process_sentiment: {e!s}")
                        print(f"Error in process_sentiment: {e!s}")
                        sentiment = "APi server error"
                        sentiment_score = 0.0
                        api_sentiment = "APi server error"
                        api_sentiment_score = 0.0

                    if not self.config.risk_levels:
                        risk_level = risk_levels_general
                        logger.info("The risk levels from sample is selected.")
                    else:
                        risk_level = self.config.risk_levels
                        logger.info("The risk level from frontend is selected.")

                    if not risk_level:
                        risk_level = risk_levels_general
                        logger.info("The risk level is risk_levels_general value.")

                    try:
                        print("Calling process_justification...")
                        input_text = "\n".join(
                            [
                                str(summary),
                                str(category_name),
                                str(sub_category_name),
                                str(risk_level),
                            ],
                        )
                        # eng_justification, malay_justification, risk_status, irrelevant_score = "None", "None", "None", "None"
                        (
                            eng_justification,
                            malay_justification,
                            risk_status,
                            irrelevant_score,
                        ) = self.process_justification(input_text)

                        eng_justification = (
                            eng_justification
                            if eng_justification is not None
                            else "None"
                        )
                        malay_justification = (
                            malay_justification
                            if malay_justification is not None
                            else "None"
                        )
                        risk_status = risk_status if risk_status is not None else "None"
                        irrelevant_score = (
                            irrelevant_score if irrelevant_score is not None else "None"
                        )
                        logger.info("Completed process_justification successfully.")
                    except Exception as e:
                        logger.error(f"Error in process_justification: {e!s}")
                        print(f"Error in process_justification: {e!s}")
                        eng_justification = "APi server error"
                        malay_justification = "APi server error"
                        risk_status = "APi server error"
                        irrelevant_score = "APi server error"

                    try:
                        print("Calling process_law_regulated...")
                        input_text = " ".join(
                            [
                                str(sub_category_name),
                                str(summary),
                                str(description),
                                str(transcription),
                                str(risk_status),
                                str(eng_justification),
                            ],
                        )
                        # law = "None"
                        law = self.process_law(input_text, self.config.files_name)
                        law = law if law is not None else "None"
                        logger.info("Completed process_law_regulated successfully.")
                    except Exception as e:
                        logger.error(f"Error in process_law_regulated: {e!s}")
                        print(f"Error in process_law_regulated: {e!s}")
                        law = "APi server error"

                    processing_time = (datetime.now() - start_time).total_seconds()

                    # print("========= justify =============")
                    # print(api_sentiment)
                    # print(sentiment_score)
                    # print(risk_level)
                    # print(eng_justification)
                    # print(risk_status)
                    # print(law)
                    # print(type(eng_justification))
                    # print(type(risk_status))
                    # print("=========  =============")

                    # Step 3: Create a AnalysisTableSchema record
                    sentiment_record = AnalysisTableSchema(
                        category_id=int(category_id) if pd.notnull(category_id) else 1000,
                        sub_category_id=int(sub_category_id) if pd.notnull(sub_category_id) else 1000,
                        video_id=str(video_id) if pd.notnull(video_id) else "Unknown",
                        preprocessed_unbiased_id=int(analysis_id_) if analysis_id_ is not None else 1000,
                        sentiment=str(sentiment) if sentiment else "None",
                        sentiment_score=float(sentiment_score) if sentiment_score is not None else 0.0,
                        api_sentiment=str(api_sentiment) if api_sentiment else "None",
                        api_sentiment_score=float(api_sentiment_score) if api_sentiment_score is not None else 0.0,
                        eng_justification=json.dumps(eng_justification if eng_justification else "None"),
                        malay_justification=json.dumps(malay_justification if malay_justification else "None"),
                        risk_status=str(risk_status) if risk_status else "None",
                        irrelevant_score=str(irrelevant_score) if irrelevant_score else "None",
                        law_regulated=json.dumps(law if law else "None"),
                        timestamp=timestamp,
                        process_time=float(processing_time) if processing_time is not None else 1000.0
                    )


                    sentiment_data_list.append(sentiment_record)
                    cnt += 1

                    mapped_update_record = MappedTableSchemaOut(
                        category_id=category_id,
                        sub_category_id=sub_category_id,
                        video_id=video_id,
                        preprocessed_unbiased_id=analysis_id_,
                        analysis_id=cnt,
                    )

                    mapped_updates_list.append(mapped_update_record)

                    # # Use SQLAlchemy's inspect function to get column names from the table
                    columns = inspect(
                        AnalysisTableSchema,
                    ).c  # Access columns of the schema

                    # HIGHLIGHTED: Ensure both lists are consistent
                    if len(sentiment_data_list) != len(
                        mapped_updates_list,
                    ):  # HIGHLIGHTED
                        logger.error(
                            f"Mismatch between list sizes: sentiment_data_list={len(sentiment_data_list)}, "  # HIGHLIGHTED
                            f"mapped_updates_list={len(mapped_updates_list)}",
                        )  # HIGHLIGHTED

                    # **Insert in Batches (Highlighted Change)**
                    if (
                        len(sentiment_data_list) >= batch_size
                    ):  # Check if batch size is reached
                        logger.info(
                            f"Inserting {len(sentiment_data_list)} sentiment records...",
                        )
                        insert_data_in_batches(
                            session,
                            AnalysisTableSchema,
                            sentiment_data_list,
                            batch_size=batch_size,
                        )
                        sentiment_data_list.clear()  # Clear the list after inserting

                    if (
                        len(mapped_updates_list) >= batch_size
                    ):  # Check if batch size is reached
                        logger.info(
                            f"Inserting {len(mapped_updates_list)} mapped update records...",
                        )
                        insert_data_in_batches(
                            session,
                            MappedTableSchemaOut,
                            mapped_updates_list,
                            batch_size=batch_size,
                        )
                        mapped_updates_list.clear()  # Clear the list after inserting

            # **Final Insert for Remaining Records (Highlighted Change)**
            if sentiment_data_list:  # Insert remaining sentiment records
                logger.info(
                    f"Inserting remaining {len(sentiment_data_list)} sentiment records...",
                )
                insert_data_in_batches(
                    session,
                    AnalysisTableSchema,
                    sentiment_data_list,
                    batch_size=batch_size,
                )
                sentiment_data_list.clear()

            if mapped_updates_list:  # Insert remaining mapped update records
                logger.info(
                    f"Inserting remaining {len(mapped_updates_list)} mapped update records...",
                )
                insert_data_in_batches(
                    session,
                    MappedTableSchemaOut,
                    mapped_updates_list,
                    batch_size=batch_size,
                )
                mapped_updates_list.clear()

            session.commit()
            logger.info("All updates completed successfully.")

        except Exception as e:
            logger.error(f"Error processing data: {e}")
            session.rollback()
        finally:
            session.close()

    def process_comments_data_and_store(self, batch_size=5):
        try:
            session = self.db.get_session()
            # Define a batch size for bulk insert
            df = self.df

            # print("@@@@@@@@@ analysis_ids @@@@@@@@@@@@")
            # print(len(df))

            comment_data_list = []

            for index, mapped_record in df.iterrows():
                category = mapped_record["category"]
                sub_category = mapped_record["subcategory"]
                text = mapped_record["text"]

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                start_time = datetime.now()

                # print("@@@@@@@@@ category @@@@@@@@@@@@")
                # print(category, sub_category)

                if category is None and sub_category is None:
                    logger.info("Found the category or subcategory None value.")
                    continue

                summary = self.df.loc[index, Num.VIDEO_SUMMARY]
                if not summary:
                    logger.error("The summary is not a value.")

                risk_level = str(
                    get_risk_levels(category, sub_category, risk_levels_sample),
                )

                if not risk_level:
                    risk_level = risk_levels_general
                    logger.info("The risk level is risk_levels_general value.")

                try:
                    print("Calling process_Comments...")
                    input_text = "\n".join(
                        [
                            str(summary),
                            str(text),
                            str(category),
                            str(sub_category),
                            str(risk_level),
                        ],
                    )

                    # Attempt to get values from process_comment_risk
                    (
                        eng_justification,
                        malay_justification,
                        risk_status,
                        irrelevant_score,
                    ) = self.process_comment_risk(input_text)

                    # Ensure all variables are set to a non-None default
                    eng_justification = (
                        eng_justification if eng_justification is not None else "None"
                    )
                    malay_justification = (
                        malay_justification
                        if malay_justification is not None
                        else "None"
                    )
                    risk_status = risk_status if risk_status is not None else "None"
                    irrelevant_score = (
                        irrelevant_score if irrelevant_score is not None else "None"
                    )

                    logger.info("Completed process_Comments successfully.")
                except Exception as e:
                    logger.error(f"Error in process_Comments: {e!s}")
                    print(f"Error in process_Comments: {e!s}")
                    eng_justification = "APi server error"
                    malay_justification = "APi server error"
                    risk_status = "APi server error"
                    irrelevant_score = "APi server error"

                processing_time = (datetime.now() - start_time).total_seconds()

                # print("========= comments result =============")
                # print(eng_justification)
                # print(risk_status)
                # print(type(eng_justification))
                # print(type(risk_status))
                # print("=========  =============")

                # # Step 3: Create a AnalysisTableSchema record
                comment_record = CommentsTableSchemaOut(
                    comment_mongodb_id=mapped_record.get("comment_mongodb_id", "Unknown"),
                    video_comment_id=mapped_record.get("video_comment_id", "Unknown"),
                    video_id=mapped_record.get("video_id", "Unknown"),
                    text=mapped_record.get("text", ""),
                    comment_posted_timestamp=mapped_record.get("comment_posted_timestamp", timestamp),
                    comment_like_count=mapped_record.get("comment_like_count", 0),
                    crawling_timestamp=mapped_record.get("crawling_timestamp", timestamp),
                    request_id=mapped_record.get("request_id", "Unknown"),
                    user_handle=mapped_record.get("user_handle", "Unknown"),
                    video_summary=mapped_record.get("video_summary", "None"),
                    category=mapped_record.get("category", "Uncategorized"),
                    subcategory=mapped_record.get("subcategory", "Uncategorized"),
                    agent_name=mapped_record.get("agent_name", "Unknown"),
                    eng_justification=json.dumps(eng_justification if eng_justification else "None"),
                    malay_justification=json.dumps(malay_justification if malay_justification else "None"),
                    risk_status=str(risk_status) if risk_status else "None",
                    irrelevant_score=str(irrelevant_score) if irrelevant_score else "None",
                    timestamp=timestamp,
                    process_time=float(processing_time) if processing_time is not None else 1000.0
                )

                comment_data_list.append(comment_record)

                # **Insert in Batches (Highlighted Change)**
                if (
                    len(comment_data_list) >= batch_size
                ):  # Check if batch size is reached
                    logger.info(
                        f"Inserting {len(comment_data_list)} comments records...",
                    )
                    insert_data_in_batches(
                        session,
                        CommentsTableSchemaOut,
                        comment_data_list,
                        batch_size=batch_size,
                    )
                    comment_data_list.clear()  # Clear the list after inserting

                # # Use SQLAlchemy's inspect function to get column names from the table
                columns = inspect(
                    CommentsTableSchemaOut,
                ).c  # Access columns of the schema

            # Check if a record with the same `comment_mongodb_id` already exists
            existing_record = (
                session.query(CommentsTableSchemaOut)
                .filter_by(
                    comment_mongodb_id=mapped_record["comment_mongodb_id"],
                )
                .first()
            )

            if existing_record:
                # Raise a DuplicateRecordError if a duplicate is found
                logger.error(
                    f"Duplicate record found for comment_mongodb_id: {comment_record.comment_mongodb_id}",
                )
                raise

            # **Final Insert for Remaining Records (Highlighted Change)**
            if comment_data_list:  # Insert remaining sentiment records
                logger.info(
                    f"Inserting remaining {len(comment_data_list)} sentiment records...",
                )
                insert_data_in_batches(
                    session,
                    CommentsTableSchemaOut,
                    comment_data_list,
                    batch_size=batch_size,
                )
                comment_data_list.clear()

            logger.info("All updates completed successfully.")

        except Exception as e:
            logger.error(f"Error processing data: {e}")
            session.rollback()
        finally:
            session.close()
