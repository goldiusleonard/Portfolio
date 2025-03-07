import logging
import os

import requests
from googletrans import Translator
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

# Configure logging
log_filename = "sentiment_analysis.log"  # Name of the log file

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create file handler for logging to a file
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)

# Create console handler for logging to terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter for log messages
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

# Set the formatter for both handlers
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Break
logger.info("------------------------------------------------------------")

# Define your API credentials and model
LLM_BASE_URL = "http://172.210.166.80:8001/v1"
LLM_API_KEY = "llm_api_key_ABC123XYZ"
MODEL = "hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4"


class SentimentAnalyzer:
    def __init__(self) -> None:
        """Initialize sentiment analysis model and translation service."""
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

    def analyze_sentiment_api(self, text: str) -> str:
        """Analyze sentiment using API."""
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
            return sentiment_response  # Return only the sentiment classification
        logger.error(f"API Error: {response.status_code} - {response.text}")
        return None

    def analyze_sentiment_transformer(self, text: str):
        """Analyze sentiment using transformer model."""
        # Get the sentiment analysis result with all emotion scores
        result = self.sentiment_model(text)
        return result

    def analyze_sentiment_with_translation(self, text: str):
        """Analyze sentiment after translating text to English."""
        # Translate the input text to English
        english_translation = self.translator.translate(text, dest="en").text
        logger.info(f"Translated English Text: {english_translation}")
        # Analyze sentiment on the translated text
        sentiment_result = self.analyze_sentiment_transformer(english_translation)
        return sentiment_result

    def analyze_text_files_in_folder(
        self,
        input_folder: str,
        output_folder: str,
    ) -> None:
        """Analyze sentiment in text files and save results."""
        os.makedirs(output_folder, exist_ok=True)
        logger.info(f"Analyzing text files in folder: '{input_folder}'...")

        for filename in os.listdir(input_folder):
            if filename.endswith(".txt"):  # Only process text files
                file_path = os.path.join(input_folder, filename)
                with open(file_path, encoding="utf-8") as file:
                    text = file.read()
                    logger.info(f"Analyzing sentiment for file: '{filename}'")

                    # Analyze sentiment using the API
                    api_sentiment = self.analyze_sentiment_api(text)

                    # Analyze sentiment using the transformer
                    transformer_result = self.analyze_sentiment_with_translation(text)

                    # Sort emotions by score from highest to lowest
                    sorted_emotions = sorted(
                        transformer_result[0],
                        key=lambda x: x["score"],
                        reverse=True,
                    )

                    # Create a new output folder for each text file
                    text_output_folder = os.path.join(
                        output_folder,
                        os.path.splitext(filename)[0],
                    )
                    os.makedirs(text_output_folder, exist_ok=True)

                    # Prepare the output results
                    output_file_path = os.path.join(
                        text_output_folder,
                        f"{os.path.splitext(filename)[0]}_sentiment.txt",
                    )
                    with open(output_file_path, "w", encoding="utf-8") as output_file:
                        # Print each emotion label and its corresponding score
                        for emotion in sorted_emotions:
                            label = emotion["label"]
                            score = round(emotion["score"] * 100, 2)
                            output_file.write(f"{label}: {score}%\n")
                            logger.info(f"{label}: {score}%")

                    # Save the API sentiment result to a separate file
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


######### Main Execution #########
if __name__ == "__main__":
    input_folder = "input_folder"  # Specify your input folder path here
    output_folder = "output_folder"  # Path to your output folder for saving results
    sentiment_analyzer = SentimentAnalyzer()
    sentiment_analyzer.analyze_text_files_in_folder(input_folder, output_folder)
