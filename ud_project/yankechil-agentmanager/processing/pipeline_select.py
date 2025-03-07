
from config.config_num import Num
from log_mongo import logger


# Define a function to handle missing values
def handle_missing_value(value, default="None"):
    """Returns the value if it exists, otherwise returns the default value."""
    return value if value else default


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
        # Do not put new line (\n) for this input
        input_text = remove_quotes(input_text)
        law = self.agentsprocess.get_law_regulated_output(input_text)
        return law

    def process_law_v1(self, input_text, files):
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

   
    def insert_data_in_batches(self, session, table_name, data, batch_size=5):
        """
        Insert data into a table in batches. Converts ORM objects to dictionaries if necessary.
        """
        from sqlalchemy import Table

        try:
            # Reflect the table using MetaData
            table = Table(
                table_name,
                self.db.metadata,
                autoload_with=self.db.engine,
            )

            if not isinstance(data, list):
                raise ValueError("Input data must be a list")

            # Split data into batches
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                session.execute(table.insert(), batch)
                session.commit()
                logger.info(f"Batch of {len(batch)} records committed successfully.")

        except Exception as e:
            session.rollback()  # Roll back in case of error
            logger.error(f"Error in batch commit: {e!s}")
            print(f"Error in batch commit: {e!s}")


    def run_summary_agent_pipeline(self, key_id, config, batch_size=5):
        batch_data = []  # To store rows for batch processing
        try:
            # Process each row in the dataframe
            for index, row in self.df.iterrows():
                try:
                    # Prepare input text for processing
                    columns_name = config.input_columns_name[0].split(",")
                    input_text = "\n".join(
                        [str(row[column]) for column in columns_name]
                    )
                    summary = self.process_summary(input_text)
                    summary = summary if summary is not None else "None"
                except Exception as e:
                    logger.error(f"Error in process_summary_v0: {e!s}")
                    print(f"Error in process_summary_v0: {e!s}")
                    summary = "APi server error"

                # Collect data for batch insertion
                batch_data.append({
                    key_id: row[key_id],  # Use the primary key column
                    "summary": str(summary)
                })

                # Commit in batches
                if len(batch_data) >= batch_size:
                    self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data, batch_size)
                    batch_data = []  # Clear the batch after committing

            # Commit any remaining rows in the batch
            if batch_data:
                self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data, batch_size)

        except Exception as e:
            logger.error(f"Error in run_summary_agent_pipeline: {e!s}")
            print(f"Error in run_summary_agent_pipeline: {e!s}")

    def run_category_agent_pipeline(self, key_id, config, batch_size=5):
        batch_data = []
        for index, row in self.df.iterrows():
            try:
                columns_name = config.input_columns_name[0].split(",")
                input_text = "\n".join([str(row[column]) for column in columns_name])
                category, subcategory = self.process_category(input_text)
                category = category if category is not None else "None"
                subcategory = subcategory if subcategory is not None else "None"
            except Exception as e:
                logger.error(f"Error in process_category: {e!s}")
                category = "API server error"
                subcategory = "API server error"

            batch_data.append({
                key_id: row[key_id],
                "category": str(category),
                "subcategory": str(subcategory),
            })

            if len(batch_data) >= batch_size:
                self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data)
                batch_data = []

        # Insert any remaining data
        if batch_data:
            self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data)

    def run_sentiment_agent_pipeline(self, key_id, config, batch_size=5):
        batch_data = []
        for index, row in self.df.iterrows():
            try:
                columns_name = config.input_columns_name[0].split(",")
                input_text = "\n".join([str(row[column]) for column in columns_name])
                sentiment, sentiment_score, api_sentiment, api_sentiment_score = self.process_sentiment(input_text)
                sentiment = sentiment if sentiment is not None else "None"
                sentiment_score = sentiment_score if sentiment_score is not None else 0.0
                api_sentiment = api_sentiment if api_sentiment is not None else "None"
                api_sentiment_score = api_sentiment_score if api_sentiment_score is not None else 0.0
            except Exception as e:
                logger.error(f"Error in process_sentiment: {e!s}")
                sentiment = "API server error"
                sentiment_score = 0.0
                api_sentiment = "API server error"
                api_sentiment_score = 0.0

            batch_data.append({
                key_id: row[key_id],
                "sentiment": str(sentiment),
                "sentiment_score": float(sentiment_score),
                "api_sentiment": str(api_sentiment),
                "api_sentiment_score": float(api_sentiment_score),
            })

            if len(batch_data) >= batch_size:
                self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data)
                batch_data = []

        if batch_data:
            self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data)

    def run_justification_risk_agent_pipeline(self, key_id, config, batch_size=5):
        batch_data = []
        for index, row in self.df.iterrows():
            try:
                columns_name = config.input_columns_name[0].split(",")
                input_text = "\n".join([str(row[column]) for column in columns_name])
                eng_justification, malay_justification, risk_status, irrelevant_score = self.process_justification(input_text)
                eng_justification = eng_justification if eng_justification is not None else "None"
                malay_justification = malay_justification if malay_justification is not None else "None"
                risk_status = risk_status if risk_status is not None else "None"
                irrelevant_score = irrelevant_score if irrelevant_score is not None else "None"
            except Exception as e:
                logger.error(f"Error in process_justification: {e!s}")
                eng_justification = "API server error"
                malay_justification = "API server error"
                risk_status = "API server error"
                irrelevant_score = "API server error"

            batch_data.append({
                key_id: row[key_id],
                "eng_justification": str(eng_justification),
                "malay_justification": str(malay_justification),
                "risk_status": str(risk_status),
                "irrelevant_score": str(irrelevant_score),
            })

            if len(batch_data) >= batch_size:
                self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data)
                batch_data = []

        if batch_data:
            self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data)

    def run_law_agent_pipeline(self, key_id, config, batch_size=5):
        batch_data = []
        for index, row in self.df.iterrows():
            try:
                columns_name = config.input_columns_name[0].split(",")
                input_text = "\n".join([str(row[column]) for column in columns_name])
                law = self.process_law(input_text)
                law = law if law is not None else "None"
            except Exception as e:
                logger.error(f"Error in process_law: {e!s}")
                law = "API server error"

            batch_data.append({
                key_id: row[key_id],
                "law_regulated": str(law),
            })

            if len(batch_data) >= batch_size:
                self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data)
                batch_data = []

        if batch_data:
            self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data)

    def run_comment_risk_agent_pipeline(self, key_id, config, batch_size=5):
        batch_data = []
        for index, row in self.df.iterrows():
            try:
                columns_name = config.input_columns_name[0].split(",")
                input_text = "\n".join([str(row[column]) for column in columns_name])
                eng_justification, malay_justification, risk_status, irrelevant_score = self.process_comment_risk(input_text)
                eng_justification = eng_justification if eng_justification is not None else "None"
                malay_justification = malay_justification if malay_justification is not None else "None"
                risk_status = risk_status if risk_status is not None else "None"
                irrelevant_score = irrelevant_score if irrelevant_score is not None else "None"
            except Exception as e:
                logger.error(f"Error in process_comments: {e!s}")
                eng_justification = "API server error"
                malay_justification = "API server error"
                risk_status = "API server error"
                irrelevant_score = "API server error"

            batch_data.append({
                key_id: row[key_id],
                "eng_justification": str(eng_justification),
                "malay_justification": str(malay_justification),
                "risk_status": str(risk_status),
                "irrelevant_score": str(irrelevant_score),
            })

            if len(batch_data) >= batch_size:
                self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data)
                batch_data = []

        if batch_data:
            self.insert_data_in_batches(self.db.session, config.output_table_name, batch_data)

