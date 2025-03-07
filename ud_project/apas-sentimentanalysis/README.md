# Apas Sentiment Analysis Tool 🎭📊

---

This project, **Sentiment Analysis Tool**, is an automated **Apas Analysis Application** that leverages **Transformers**, **Specific Meta-Llama-3.1-70B-Instruct-AWQ-INT4 LLM** and **Google Translate API** for accurate sentiment detection. It supports multiple languages by translating input text into English and then classifying the sentiment using a custom RoBERTa-based model and LLM.

## Repository Link
You can access this repository on Azure DevOps [here](https://dev.azure.com/userdata-ada/marketplace/_git/apas-sentimentanalysis).

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
This project is designed for efficient sentiment analysis on text data, especially for batch processing. It uses a custom model based on RoBERTa to classify emotions within text files and supports visualization of emotion distribution as pie charts.

## Getting Started

This section will guide you through setting up **Sentiment Analysis Tool** on your local machine.

### 1. Installation Process

1. **Clone the repository**:

    - git clone https://dev.azure.com/userdata-ada/marketplace/_git/apas-sentimentanalysis -b main

2. **Set up a virtual environment (optional but recommended)**:

    - python -m venv env
    - source env/bin/activate  # For Windows, use `env\Scripts\activate`

3. **Install required packages:**:

    - pip install -r requirements.txt

### 2. Software Dependencies

- Python 3.8 or higher
- Transformers for RoBERTa model operations
- LLM (Meta-Llama-3.1-70B-Instruct-AWQ-INT4) need credentials
- Googletrans for language translation
- Matplotlib for plotting emotion distribution
- Logging for progress tracking and debugging

### 3. Latest Releases

Check the Releases section in this Azure DevOps repository for the latest version and feature updates.

### 4. API References

- Transformers API by Hugging Face supports RoBERTa model integration.
- Google Translate API for language translation.

## Build and Test

Follow these steps to run and test the sentiment analyzer:

> 1. Prepare folders:

Create `input_folder` (for text input) and `output_folder` (for results) folders in the project directory, or specify alternative paths directly in the code.

> 2. Run the sentiment analyzer:

    - python apas_db_final.py

This will analyze all text files in `MySQL summary table`, saving the output in `MySQL sentiment table`.

> 3. Validate results:

Check the output in `sentiment table` for sentiment classifications and emotion distributions.
Customize parameters such as translation, model selection, and visualization as needed.

---

## Version

> **Current Version**:
> # ![1.2.0](https://img.shields.io/badge/version-1.2.0-brightgreen)
- Added Docker File.
- The output for sentiment_api will now be mapped to a number (1=postitive, 0=neutral, -1=negative).
- Enahnced logging.
- Fastapi enhancements for input values and output values.


> **Previous Versions**:
> # ![1.0.0](https://img.shields.io/badge/version-1.0.0-lightgray)

> # ![1.1.0](https://img.shields.io/badge/version-1.1.0-lightgray)
- Added Connections To MySQL as for the input and the output.
- The output will be _id (as the key), sentiment, sentiment_score, sentiment_api, sentiment_api_score.
- Enahnced detailed logging.
- Modulerized the code.
- Added scoring for both results from two models.
- Initial release of Sentiment Analysis Tool.
- Features include sentiment analysis with RoBERTa, emotion visualization, and support for multiple languages.

### Developer

> ![Developed by Ahmedalla](https://img.shields.io/badge/Developed%20by-Ahmedalla%20%40%20Userdata-blue?style=plastic&logo=azure)

