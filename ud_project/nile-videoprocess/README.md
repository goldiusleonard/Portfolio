# Nile Video Processing Tool 🎞️
---

This project, **Video Captioning Tool**, is an automated **Video Captioning System** that uses the **BLIP** model for generating captions from video frames. It supports batch processing of multiple videos from a specified folder, saving the results in a structured output format.

## Repository Link
You can access this repository on Azure DevOps [here](https://dev.azure.com/userdata-ada/marketplace/_git/nile-videoprocess).

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
This project aims to streamline video captioning tasks, making it easy to process and generate captions from video files (supported formats include `.mp4`, `.wav`, and `.mkv`). Using the **BLIP** model, this tool provides automated caption generation by processing video frames.

## Getting Started

This section will guide you through setting up **Video Captioning Tool** on your local machine.

### 1. Installation Process

1. **Clone the repository**:

    - git clone https://dev.azure.com/userdata-ada/marketplace/_git/nile-videoprocess -b main

2. **Set up a virtual environment (optional but recommended)**:

    - python -m venv env
    - source env/bin/activate  # For Windows, use `env\Scriptsctivate`

3. **Install required packages:**:

    - pip install -r requirements.txt

### 2. Software Dependencies

- Python 3.8 or higher
- PyTorch for optimized processing on GPU/CPU
- Transformers for BLIP model operations
- OpenCV for video processing
- Logging for progress tracking and debugging

### 3. Latest Releases

Check the Releases section in this Azure DevOps repository for the latest version and feature updates.

### 4. API References

- BLIP API from Salesforce provides image captioning capabilities.
- Transformers API by Hugging Face supports BLIP model integration.

## Build and Test

Follow these steps to run and test the captioning tool:

> 1. Prepare folders:

Create video_folder (input) and output_folder (output) folders in the project directory, or specify alternative paths directly in the code.

> 2. Run the captioner:

python nile_final.py

This will caption all videos in the selected DB.

> 3. Validate captions:

Check the output in output_folder for correct captions and timestamp information.
Customize parameters like FPS rate, model type, and other configurations as needed.

---

## Version

> **Current Version**:
> # ![1.1.0](https://img.shields.io/badge/version-1.1.0-brightgreen)
- Added Connections To Mongo DB as input, and MySQL as for the output.
- The output will be _id (as the key), and video_description.
- Enahnced detailed logging.
- Modulerized the code.
- To handle processed video by downloading it locally to process then to delete it as it done processing 
(temp downloads folder)

> **Previous Versions**:
> # ![1.0.0](https://img.shields.io/badge/version-1.0.0-lightgray)

- Initial release of Video Captioning Tool Nile.
- Features include video captioning, batch processing of video files, and support for BLIP model.

### Developer

> ![Developed by Ahmedalla](https://img.shields.io/badge/Developed%20by-Ahmedalla%20%40%20Userdata-blue?style=plastic&logo=azure)