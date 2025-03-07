import asyncio
import aiohttp
import pandas as pd
from logging_section import setup_logging
from fastapi import HTTPException

logger = setup_logging()


class DescriptionAgent:
    """Handles video caption generation with API."""

    def __init__(self, url: str):
        self.url = url

    async def generate_description(self, session, video_path: str) -> str:
        """Calls the API to generate description for a given video.."""
        try:
            async with session.get(self.url,  params={"video_path": video_path}) as response:
                response.raise_for_status()
                data = await response.json()
                if "video_description" not in data:
                    raise ValueError("Missing 'video_description' in the API response")
                return data.get("video_description", "No description available")
        
        except aiohttp.ClientError as e:
            logger.error(f"Error calling the Nile API: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error calling the Nile API: {e}"
            )
        except ValueError as e:
            logger.error(f"Invalid API response: {e}")
            raise HTTPException(
                status_code=500, detail="Invalid API response: e"
            )

    async def process_videos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate video captions asynchronously."""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.generate_description(session, row["video_path"])
                for _, row in df.iterrows()
            ]
            descriptions = await asyncio.gather(*tasks)
            
        df["video_description"] = descriptions
        logger.info("Video description generation complete")
        return df
