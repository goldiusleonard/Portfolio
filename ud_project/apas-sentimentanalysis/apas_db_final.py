import os

import mysql.connector
import requests
from dotenv import load_dotenv
from googletrans import Translator
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from logging_section import setup_logger

# Load environment variables
load_dotenv()

# Fetch credentials from .env file
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_API_KEY = os.getenv("LLM_API_KEY")
MODEL = os.getenv("MODEL")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))

# Set up the logger
logger = setup_logger()


class SentimentAnalyzer:
    def __init__(self) -> None:
        # Load the custom model and tokenizer for sentiment analysis
        model_name = "SamLowe/roberta-base-go_emotions"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)

        # Set up the sentiment analysis pipeline
        self.sentiment_model = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            return_all_scores=True,
        )

        # Initialize the translator
        self.translator = Translator()
        logger.info("Sentiment analysis model and translator loaded successfully.")

        # Establish MySQL connection
        self.db_connection = mysql.connector.connect(
            host=MYSQL_HOST,
            database=MYSQL_DATABASE,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            port=MYSQL_PORT,
        )
        self.cursor = self.db_connection.cursor(dictionary=True)
        logger.info("Connected to the database successfully.")

    def analyze_sentiment_api(self, text):
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        }

        prompt = f'Classify the sentiment of the following text as Positive, Negative, or Neutral (strictly only one word from Negative, Positive, or Neutral):\n\n"{text}"\n\nSentiment:'
        data = {
            "model": MODEL,
            "prompt": prompt,
            "logprobs": 1,  # Request log probabilities if supported
        }

        try:
            response = requests.post(
                f"{LLM_BASE_URL}/completions",
                headers=headers,
                json=data,
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(f"API Response: {result}")

                # Extract sentiment and score
                choices = result.get("choices")
                if choices and len(choices) > 0:
                    sentiment_response = choices[0].get("text", "").strip()
                    logprobs = choices[0].get("logprobs", {})

                    if logprobs:
                        # Calculate confidence score from log probabilities
                        token_logprobs = logprobs.get("token_logprobs", [])
                        if token_logprobs:
                            avg_logprob = sum(token_logprobs) / len(token_logprobs)
                            sentiment_score = round(
                                100 * (2.718**avg_logprob),
                                2,
                            )  # Convert log-probability
                        else:
                            sentiment_score = 0.8  # Default confidence
                    else:
                        sentiment_score = 0.8  # Fallback confidence

                    return sentiment_response, sentiment_score

                logger.error("API response does not contain 'choices' or is malformed.")
                return None, None
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return None, None

        except requests.exceptions.RequestException as e:
            logger.error(f"API Request failed: {e}")
            return None, None

    def analyze_sentiment_transformer(self, text):
        result = self.sentiment_model(text)
        return result

    def process_videos(self):
        # Create the output table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS video_sentiment (
            _id INT PRIMARY KEY,
            sentiment VARCHAR(255),
            sentiment_score FLOAT,
            sentiment_api VARCHAR(255),
            sentiment_api_score FLOAT
        );
        """
        self.cursor.execute(create_table_query)
        self.db_connection.commit()
        logger.info("Ensured the output table 'video_sentiment' exists.")

        # Fetch unprocessed rows from video_summary
        fetch_query = "SELECT _id, video_summary FROM video_summary WHERE _id NOT IN (SELECT _id FROM video_sentiment);"
        self.cursor.execute(fetch_query)
        rows = self.cursor.fetchall()

        for row in rows:
            _id = str(row["_id"])
            video_summary = row["video_summary"]

            # Process sentiment using the transformer model
            transformer_result = self.analyze_sentiment_transformer(video_summary)
            sorted_emotions = sorted(
                transformer_result[0],
                key=lambda x: x["score"],
                reverse=True,
            )
            top_sentiment = sorted_emotions[0]["label"]
            top_sentiment_score = sorted_emotions[0]["score"]

            # Process sentiment using the API
            sentiment_api, sentiment_api_score = self.analyze_sentiment_api(
                video_summary,
            )

            # Insert the results into video_sentiment
            insert_query = """
            INSERT INTO video_sentiment (_id, sentiment, sentiment_score, sentiment_api, sentiment_api_score)
            VALUES (%s, %s, %s, %s, %s);
            """
            self.cursor.execute(
                insert_query,
                (
                    _id,
                    top_sentiment,
                    top_sentiment_score,
                    sentiment_api,
                    sentiment_api_score,
                ),
            )
            self.db_connection.commit()
            logger.info(f"Processed and inserted sentiment analysis for _id: {_id}")


if __name__ == "__main__":
    sentiment_analyzer = SentimentAnalyzer()
    sentiment_analyzer.process_videos()
