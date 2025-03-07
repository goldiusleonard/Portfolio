import tempfile
import torch
import whisperx

from typing import Tuple, Union
from ..utils import configure_logging

logger = configure_logging()

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True


class Transcriber:
    def __init__(
        self,
        device="cuda",
        device_index=0,
        batch_size=16,
        compute_type="float32",
        whisper_variant="large-v2",
    ) -> None:
        self.device = device
        self.batch_size = batch_size
        self.compute_type = compute_type
        self.whisper_variant = "userdata/whisper-largeV2-03-ms-v11-LORA-Merged"

        # Load Whisper model
        try:
            logger.info("Loading Whisper model...")

            if ":" in self.device:
                parts = self.device.split(":")
                device = parts[0]
                device_index = int(parts[1])

            self.whisperx_model = whisperx.load_model(
                whisper_variant,
                device=device,
                device_index=device_index,
                compute_type=compute_type,
            )
            logger.info("Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe_video(
        self, video_path, return_text_only=True
    ) -> Union[list, Tuple[str, str]]:
        try:
            logger.info(f"Starting transcription for video '{video_path}'...")
            audio_array = whisperx.load_audio(video_path)
            if audio_array.size == 0:
                logger.warning(f"Audio array for '{video_path}' is empty.")
                return "", ""

            logger.info("Transcribing audio...")
            whisper_original_result = self.whisperx_model.transcribe(
                audio_array, batch_size=self.batch_size
            )
            logger.info(
                f"Transcription result for '{video_path}': {whisper_original_result}"
            )

            if (
                "segments" not in whisper_original_result
                or not whisper_original_result["segments"]
            ):
                logger.warning(
                    f"No segments found in transcription result for '{video_path}'."
                )
                return "", ""

            detected_language = whisper_original_result["language"]
            logger.info(f"Detected language for '{video_path}': {detected_language}")

            # Only process if the detected language is English (en) or Malay (ms)
            if detected_language not in ["en", "ms"]:
                logger.info(
                    f"Skipping transcription as detected language '{detected_language}' is not supported."
                )
                if detected_language is None:
                    detected_language = ""
                return "", detected_language

            all_segments = []
            for segment in whisper_original_result["segments"]:
                t_start, t_end, sentence = (
                    segment["start"],
                    segment["end"],
                    segment["text"],
                )
                all_segments.append(
                    {"text": sentence, "time": {"start": t_start, "end": t_end}}
                )
                logger.debug(f"Segment: {sentence} (Start: {t_start}, End: {t_end})")

            if return_text_only:
                transcript = " ".join([seg["text"] for seg in all_segments]).strip()
                logger.info(f"Final transcript for '{video_path}': {transcript}")
                return transcript, detected_language

            return all_segments
        except Exception as e:
            logger.error(f"Error during transcription of '{video_path}': {e}")
            return "", ""

    def transcribe_video_file(
        self, video_file, return_text_only=True
    ) -> Tuple[str, str]:
        """
        Transcribes a video from a file-like object (e.g., BytesIO or an uploaded file).

        Args:
            video_file: A file-like object representing the video (e.g., BytesIO).
            return_text_only (bool): Whether to return only the transcript text.

        Returns:
            tuple: Transcript (str or list of segments) and detected language (str).
        """
        try:
            # Save the video file temporarily
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as temp_video:
                temp_video.write(video_file.read())
                temp_video_path = temp_video.name

                # Transcribe the temporary video file
                logger.info("Starting transcription from file-like object...")
                transcript, detected_language = self.transcribe_video(
                    temp_video_path, return_text_only
                )

                return transcript, detected_language
        except Exception as e:
            logger.error(f"Error during transcription of video file: {e}")
            return "", ""
