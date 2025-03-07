import os

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

    def analyze_sentiment_api(self, text):
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json",
        }

        # Create a prompt that instructs the model to determine sentiment
        prompt = f'Classify the sentiment of the following text as Positive, Negative, or Neutral (strictly only one word from Negative, Positive, or Neutral):\n\n"{text}"\n\nSentiment:'
        data = {
            "model": MODEL,
            "prompt": prompt,
        }

        response = requests.post(
            f"{LLM_BASE_URL}/completions",
            headers=headers,
            json=data,
        )

        if response.status_code == 200:
            result = response.json()
            sentiment_response = result.get("choices")[0].get("text").strip()
            logger.info(f"API Sentiment: {sentiment_response}")
            return sentiment_response
        logger.error(f"API Error: {response.status_code} - {response.text}")
        return None

    def analyze_sentiment_transformer(self, text):
        result = self.sentiment_model(text)
        return result

    def analyze_sentiment_with_translation(self, text):
        english_translation = self.translator.translate(text, dest="en").text
        logger.info(f"Translated English Text: {english_translation}")
        sentiment_result = self.analyze_sentiment_transformer(english_translation)
        return sentiment_result

    def analyze_text_files_in_folder(self, input_folder, output_folder):
        os.makedirs(output_folder, exist_ok=True)
        logger.info(f"Analyzing text files in folder: '{input_folder}'...")

        for filename in os.listdir(input_folder):
            if filename.endswith(".txt"):
                file_path = os.path.join(input_folder, filename)
                with open(file_path, encoding="utf-8") as file:
                    text = file.read()
                    logger.info(f"Analyzing sentiment for file: '{filename}'")

                    api_sentiment = self.analyze_sentiment_api(text)
                    transformer_result = self.analyze_sentiment_with_translation(text)

                    sorted_emotions = sorted(
                        transformer_result[0],
                        key=lambda x: x["score"],
                        reverse=True,
                    )

                    text_output_folder = os.path.join(
                        output_folder,
                        os.path.splitext(filename)[0],
                    )
                    os.makedirs(text_output_folder, exist_ok=True)

                    output_file_path = os.path.join(
                        text_output_folder,
                        f"{os.path.splitext(filename)[0]}_sentiment.txt",
                    )
                    with open(output_file_path, "w", encoding="utf-8") as output_file:
                        for emotion in sorted_emotions:
                            label = emotion["label"]
                            score = round(emotion["score"] * 100, 2)
                            output_file.write(f"{label}: {score}%\n")
                            logger.info(f"{label}: {score}%")

                    api_output_file_path = os.path.join(
                        text_output_folder,
                        f"{os.path.splitext(filename)[0]}_api_sentiment.txt",
                    )
                    with open(
                        api_output_file_path,
                        "w",
                        encoding="utf-8",
                    ) as api_output_file:
                        api_output_file.write(f"API Sentiment: {api_sentiment}\n")
                        logger.info(f"API sentiment saved to '{api_output_file_path}'.")


if __name__ == "__main__":
    input_folder = "input_folder"  # Specify your input folder path here
    output_folder = "output_folder"  # Specify your output folder path here
    sentiment_analyzer = SentimentAnalyzer()
    sentiment_analyzer.analyze_text_files_in_folder(input_folder, output_folder)
