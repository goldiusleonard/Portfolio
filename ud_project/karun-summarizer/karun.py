import aiohttp
import asyncio
import csv
import logging
import os
import pandas as pd

from datetime import datetime
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional

# Create logs directory (if not exist)
os.makedirs("logs", exist_ok=True)


# Initialize logging configuration
def setup_logging():
    logger = logging.getLogger("summarizer")

    # Set base logging level
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    # Configure rotating file handler
    log_file = f'logs/summarizer_{datetime.now().strftime("%Y%m%d")}.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024,  # 1 MB max file size
        backupCount=5,  # Keep 5 backup files
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)

    # Set up formatter patterns
    file_format = logging.Formatter(
        fmt="%(asctime)s,%(msecs)03d | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_format = logging.Formatter("%(message)s")

    # Apply file formatter
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Set up console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_format)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger


class LLMConfig:
    def __init__(
        self, base_url: str, api_key: str, model: str, tone: str, summary_format: str
    ):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.tone = tone
        self.summary_format = summary_format


class SummaryGenerator:
    # Initialize with LLM configuration
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logging.getLogger("summarizer")

    # Calculate appropriate summary length based on input text length
    def _calculate_summary_length(self, text: str) -> int:
        word_count = len(text.split())

        if word_count <= 50:
            return min(word_count, 25)  # Very short text
        elif word_count <= 200:
            return min(word_count // 3, 50)  # Short text
        elif word_count <= 500:
            return min(word_count // 4, 75)  # Medium text
        else:
            return 100  # Cap at 100 words for long text

    # Create API request payload
    def _create_payload(self, transcript: str, perspective: str) -> Dict:
        # Calculate appropriate summary length
        target_length = self._calculate_summary_length(transcript)

        # Define output format rules
        format_instructions = {
            "paragraph": (
                f"""
                - EXACTLY ONE paragraph (no line breaks)
                - Approximately {target_length} words
                - No bullet points or lists
                - No paragraph breaks
                - Keep it concise but informative
                """
            ),
            "bullets": (
                """
                - STRICTLY use EXACTLY between 3-7 bullet points ONLY
                - Start each point with '•'
                - DO NOT end points with periods or full stops
                - Focus on key information only
                - Output ONLY the bullet points, no other text
                - Do not number the points
                """
            ),
        }

        # Define system prompt
        system_content = f"""
            You are Karun Agent - an advanced text summarization assistant capable of processing any type of text content. 
            Your summaries MUST follow these rules:
            - {self.config.tone} in tone
            - STRICTLY in English ONLY - translate any non-English content to English
            - Complete thoughts and maintain context while being concise
            - Focus on summarizing from the perspective of {perspective if perspective else 'a general viewer'}
            {format_instructions[self.config.summary_format]}
            Failure to follow any of these rules is not acceptable.
            ALWAYS translate and summarize in English, regardless of the input language.
            """

        # Define user prompt
        user_content = (
            f"Analyze and summarize the following content in English bullet points, focusing on key information: {transcript}"
            if self.config.summary_format == "bullets"
            else f"Analyze and summarize the following content in ONE English paragraph of approximately {target_length} words: {transcript}"
        )

        # Build and return API request payload
        return {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.5,  # Balance between creativity and consistency
        }

    async def generate_summary(
        self, transcript: str, perspective: str = None
    ) -> Optional[str]:
        # Set API request headers
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        # Prepare API request data
        payload = self._create_payload(transcript, perspective)

        # Make API request and process response
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.config.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as response:
                    response.raise_for_status()
                    response_data = await response.json()
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        # Extract and format summary text
                        summary = response_data["choices"][0]["message"]["content"]
                        summary_lines = [
                            line.strip()
                            for line in summary.splitlines()
                            if line.strip()
                            and (
                                self.config.summary_format != "bullets"
                                or line.strip().startswith("•")
                            )
                        ]
                        # Return "None" if no valid summary was generated
                        return "\n".join(summary_lines) if summary_lines else "None"
                    else:
                        self.logger.error(
                            "Invalid response format: 'choices' key is missing or empty"
                        )
                        return "None"
            except aiohttp.ClientError as e:
                self.logger.error(f"Error generating summary: {str(e)}")
                return "None"


# Add error handling for missing input files
async def process_csv_data(
    generator: SummaryGenerator,
    volga_file: str,
    captions_file: str,
    crawled_file: str,
    output_file: str,
):
    logger = logging.getLogger("summarizer")

    # Check if input files exist
    for file_path in [volga_file, captions_file, crawled_file]:
        if not os.path.exists(file_path):
            logger.error(f"Input file not found: {file_path}")
            raise FileNotFoundError(f"Input file not found: {file_path}")

    try:
        # Read CSV files
        df_volga = pd.read_csv(volga_file)
        df_captions = pd.read_csv(captions_file)
        df_crawled = pd.read_csv(crawled_file)

        # Keep only required columns
        if "_id" not in df_volga.columns or "transcription" not in df_volga.columns:
            logger.error("Required columns not found in volga results file")
            return

        # Merge the dataframes on _id
        df = (
            df_volga[["_id", "transcription"]]
            .merge(df_captions[["_id", "video_description"]], on="_id", how="left")
            .merge(df_crawled[["_id", "title", "perspective"]], on="_id", how="left")
        )

        # Fill NaN values with empty strings
        df["video_description"] = df["video_description"].fillna("")
        df["transcription"] = df["transcription"].fillna("")
        df["title"] = df["title"].fillna("")
        df["perspective"] = df["perspective"].fillna("general")

        # Add new column for summaries
        df["video_summary"] = ""

        # Process each row
        for index, row in df.iterrows():
            # Check if both transcription and description are empty (regardless of title)
            if (
                not row["transcription"].strip()
                and not row["video_description"].strip()
            ):
                logger.warning(
                    f"Skipping row {index + 1}: No transcription or description available"
                )
                df.at[index, "video_summary"] = "None"
                continue

            # Combine inputs for summary generation
            text = (
                f"Title: {row['title'].strip()}\n"
                f"Video Description: {row['video_description'].strip()}\n"
                f"Transcription: {row['transcription'].strip()}"
            ).strip()

            # Generate video summary using combined text and perspective
            start_time = datetime.now()
            summary = await generator.generate_summary(text, row["perspective"])
            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Store summary
            df.at[index, "video_summary"] = (
                summary.strip('" \'"').replace('""', '"') if summary else "None"
            )
            logger.info(
                f"Generated summary for row {index + 1} (took {processing_time:.0f}ms)"
            )

        # Keep only required columns for output
        df = df[["_id", "video_summary"]]

        # Save results to output CSV
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False, quoting=csv.QUOTE_MINIMAL)
        logger.info(f"Successfully saved summaries to {output_file}")

    except Exception as e:
        logger.error(f"Error processing CSV: {str(e)}")
        raise


async def main():
    # Set up logging and load environment variables
    logger = setup_logging()
    load_dotenv()

    # Check for required environment variables
    required_vars = ["LLM_BASE_URL", "LLM_API_KEY", "MODEL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    # Get tone setting with default
    tone = os.getenv("TONE", "neutral").lower()

    # Validate tone setting
    if tone not in ["neutral", "informative", "formal"]:
        logger.warning(f"Invalid TONE '{tone}', using 'neutral'")
        tone = "neutral"

    # Validate summary format with default
    summary_format = os.getenv("SUMMARY_FORMAT", "paragraph").lower()

    # Validate summary format
    if summary_format not in ["paragraph", "bullets"]:
        logger.warning(f"Invalid SUMMARY_FORMAT '{summary_format}', using 'paragraph'")
        summary_format = "paragraph"

    # Create LLM configuration
    config = LLMConfig(
        base_url=os.getenv("LLM_BASE_URL"),
        api_key=os.getenv("LLM_API_KEY"),
        model=os.getenv("MODEL"),
        tone=tone,
        summary_format=summary_format,
    )

    # Define input and output file paths
    input_files = {
        "volga": "data/volga_results_dev.csv",  # Transcription data
        "captions": "data/video_captions.csv",  # Video descriptions
        "crawled": "data/preprocessed_crawled_data.csv",  # Video titles and perspectives
    }
    output_file = "data/video_summary.csv"

    # Initialize summary generator and process CSV data
    generator = SummaryGenerator(config)
    await process_csv_data(
        generator,
        input_files["volga"],
        input_files["captions"],
        input_files["crawled"],
        output_file,
    )


if __name__ == "__main__":
    asyncio.run(main())
