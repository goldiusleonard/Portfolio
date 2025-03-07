# Summarizer - Karun Agent

A versatile text summarization system powered by Large Language Models (LLMs). Karun Agent processes various types of text content to generate concise, informative summaries while preserving the original context, with support for multiple output formats and multilingual content.

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Configuration](#configuration)
- [Features](#features)
- [Usage](#usage)
- [Logging](#logging)
- [Contributing](#contributing)
- [License](#license)

## Getting Started

### Prerequisites

- Python 3.7 or higher
- MySQL database
- `pip` package manager
- Access to LLM API endpoint (Llama-based model)
- Virtual environment

### Installation

1. **Clone this repository:**

   ```bash
   git clone https://userdata-ada@dev.azure.com/userdata-ada/karun-summarizer/_git/karun-summarizer
   cd Karun_Summarizer
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**

   Create a `.env` file in the project root and configure your environment variables:

   ```properties
   LLM_BASE_URL="http://your-llm-api-endpoint"
   LLM_API_KEY="your-api-key"
   MODEL="your-llm-model"
   TONE="summary-tone-preference"
   SUMMARY_FORMAT="bullets"  # or "paragraph"
   ```

## Configuration

The application uses environment variables for configuration, loaded from the `.env` file:

**Environment Variables:**

- `LLM_BASE_URL`: URL of your LLM API endpoint
- `LLM_API_KEY`: Your API key for authentication
- `MODEL`: LLM model name (e.g., "hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4")
- `TONE`: Summary tone preference (e.g., "informative")
- `SUMMARY_FORMAT`: Output format ("paragraph" or "bullets")
- `MYSQL_*`: MySQL database connection settings

## Features

- **Universal Text Processing**: Summarizes any text content type
- **Flexible Output Formats**: Support for paragraph or bullet-point summaries
- **Configurable Tone**: Adjustable summary tone (neutral, informative, formal)
- **Multilingual Support**: Auto-translates and summarizes non-English content
- **API Access**: FastAPI endpoint for real-time summarization
- **Database Integration**: MySQL support for data persistence
- **Smart Length Adjustment**: Automatically adjusts summary length based on input
- **Detailed Logging**: Comprehensive logging system with rotation

## Usage

1. **API Mode:**

   ```bash
   python karun_fastapi.py
   ```

   Access the API at `http://localhost:8000/summary?text=your_text_here`

2. **Batch Processing Mode:**

   ```bash
   python karun.py
   ```

   Processes text content from CSV files and saves summaries

3. **Database Operations:**

   ```bash
   # Export from database to CSV
   python db_export.py
   
   # Import summaries back to database
   python db_import.py
   ```

## API Endpoints

- GET `/summary`
  - Query parameter: `text` (required)
  - Returns: JSON with summarized text
  - Example: `curl "http://localhost:8000/summary?text=Your+text+here"`

## Logging

The application implements rotating file-based logging:

- **Format**: `YYYY-MM-DD HH:MM:SS | LEVEL | Message`
- **Levels**: INFO for successful processing, WARNING for skipped items
- **Rotation**: 1MB max file size with 5 backup files
- **Location**: All logs stored in `logs/` directory

Example log entries:

## Contributing

1. Fork the repository.
2. Create your feature branch.
3. Commit your changes.
4. Push to the branch.
5. Create a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
