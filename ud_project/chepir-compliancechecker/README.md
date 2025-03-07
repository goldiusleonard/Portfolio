# Compliance Checker - Chepir Agent

An AI-powered compliance checking system that analyzes content against Malaysian laws and TikTok community guidelines using advanced vector similarity search and LLM analysis.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Features](#features)
6. [Usage](#usage)
7. [Logging](#logging)
8. [Contributing](#contributing)
9. [License](#license)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- MySQL 8.0 or higher for data export
- Qdrant vector database server
- Access to LLM API endpoint
- Required reference documents in TXT format:
  - Communications and Multimedia Act 1998 (CMA)
  - Malaysian Penal Code
  - Sedition Act 1948
  - TikTok Community Guidelines

### Installation

1. Clone the repository:

   ```bash
   git clone https://userdata-ada@dev.azure.com/userdata-ada/chepir-compliancechecker/_git/chepir-compliancechecker
   cd Chepir_Compliance_Checker
   ```

2. Create and activate virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Set up environment variables in `.env`:

   ```env
   # LLM Configuration
   LLM_BASE_URL="your_llm_endpoint"
   LLM_API_KEY="your_llm_api_key"
   MODEL="your_model_name"

   # MySQL Configuration
   MYSQL_HOST="your_mysql_host"
   MYSQL_DATABASE="your_database"
   MYSQL_USER="your_username"
   MYSQL_PASSWORD="your_password"
   MYSQL_PORT=3306

   # Qdrant Configuration
   QDRANT_HOST="your_qdrant_host"
   QDRANT_API_KEY="your_qdrant_api_key"
   ```

2. Directory Structure Setup:

   ```bash
   mkdir -p data logs output references
   ```

3. Place reference documents in the `references` directory:

   ```plaintext
   references/
   ├── cma_1998.txt          # Communications and Multimedia Act
   ├── penal_code.txt        # Malaysian Penal Code
   ├── sedition_act_1948.txt # Sedition Act
   └── tiktok_guidelines.txt # TikTok Community Guidelines
   ```

## Features

- **Multi-Source Analysis**: Processes text content against multiple legal references
- **Vector Search**: Uses Qdrant for efficient similarity search
- **LLM Integration**: Advanced content analysis using LLM
- **API Support**: FastAPI endpoint for real-time checking
- **Comprehensive Logging**: Detailed operation logs with rotation
- **Batch Processing**: Support for bulk content analysis
- **MySQL Integration**: Export capabilities to MySQL database
- **Health Monitoring**: Connection status checks for services

## Usage

1. Verify service connections:

   ```bash
   python qdrant_healthcheck.py
   ```

2. Load reference documents:

   ```bash
   python reference_loader.py
   ```

3. Run compliance checks:

   - Using CLI:

     ```bash
     python chepir.py
     ```

   - Using API server:

     ```bash
     python chepir_fastapi.py
     ```

   - Access API at: <http://localhost:8001/docs>

4. Export data (if needed):

   ```bash
   python db_export.py
   ```

## Logging

- Log files are stored in `logs/` directory
- Naming format: `{service}_{date}.log`
- Maximum file size: 1MB
- Keeps 5 backup files
- Log levels: INFO, WARNING, ERROR

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Submit pull request

## License

This project is licensed under the MIT License.
