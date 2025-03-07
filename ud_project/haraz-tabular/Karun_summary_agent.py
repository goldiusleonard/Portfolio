from typing import Tuple
import pandas as pd
import requests
from fastapi import HTTPException
from logging_section import setup_logging

logger = setup_logging()


class SummaryAgent:
    """Handles text summarization with API."""

    def __init__(self, url: str):
        self.url = url

    def summarize(self, text: str) -> str:
        """Summarize the given text using an external API."""
        try:
            response = requests.post(self.url, json={"text": text})
            response.raise_for_status()
            return response.json().get("summary", "No summary available")
        except requests.RequestException as e:
            logger.error(f"Error calling the summary agent: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error calling the summary agent: {e}"
            )

    def generate_summaries(
        self, df: pd.DataFrame, comments_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Summarize video-related text fields and merge summaries with comments."""
        total_rows = len(df)

        # Summarize the text fields for each row and log progress
        def summarize_with_progress(row):
            row_text = " ".join(
                row[["video_description", "transcription", "title"]].dropna()
            )
            logger.info(f"Processing summary for row {row['id']}/{total_rows}")  # Log progress
            return self.summarize(row_text)

        df["video_summary"] = df.apply(summarize_with_progress, axis=1)

        # Merge video summaries with comments
        comments_df = comments_df.merge(
            df[["video_id", "video_summary"]], on="video_id", how="inner"
        )

        logger.info("Summarization and merging complete.")
        return df, comments_df
