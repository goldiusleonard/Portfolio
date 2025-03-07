# Volga Audio Processing 🎙️
---

This project, **Volga Audio Processing**, is an automated **Audio Transcription Tool** that uses **Whisper** and **Transformers** for efficient transcription of audio within video files. It supports Malay language detection and batch processing of multiple videos from a specified folder, saving the results in a structured output format.

## Repository Link
You can access this repository on Azure DevOps [here](https://dev.azure.com/userdata-ada/marketplace/_git/marketplace?version=GBAhmedalla_Volga_AudioProcessing).

---

# Table of Contents
- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Installation Process](#installation-process)
  - [Software Dependencies](#software-dependencies)
  - [Latest Releases](#latest-releases)
  - [API References](#api-references)
- [Build and Test](#build-and-test)
- [Version](#version)


---

## Introduction
This project aims to streamline audio transcription tasks, making it easy to process and transcribe audio from video files (supported formats include `.mp4`, `.wav`, and `.mkv`). Using a custom Whisper model and helper functions, this tool provides accurate language detection and transcriptions, especially optimized for the Malay language.

## Getting Started

This section will guide you through setting up **Volga Audio Processing** on your local machine.

### 1. Installation Process

1. **Clone the repository**:

    - git clone https://dev.azure.com/userdata-ada/_git/volga-audioprocess -b main

2. **Set up a virtual environment (optional but recommended)**:

    - python -m venv env
    - source env/bin/activate  # For Windows, use `env\Scripts\activate`

3. **Install required packages:**:

    - pip install -r requirements.txt

### 2. Software Dependencies

- Python 3.8 or higher
- Libcudnn 8.x (Libcudnn 9 and later will not work)
- PyTorch for optimized processing on GPU/CPU
- Transformers for Whisper model operations
- WhisperX for audio loading and manipulation
- Logging for progress tracking and debugging

### 3. Latest Releases

Check the Releases section in this Azure DevOps repository for the latest version and feature updates.

### 4. API References

- Whisper API from OpenAI provides transcription and translation.
- Transformers API by Hugging Face supports Whisper model integration.

## Build and Test

Follow these steps to run and test the transcriber:

> 1. Prepare folders:

Create video_folder (input) and output_folder (output) folders in the project directory, or specify alternative paths directly in the code.
For version 1.1.0: all done using DB credentials.

> 2. Run the transcriber:

python transcribe.py
For version 1.1.0: python transcribe_final.py


> 3. Validate transcriptions:

Check the output in output_folder for correct transcriptions and language detections.
Customize parameters like batch size, compute type, and Whisper variant as needed.
Or check in the DB.
---

## Version

> **Current Version**:
> # ![1.1.0](https://img.shields.io/badge/version-1.1.0-brightgreen)
- Added Connections To Mongo DB as input, and MySQL as for the output.
- The output will be _id (as the key), video_language, and transcripton columns.
- Enahnced detailed logging.
- Modulerized the code.
- To handle processed video by downloading it locally to process then to delete it as it done processing 
(temp downloads folder)

> **Previous Versions**:
> # ![1.0.0](https://img.shields.io/badge/version-1.0.0-lightgray)
- Initial release of Volga Audio Processing.
- Features include audio transcription, batch processing of video files, language detection, and support for Malay language.

### Developer

> ![Developed by Ahmedalla](https://img.shields.io/badge/Developed%20by-Ahmedalla%20%40%20Userdata-blue?style=plastic&logo=azure)







