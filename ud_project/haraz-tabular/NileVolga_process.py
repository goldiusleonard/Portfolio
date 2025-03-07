import asyncio
import os
import pandas as pd

from Nile_caption_agent import DescriptionAgent
from Volga_transc_agent import TranscriptionAgent


nile_url = os.getenv("NILE_URL")
description_agent = DescriptionAgent(nile_url)

volga_url = os.getenv("VOLGA_URL")
transcription_agent = TranscriptionAgent(volga_url)


class NileVolgaProcessor:
    """A class for processing videos."""
    
    @staticmethod
    async def process_all_videos(df: pd.DataFrame) -> pd.DataFrame:
        """Process videos asynchronously for both transcription and description."""

        # Create tasks for the two agents
        transcription_task = asyncio.create_task(transcription_agent.process_videos(df.copy()))
        description_task = asyncio.create_task(description_agent.process_videos(df.copy()))

        # Gather the results concurrently
        processed_transcription, processed_description = await asyncio.gather(transcription_task, description_task)

        # Merge the changes into the original dataframe
        df['video_transcription'] = processed_transcription['video_transcription']
        df['video_description'] = processed_description['video_description']

        return df