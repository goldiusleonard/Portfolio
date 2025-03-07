import os
import subprocess
import logging
from ..utils import Logger

log = Logger(name="database_logger")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_file_list(input_files, list_file_path):
    """
    Create a file list for FFmpeg to concatenate.
    """
    with open(list_file_path, "w") as f:
        for file in input_files:
            f.write(f"file '{file}'\n")


def concatenate_videos(input_files, output_file):
    """
    Concatenate multiple MP4 files from the given list using FFmpeg.
    """
    if not input_files:
        print("No MP4 files to concatenate.")
        return

    list_file_path = "file_list.txt"
    create_file_list(input_files, list_file_path)

    command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_file_path,
        "-c",
        "copy",
        "-y",
        output_file,
    ]

    try:
        subprocess.run(command, check=True)
        logger.info(f"Videos concatenated successfully into {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error concatenating videos: {e}")
    finally:
        if os.path.exists(list_file_path):
            os.remove(list_file_path)


def add_metadata_to_video(input_file, text):
    """
    Add metadata to the video file and save it to a new file.
    """
    output_file = input_file.replace(".mp4", "_with_metadata.mp4")

    command = [
        "ffmpeg",
        "-i",
        input_file,
        "-metadata",
        f"comment={text}",
        "-codec",
        "copy",
        "-y",
        output_file,
    ]

    subprocess.run(command)
    log.info(f"Added metadata to video, saved as: {output_file}")

    return output_file


def create_empty_mp4(output_file):
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=640x360",
            "-t",
            "1",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            output_file,
        ]
    )

    log.info(f"Empty MP4 file created: {output_file}")
