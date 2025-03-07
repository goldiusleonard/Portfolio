import asyncio
import aiohttp
import pandas as pd
from logging_section import setup_logging
from fastapi import HTTPException

logger = setup_logging()


class TranscriptionAgent:
    """Handles video transcription generation with API."""

    def __init__(self, url: str):
        self.url = url

    async def generate_transcription(self, session, video_path: str) -> str:
        """Generate captions for a given video path using an external API."""
        try:
            async with session.get(self.url, params={"video_path": video_path}) as response:
                response.raise_for_status()
                data = await response.json()
                if "video_transcription" not in data:
                    raise ValueError("Missing 'video_transcription' in the API response")
                return data.get("video_transcription", "No description available")
        
        except aiohttp.ClientError as e:
            logger.error(f"Error calling the Nile API: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error calling the Nile API: {e}"
            )
        except ValueError as e:
            logger.error(f"Invalid API response: {e}")
            raise HTTPException(
                status_code=500, detail=f"Invalid API response: {e}"
            )

    async def process_videos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate video transcriptions asynchronously."""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.generate_transcription(session, row["video_path"])
                for _, row in df.iterrows()
            ]
            transcriptions = await asyncio.gather(*tasks)
            
        df["video_transcription"] = transcriptions
        logger.info("Video transcription generation complete")
        return df


    # async def _process_videos_async(self, df: pd.DataFrame) -> pd.DataFrame:
    #     """Generate video transcriptions asynchronously."""
    #     async with aiohttp.ClientSession() as session:
    #         tasks = [
    #             self.generate_transcription(session, row["video_path"])
    #             for _, row in df.iterrows()
    #         ]
    #         transcriptions = await asyncio.gather(*tasks)
            
    #     df["video_transcription"] = transcriptions
    #     logger.info("Video transcription generation complete")
    #     return df


    # def process_videos(self, df: pd.DataFrame) -> pd.DataFrame:
    #      """Generate video transcriptions with progress logging."""
    #      return asyncio.run(self._process_videos_async(df))
    

    # def process_videos(self, df: pd.DataFrame) -> pd.DataFrame:
    #     """Generate video transcriptions with progress logging."""
    #     total_rows = len(df)

    #     # Generate captions for each video and log progress
    #     def generate_with_progress(row):
    #         logger.info(f"Processing transcription for row {row['id']}/{total_rows}")
    #         return self.generate_transcription(row["video_path"])

    #     df["video_description"] = df.apply(generate_with_progress, axis=1)
    #     logger.info("Video description generation complete")
    #     return df 