from datetime import datetime

from config.config_num import Num
from config.config_risk_samples import risk_levels_general, risk_levels_sample
from log_mongo import logger
from processing.process import process_with_agent
from schema.output_schemas import (
    TikTokTableSchemaOut,
)


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
    try:
        # Access the subcategory dictionary
        subcategory_data = risk_levels_dict[category][subcategory]
        return subcategory_data
    except KeyError:
        # Return None if the category or subcategory is not found
        print(f"Category '{category}' or Subcategory '{subcategory}' not found.")
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


class DataProcessorPipeline_v00:
    def __init__(self, agentsprocess, db, df, config=None):
        self.agentsprocess = agentsprocess
        self.db = db
        self.df = df.copy()
        self.config = config

    def process_summary(self, index, input_text):
        for col in [Num.VIDEO_SUMMARY]:
            if col not in self.df.columns:
                self.df[col] = "None"

        process_with_agent(
            self.agentsprocess.get_summary_output,
            input_text,
            self.df,
            index,
            {
                Num.VIDEO_SUMMARY,
            },
        )

    def process_category(self, index, input_text):
        for col in [Num.CATEGORY, Num.SUBCATEGORIES]:
            if col not in self.df.columns:
                self.df[col] = "None"

        process_with_agent(
            self.agentsprocess.get_category_output,
            input_text,
            self.df,
            index,
            {
                Num.CATEGORY: Num.CATEGORY,
                Num.SUBCATEGORIES: Num.SUBCATEGORIES,
            },
        )

    def process_sentiment(self, index, input_text):
        default_values = {
            Num.SENTIMENT: "None",
            Num.SENTIMENT_SCORE: 0.0,
            Num.API_SENTIMENT: "None",
            Num.API_SENTIMENT_SCORE: 0.0,
        }
        for i, col in enumerate(
            [
                Num.SENTIMENT,
                Num.SENTIMENT_SCORE,
                Num.API_SENTIMENT,
                Num.API_SENTIMENT_SCORE,
            ],
        ):
            if col not in self.df.columns:
                self.df[col] = default_values[i]

        process_with_agent(
            self.agentsprocess.get_sentiment_output,
            input_text,
            self.df,
            index,
            {
                Num.SENTIMENT: "transformer.sentiment",
                Num.SENTIMENT_SCORE: "transformer.sentiment_score",
                Num.API_SENTIMENT: "api.sentiment",
                Num.API_SENTIMENT_SCORE: "api.sentiment_score",
            },
        )

    def process_justification(self, index, input_text):
        for col in [
            Num.ENGLISH_JUSTIFICATION,
            Num.MALAY_JUSTIFICATION,
            Num.RISK_STATUS,
            Num.IRRELEVANT_SCORE,
        ]:
            if col not in self.df.columns:
                self.df[col] = "None"

        process_with_agent(
            self.agentsprocess.get_justification_risk_output,
            input_text,
            self.df,
            index,
            {
                Num.ENGLISH_JUSTIFICATION: Num.ENGLISH_JUSTIFICATION,
                Num.MALAY_JUSTIFICATION: Num.MALAY_JUSTIFICATION,
                Num.RISK_STATUS: Num.RISK_STATUS,
                Num.IRRELEVANT_SCORE: Num.IRRELEVANT_SCORE,
            },
        )

    def process_law(self, index, input_text):
        # Do not put new line (\n) for this input
        input_text = remove_quotes(input_text)

        law = self.agentsprocess.get_law_regulated_output(input_text)
        return law

    def process_comment_risk(self, index, input_text):
        for col in [Num.RISK_STATUS]:
            if col not in self.df.columns:
                self.df[col] = None
        for col in [
            Num.ENGLISH_JUSTIFICATION,
            Num.MALAY_JUSTIFICATION,
            Num.RISK_STATUS,
            Num.IRRELEVANT_SCORE,
        ]:
            if col not in self.df.columns:
                self.df[col] = None

        process_with_agent(
            self.agentsprocess.get_comment_risk_output,
            input_text,
            self.df,
            index,
            {
                Num.ENGLISH_JUSTIFICATION: Num.ENGLISH_JUSTIFICATION,
                Num.MALAY_JUSTIFICATION: Num.MALAY_JUSTIFICATION,
                Num.RISK_STATUS: Num.RISK_STATUS,
                Num.IRRELEVANT_SCORE: Num.IRRELEVANT_SCORE,
            },
        )

    def run_all_agents_pipeline(self, key_id):
        try:
            for index, row in self.df.iterrows():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                start_time = datetime.now()

                # try:
                #     input_text = "\n".join(
                #             [
                #                 str(self.df.loc[index, Num.TITLE]),
                #                 str(self.df.loc[index, Num.VIDEO_DESCRIPTION]),
                #                 str(self.df.loc[index, Num.TRANSCRIPTION])
                #             ],
                #         )
                #     # self.process_summary(index, input_text)
                #     self.df.loc[index, Num.VIDEO_SUMMARY] = "None"
                # except Exception as e:
                #     logger.error(f"Error in process_summary_v0: {str(e)}")
                #     print(f"Error in process_summary_v0: {str(e)}")

                try:
                    input_text = str(self.df.loc[index, Num.VIDEO_SUMMARY])
                    self.process_category(index, input_text)
                    # self.df.loc[index, Num.CATEGORY] = "None"
                    # self.df.loc[index, Num.SUBCATEGORIES] = "None"
                except Exception as e:
                    logger.error(f"Error in process_category_v0: {e!s}")
                    print(f"Error in process_category_v0: {e!s}")
                    self.df.loc[index, Num.CATEGORY] = "APi server error"
                    self.df.loc[index, Num.SUBCATEGORIES] = "APi server error"

                try:
                    input_text = str(self.df.loc[index, Num.VIDEO_SUMMARY])
                    self.process_sentiment(index, input_text)
                    # self.df.loc[index, Num.SENTIMENT] = "None"
                    # self.df.loc[index, Num.SENTIMENT_SCORE] = 0.0
                    # self.df.loc[index, Num.API_SENTIMENT] = "None"
                    # self.df.loc[index, Num.API_SENTIMENT_SCORE] = 0.0
                except Exception as e:
                    logger.error(f"Error in process_sentiment_v0: {e!s}")
                    print(f"Error in process_sentiment_v0: {e!s}")
                    self.df.loc[index, Num.SENTIMENT] = "APi server error"
                    self.df.loc[index, Num.SENTIMENT_SCORE] = 0.0
                    self.df.loc[index, Num.API_SENTIMENT] = "APi server error"
                    self.df.loc[index, Num.API_SENTIMENT_SCORE] = 0.0

                try:
                    category_name = (
                        str(self.df.loc[index, Num.CATEGORY])
                        if Num.CATEGORY in self.df.columns
                        else "None"
                    )
                    sub_category_name = (
                        str(self.df.loc[index, Num.SUBCATEGORIES])
                        if Num.SUBCATEGORIES in self.df.columns
                        else "None"
                    )
                    # category_name = "None"
                    # sub_category_name = "None"
                    risk_levels = risk_levels_sample
                    risk_level = str(
                        get_risk_levels(category_name, sub_category_name, risk_levels),
                    )

                    input_text = "\n".join(
                        [
                            str(self.df.loc[index, Num.VIDEO_SUMMARY]),
                            str(self.df.loc[index, Num.CATEGORY]),
                            str(self.df.loc[index, Num.SUBCATEGORIES]),
                            str(risk_level),
                        ],
                    )
                    self.process_justification(index, input_text)
                    # self.df.loc[index, Num.ENGLISH_JUSTIFICATION] = "None"
                    # self.df.loc[index, Num.MALAY_JUSTIFICATION] = "None"
                    # self.df.loc[index, Num.RISK_STATUS] = "None"
                    # self.df.loc[index, Num.IRRELEVANT_SCORE] = "None"
                except Exception as e:
                    logger.error(f"Error in process_justification_v0: {e!s}")
                    print(f"Error in process_justification_v0: {e!s}")
                    self.df.loc[index, Num.ENGLISH_JUSTIFICATION] = "APi server error"
                    self.df.loc[index, Num.MALAY_JUSTIFICATION] = "APi server error"
                    self.df.loc[index, Num.RISK_STATUS] = "APi server error"
                    self.df.loc[index, Num.IRRELEVANT_SCORE] = "APi server error"

                try:
                    input_text = "\n".join(
                        [
                            str(self.df.loc[index, Num.SUBCATEGORIES]),
                            str(self.df.loc[index, Num.VIDEO_SUMMARY]),
                            str(self.df.loc[index, Num.VIDEO_DESCRIPTION]),
                            str(self.df.loc[index, Num.TRANSCRIPTION]),
                            str(self.df.loc[index, Num.RISK_STATUS]),
                            str(self.df.loc[index, Num.ENGLISH_JUSTIFICATION]),
                        ],
                    )
                    law = self.process_law(index, input_text)
                    self.df.loc[index, Num.LAW_REGULATED_OUT] = str(law)
                    # self.df.loc[index, Num.LAW_REGULATED_OUT] = "None"
                except Exception as e:
                    logger.error(f"Error in process_law_v0: {e!s}")
                    print(f"Error in process_law_v0: {e!s}")
                    self.df.loc[index, Num.LAW_REGULATED_OUT] = "APi server error"

                self.df.loc[index, Num.TIMESTAMP] = timestamp
                processing_time = (datetime.now() - start_time).total_seconds()
                self.df.loc[index, Num.PROCESS_TIME] = processing_time

                try:
                    table_row = self.df.loc[index]
                    schema = TikTokTableSchemaOut
                    # # Assuming `table_row` is a pandas Series or a dictionary
                    # valid_columns = [column.name for column in schema.__table__.columns]
                    # table_row = {key: value for key, value in table_row.items() if key in valid_columns}

                    # Fetch existing record by key_id
                    existing_record = (
                        self.db.session.query(schema)
                        .filter(getattr(schema, key_id) == table_row[key_id])
                        .first()
                    )

                    if existing_record:
                        logger.info(
                            f"Duplicate row found, skipping insertion: {table_row}",
                        )
                    else:
                        # Insert the row if it does not exist
                        self.db.insert_row_by_row(key_id, schema, table_row, index)
                        logger.info("Row inserted successfully in process all agents.")
                except KeyError as e:
                    logger.error(
                        f"KeyError in process all agents: {e!s} - Check if '{key_id}' exists in the row: {table_row}",
                    )

                except AttributeError as e:
                    logger.error(
                        f"AttributeError in process all agents: {e!s} - Check if schema or key_id is valid.",
                    )

                except Exception as e:
                    logger.exception("Error in inserting row in process all agents")
                    print(f"Error in inserting row in process all agents: {e!s}")

                finally:
                    logger.info("Finished processing this row.")

        finally:
            # Ensure the database is closed even if an error occurs
            self.db.session.close()
            logger.info("Database connection closed.")

        logger.info("Preproceed all agents pipeline completed.")

    def run_summary_agent_pipeline(self, key_id, config):
        for index, row in self.df.iterrows():
            try:
                input_text = config.text
                self.process_summary(index, input_text)
            except Exception as e:
                logger.error(f"Error in process_summary_v0: {e!s}")
                print(f"Error in process_summary_v0: {e!s}")

            try:
                # table_row = db.schema(**df.loc[index].to_dict())
                table_row = self.df.loc[index]
                schema = self.db.create_table_schema(
                    config.output_table_name,
                    config.columns,
                )
                self.db.insert_row_by_row(key_id, schema, table_row, index)
            except Exception as e:
                logger.error(f"Error in inserting row in process_summary_v0: {e!s}")
                print(f"Error in inserting row in process_summary_v0: {e!s}")

    def run_category_agent_pipeline(self, key_id, config):
        for index, row in self.df.iterrows():
            try:
                input_text = config.text
                self.process_category(index, input_text)
            except Exception as e:
                logger.error(f"Error in process_category_v0: {e!s}")
                print(f"Error in process_category_v0: {e!s}")

            try:
                # table_row = db.schema(**df.loc[index].to_dict())
                table_row = self.df.loc[index]
                schema = self.db.create_table_schema(
                    config.output_table_name,
                    config.columns,
                )
                self.db.insert_row_by_row(key_id, schema, table_row, index)
            except Exception as e:
                logger.error(f"Error in inserting row in process_category_v0: {e!s}")
                print(f"Error in inserting row in process_category_v0: {e!s}")

    def run_sentiment_agent_pipeline(self, key_id, config):
        for index, row in self.df.iterrows():
            try:
                input_text = "\n".join(
                    [str(row[column]) for column in config.input_columns_name]
                )
                self.process_sentiment(index, input_text)
            except Exception as e:
                logger.error(f"Error in process_sentiment_v0: {e!s}")
                print(f"Error in process_sentiment_v0: {e!s}")

            try:
                # table_row = db.schema(**df.loc[index].to_dict())
                table_row = self.df.loc[index]
                schema = self.db.create_table_schema(
                    config.output_table_name,
                    config.columns,
                )
                # Reflect the table using MetaData
                self.db.insert_row_by_row(key_id, schema, table_row.to_dict(), index)
            except Exception as e:
                logger.error(f"Error in inserting row in process_sentiment_v0: {e!s}")
                print(f"Error in inserting row in process_sentiment_v0: {e!s}")

    def run_justification_risk_agent_pipeline(self, key_id, config):
        for index, row in self.df.iterrows():
            try:
                if not self.config.category:
                    category_name = "Scam"
                    logger.warning("Category name not defined by user.")
                else:
                    category_name = self.config.category

                if not self.config.subcategory:
                    sub_category_name = "Forex"
                    logger.warning("Subcategory name not defined by user.")
                else:
                    sub_category_name = self.config.subcategory

                if not self.config.risk_levels:
                    risk_level = str(
                        get_risk_levels(
                            category_name,
                            sub_category_name,
                            risk_levels_sample,
                        ),
                    )
                else:
                    risk_level = self.config.risk_levels

                if not risk_level:
                    risk_level = risk_levels_general

                input_text = config.text
                self.process_justification(index, input_text)
            except Exception as e:
                logger.error(f"Error in process_justification_v0: {e!s}")
                print(f"Error in process_justification_v0: {e!s}")

            try:
                # table_row = db.schema(**df.loc[index].to_dict())
                table_row = self.df.loc[index]
                schema = self.db.create_table_schema(
                    config.output_table_name,
                    config.columns,
                )
                self.db.insert_row_by_row(key_id, schema, table_row, index)
            except Exception as e:
                logger.error(
                    f"Error in inserting row in process_justification_v0: {e!s}",
                )
                print(f"Error in inserting row in process_justification_v0: {e!s}")

    def run_law_agent_pipeline(self, key_id, config):
        for index, row in self.df.iterrows():
            try:
                files = [
                    "Penal_Code.json.law_document.extraction.test",
                    "akta-15-akta-hasutan-1948.v2.en.law_document",
                ]
                input_text = config.text
                law = self.process_law(index, input_text, files)
                self.df.loc[index, Num.LAW_REGULATED_OUT] = law
            except Exception as e:
                logger.error(f"Error in process_law_v0: {e!s}")
                print(f"Error in process_law_v0: {e!s}")

            try:
                # table_row = db.schema(**df.loc[index].to_dict())
                table_row = self.df.loc[index]
                schema = self.db.create_table_schema(
                    config.output_table_name,
                    config.columns,
                )
                self.db.insert_row_by_row(key_id, schema, table_row, index)
            except Exception as e:
                logger.error(f"Error in inserting row in process_law_v0: {e!s}")
                print(f"Error in inserting row in process_law_v0: {e!s}")

    def run_comment_risk_agent_pipeline(self, key_id, config):
        for index, row in self.df.iterrows():
            # Agents analysis
            try:
                # category_name = str(self.df.loc[index, Num.CATEGORY]) if Num.CATEGORY in self.df.columns else "None"
                # sub_category_name = str(self.df.loc[index, Num.SUBCATEGORIES]) if Num.SUBCATEGORIES in self.df.columns else "None"
                category_name = "None"
                sub_category_name = "None"

                if not self.config.risk_levels:
                    risk_levels = risk_levels_sample
                else:
                    risk_levels = self.config.risk_levels

                risk_level = str(
                    get_risk_levels(category_name, sub_category_name, risk_levels),
                )
                if not risk_level:
                    risk_level = "None"
                risk_level = str(
                    get_risk_levels(category_name, sub_category_name, risk_levels),
                )

                risk_level = risk_levels_general

                input_text = config.text

                print("Calling process_comment_v0...")
                self.process_comment_risk(index, input_text)
                logger.info("Completed process_comment_v0 successfully.")

            except Exception as e:
                logger.error(f"Error in process_comment_v0: {e!s}")
                print(f"Error in process_comment_v0: {e!s}")

            try:
                print("Start inserting row in process_comment_v0...")
                # table_row = db.schema(**df.loc[index].to_dict())
                table_row = self.df.loc[index]
                schema = self.db.create_table_schema(
                    config.output_table_name,
                    config.columns,
                )
                existing_record = (
                    self.db.session.query(schema)
                    .filter(getattr(schema, key_id) == row[key_id])
                    .first()
                )
                if existing_record:
                    logger.info(f"Duplicate row found, skipping insertion: {row}")
                else:
                    self.db.insert_row_by_row(key_id, schema, table_row, index)
                    logger.info("Inserting row in process_comment_v0 successfully.")
            except Exception as e:
                logger.error(f"Error in inserting row in process_comment_v0: {e!s}")
                print(f"Error in inserting row in process_comment_v0: {e!s}")


# Define a function to handle missing values
def handle_missing_value(value, default="None"):
    """Returns the value if it exists, otherwise returns the default value."""
    return value if value else default


class DataProcessorPipeline_v01:
    def __init__(self, agentsprocess, db, config=None):
        self.agentsprocess = agentsprocess
        self.db = db
        self.config = config

    def process_summary(self, input_text):
        data = self.agentsprocess.get_summary_output(input_text)
        summary = handle_missing_value(
            data,
            default="None",
        )
        return summary

    def process_category(self, input_text):
        data = self.agentsprocess.get_category_output(input_text)
        category = handle_missing_value(
            data[Num.CATEGORY],
            default="None",
        )
        subcategory = handle_missing_value(
            data[Num.SUBCATEGORY],
            default="None",
        )
        return (category, subcategory)

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


    def process_law(self, input_text):
        # Remove quotes and prepare the input text
        input_text = remove_quotes(input_text)
        
        try:
            # Log the input_text before making the request (only a snippet if it's too long)
            logger.info(f"Processing law for input: {input_text[:500]}...")  # Log a snippet of the input
            
            # Make the API request to get the law-regulated output
            law = self.agentsprocess.get_law_regulated_output(input_text)
            
            # If law is None, set it to "None"
            law = handle_missing_value(law, default="None")
            
            return law
        
        except Exception as e:
            # Log the error, including full traceback for better debugging
            logger.error(f"Error in get_law_regulated_output: {e!s}", exc_info=True)
            
            # Return a default value if there is an error
            return "API server error"
        
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

    def run_all_agents_pipeline(self, key_id, df):
        try:
            for index, row in df.iterrows():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                start_time = datetime.now()

                # try:
                #     input_text = "\n".join(
                #             [
                #                 str(df.loc[index, Num.TITLE]),
                #                 str(df.loc[index, Num.VIDEO_DESCRIPTION]),
                #                 str(df.loc[index, Num.TRANSCRIPTION])
                #             ],
                #         )
                #     summary = self.process_summary(index, input_text)
                #     summary = summary if summary is not None else "None"
                #     df.loc[index, Num.VIDEO_SUMMARY] = summary
                # except Exception as e:
                #     logger.error(f"Error in process_summary_v0: {str(e)}")
                #     print(f"Error in process_summary_v0: {str(e)}")
                #     df.loc[index, Num.VIDEO_SUMMARY] ="APi server error"

                try:
                    input_text = str(df.loc[index, Num.VIDEO_SUMMARY])
                    category, subcategory = self.process_category(input_text)
                    print("@@@@@@@@@@@@@@@@@@")
                    print(category, subcategory)
                    category = category if category is not None else "None"
                    subcategory = subcategory if subcategory is not None else "None"
                    df.loc[index, Num.CATEGORY] = str(category)
                    df.loc[index, Num.SUBCATEGORY] = str(subcategory)
                except Exception as e:
                    logger.error(f"Error in process_category_v0: {e!s}")
                    print(f"Error in process_category_v0: {e!s}")
                    df.loc[index, Num.CATEGORY] = "APi server error"
                    df.loc[index, Num.SUBCATEGORY] = "APi server error"

                try:
                    input_text = str(df.loc[index, Num.VIDEO_SUMMARY])
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
                        api_sentiment_score if api_sentiment_score is not None else 0.0
                    )
                    df.loc[index, Num.SENTIMENT] = str(sentiment)
                    df.loc[index, Num.SENTIMENT_SCORE] = float(sentiment_score)
                    df.loc[index, Num.API_SENTIMENT] = str(api_sentiment)
                    df.loc[index, Num.API_SENTIMENT_SCORE] = float(api_sentiment_score)
                except Exception as e:
                    logger.error(f"Error in process_sentiment_v0: {e!s}")
                    print(f"Error in process_sentiment_v0: {e!s}")
                    df.loc[index, Num.SENTIMENT] = "APi server error"
                    df.loc[index, Num.SENTIMENT_SCORE] = 0.0
                    df.loc[index, Num.API_SENTIMENT] = "APi server error"
                    df.loc[index, Num.API_SENTIMENT_SCORE] = 0.0

                try:
                    risk_levels = risk_levels_sample
                    risk_level = str(
                        get_risk_levels(category, subcategory, risk_levels),
                    )
                    input_text = "\n".join(
                        [
                            str(df.loc[index, Num.VIDEO_SUMMARY]),
                            str(category),
                            str(subcategory),
                            str(risk_level),
                        ],
                    )
                    (
                        eng_justification,
                        malay_justification,
                        risk_status,
                        irrelevant_score,
                    ) = self.process_justification(input_text)

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
                    df.loc[index, Num.ENGLISH_JUSTIFICATION] = str(eng_justification)
                    df.loc[index, Num.MALAY_JUSTIFICATION] = str(malay_justification)
                    df.loc[index, Num.RISK_STATUS] = str(risk_status)
                    df.loc[index, Num.IRRELEVANT_SCORE] = str(irrelevant_score)
                except Exception as e:
                    logger.error(f"Error in process_justification_v0: {e!s}")
                    print(f"Error in process_justification_v0: {e!s}")
                    df.loc[index, Num.ENGLISH_JUSTIFICATION] = "APi server error"
                    df.loc[index, Num.MALAY_JUSTIFICATION] = "APi server error"
                    df.loc[index, Num.RISK_STATUS] = "APi server error"
                    df.loc[index, Num.IRRELEVANT_SCORE] = "APi server error"

                try:
                    input_text = "\n".join(
                        [
                            str(subcategory),
                            str(df.loc[index, Num.VIDEO_SUMMARY]),
                            str(df.loc[index, Num.VIDEO_DESCRIPTION]),
                            str(df.loc[index, Num.TRANSCRIPTION]),
                            str(risk_status),
                            str(eng_justification),
                        ],
                    )

                    law = self.process_law(input_text)
                    law = law if law is not None else "None"
                    df.loc[index, Num.LAW_REGULATED_OUT] = str(law)
                except Exception as e:
                    logger.error(f"Error in process_law_v0: {e!s}")
                    print(f"Error in process_law_v0: {e!s}")
                    df.loc[index, Num.LAW_REGULATED_OUT] = "APi server error"

                df.loc[index, Num.TIMESTAMP] = timestamp
                processing_time = (datetime.now() - start_time).total_seconds()
                df.loc[index, Num.PROCESS_TIME] = processing_time

                try:
                    table_row = df.loc[index]
                    schema = TikTokTableSchemaOut
                    # # Assuming `table_row` is a pandas Series or a dictionary
                    # valid_columns = [column.name for column in schema.__table__.columns]
                    # table_row = {key: value for key, value in table_row.items() if key in valid_columns}

                    # Fetch existing record by key_id
                    existing_record = (
                        self.db.session.query(schema)
                        .filter(getattr(schema, key_id) == table_row[key_id])
                        .first()
                    )

                    if existing_record:
                        logger.info(
                            f"Duplicate row found, skipping insertion: {table_row}",
                        )
                    else:
                        # Insert the row if it does not exist
                        self.db.insert_row_by_row(key_id, schema, table_row, index)
                        logger.info("Row inserted successfully in process all agents.")
                except KeyError as e:
                    logger.error(
                        f"KeyError in process all agents: {e!s} - Check if '{key_id}' exists in the row: {table_row}",
                    )

                except AttributeError as e:
                    logger.error(
                        f"AttributeError in process all agents: {e!s} - Check if schema or key_id is valid.",
                    )

                except Exception as e:
                    logger.exception("Error in inserting row in process all agents")
                    print(f"Error in inserting row in process all agents: {e!s}")

                finally:
                    logger.info("Finished processing this row.")

        finally:
            # Ensure the database is closed even if an error occurs
            self.db.session.close()
            logger.info("Database connection closed.")

        logger.info("Preproceed all agents pipeline completed.")


    def run_all_agents_pipeline_batch(self, key_id, df, batch_size=100):
        try:
            rows_to_insert = []  # List to accumulate rows for batch insertion
            
            for index, row in df.iterrows():
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                start_time = datetime.now()

                # Processing steps for Category and Subcategory
                try:
                    input_text = str(df.loc[index, Num.VIDEO_SUMMARY])
                    category, subcategory = self.process_category(input_text)
                    category = category if category is not None else "None"
                    subcategory = subcategory if subcategory is not None else "None"
                    df.loc[index, Num.CATEGORY] = str(category)
                    df.loc[index, Num.SUBCATEGORY] = str(subcategory)
                except Exception as e:
                    logger.error(f"Error in process_category_v0: {e!s}")
                    df.loc[index, Num.CATEGORY] = "API server error"
                    df.loc[index, Num.SUBCATEGORY] = "API server error"

                # Processing steps for Sentiment
                try:
                    input_text = str(df.loc[index, Num.VIDEO_SUMMARY])
                    sentiment, sentiment_score, api_sentiment, api_sentiment_score = self.process_sentiment(input_text)
                    df.loc[index, Num.SENTIMENT] = str(sentiment if sentiment else "None")
                    df.loc[index, Num.SENTIMENT_SCORE] = float(sentiment_score if sentiment_score else 0.0)
                    df.loc[index, Num.API_SENTIMENT] = str(api_sentiment if api_sentiment else "None")
                    df.loc[index, Num.API_SENTIMENT_SCORE] = float(api_sentiment_score if api_sentiment_score else 0.0)
                except Exception as e:
                    logger.error(f"Error in process_sentiment_v0: {e!s}")
                    df.loc[index, Num.SENTIMENT] = "API server error"
                    df.loc[index, Num.SENTIMENT_SCORE] = 0.0
                    df.loc[index, Num.API_SENTIMENT] = "API server error"
                    df.loc[index, Num.API_SENTIMENT_SCORE] = 0.0

                # Processing steps for Risk Level, Justification, and Law
                try:
                    risk_levels = risk_levels_sample  # Define the risk levels sample
                    risk_level = str(get_risk_levels(category, subcategory, risk_levels))
                    input_text = "\n".join([str(df.loc[index, Num.VIDEO_SUMMARY]), str(category), str(subcategory), str(risk_level)])
                    
                    eng_justification, malay_justification, risk_status, irrelevant_score = self.process_justification(input_text)

                    # Assign values and handle missing/None values
                    eng_justification = eng_justification if eng_justification is not None else "None"
                    malay_justification = malay_justification if malay_justification is not None else "None"
                    risk_status = risk_status if risk_status is not None else "None"
                    irrelevant_score = irrelevant_score if irrelevant_score is not None else "None"

                    df.loc[index, Num.ENGLISH_JUSTIFICATION] = str(eng_justification)
                    df.loc[index, Num.MALAY_JUSTIFICATION] = str(malay_justification)
                    df.loc[index, Num.RISK_STATUS] = str(risk_status)
                    df.loc[index, Num.IRRELEVANT_SCORE] = str(irrelevant_score)
                except Exception as e:
                    logger.error(f"Error in process_justification_v0: {e!s}")
                    df.loc[index, Num.ENGLISH_JUSTIFICATION] = "API server error"
                    df.loc[index, Num.MALAY_JUSTIFICATION] = "API server error"
                    df.loc[index, Num.RISK_STATUS] = "API server error"
                    df.loc[index, Num.IRRELEVANT_SCORE] = "API server error"

                # Processing steps for Law Regulation
                try:
                    input_text = "\n".join([
                        str(subcategory),
                        str(df.loc[index, Num.VIDEO_SUMMARY]),
                        str(df.loc[index, Num.VIDEO_DESCRIPTION]),
                        str(df.loc[index, Num.TRANSCRIPTION]),
                        str(risk_status),
                        str(eng_justification),
                    ])
                    law = self.process_law(input_text)
                    law = law if law is not None else "None"
                    df.loc[index, Num.LAW_REGULATED_OUT] = str(law)
                except Exception as e:
                    logger.error(f"Error in process_law_v0: {e!s}")
                    df.loc[index, Num.LAW_REGULATED_OUT] = "API server error"

                # Adding timestamp and processing time
                df.loc[index, Num.TIMESTAMP] = timestamp
                processing_time = (datetime.now() - start_time).total_seconds()
                df.loc[index, Num.PROCESS_TIME] = processing_time

                # Append processed row to the list of rows to insert
                table_row = df.loc[index]
                rows_to_insert.append(table_row)

                # Check if we've reached the batch size
                if len(rows_to_insert) >= batch_size:
                    self.insert_batch(key_id, rows_to_insert, schema=TikTokTableSchemaOut)
                    rows_to_insert.clear()  # Clear the list for the next batch

            # After the loop, insert any remaining rows
            if rows_to_insert:
                self.insert_batch(key_id, rows_to_insert, schema=TikTokTableSchemaOut)

        except Exception as e:
            logger.exception("Error during pipeline execution")
            print(f"Error in pipeline execution: {e!s}")

        finally:
            self.db.session.close()
            logger.info("Database connection closed.")
            logger.info("Preprocess all agents pipeline completed.")


    def insert_batch(self, key_id, rows, schema):
        try:
            # Assuming `self.db.insert_row_by_row` requires `key_id`, `schema`, and an additional index `i`
            for i, row in enumerate(rows):
                # Add additional checks or column filtering if needed
                existing_record = (
                    self.db.session.query(schema)
                    .filter(getattr(schema, key_id) == row[key_id])
                    .first()
                )

                if existing_record:
                    logger.info(f"Duplicate row found, skipping insertion: {row}")
                else:
                    # Insert the row, passing the index `i` along with the other arguments
                    self.db.insert_row_by_row(key_id, schema, row, i)
                    logger.info(f"Row {i} inserted successfully in batch.")
        except Exception as e:
            logger.exception("Error in batch insertion")
            print(f"Error in batch insertion: {e!s}")