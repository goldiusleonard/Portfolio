
# Yankechil API
=====================================

## Overview
------------

The **Yankechil API** is an orchestration tool designed to execute multiple APIs in a defined sequence. It retrieves input data from a database, determines the appropriate APIs to invoke, collects their results, and stores the processed data in a final database table. This API automates workflows by managing API calls, ensuring proper sequencing, and maintaining data integrity.

There are three pipeline endpoints: AI Agent Builder Pipeline, Direct Pipeline, and Agent Select.

   - AI Agent Builder Pipeline filters results based on user input, such as category, subcategory, risk levels, and post date.

	- Direct Pipeline is triggered automatically when new data is crawled and inserted into the input table.

	- Agent Select allows users to manually execute specific APIs from the existing set of available APIs.

## Table of Contents
-----------------

* [Introduction](#introduction)
* [Getting Started](#getting-started)
  * [Installation Process](#installation-process)
  * [Software Dependencies](#software-dependencies)
  * [Configuration](#configuration)
* [Build and Test](#build-and-test)
* [Version](#version)
* [Contribute](#contribute)

## Introduction
------------

The Manager API simplifies the management of workflows involving multiple APIs by orchestrating their execution in the correct sequence. It takes input data from a database, processes it through external APIs, and saves the combined output into a final database. This ensures consistency, reduces manual intervention, and increases efficiency.

## Getting Started
-----------------

This section will guide you through setting up and running the Manager API on your local machine or server.

📦 project-root
├── 📂 agents
│   ├── Agents.py
│   ├── AgentsProcess.py
│   ├── baseAgent.py
│   ├── register_agents.py
│
├── 📂 config
│   ├── config_num.py
│   ├── config_risk_samples.py
│
├── 📂 db
│   ├── db.py
│
├── 📂 manager
│   ├── manager.py
│
├── 📂 processing
│   ├── pipeline_direct.py
│   ├── pipeline_filter.py
│   ├── pipeline_select.py
│
├── 📂 schema
│   ├── input_schemas.py
│   ├── output_schemas.py
│
├── 📂 tests
│   ├── test_agents_process.py
│   ├── test_agents.py
│   ├── test_base_agent.py
│   ├── test_db.py
│   ├── test_manager.py
│   ├── test_register_agents.py
│
├── 📂 utils
│   ├── utils.py
│
├── .env
├── .gitignore
├── api.py
├── direct_app.py
├── filter_app.py
├── direct_batch_app.py
├── filter_batch_app.py
├── log_mongo.py
├── select_app.py
├── README.md

### Installation Process
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```
2. Set up a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # For Linux/Mac
   source .venv\Scripts\activate      # For Windows
   ```
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Software Dependencies
* **Python 3.11.6 or higher**
* **FastAPI** for the API framework
* **SQLAlchemy** for database interactions
* **Requests** library for API calls
* **Pandas** for data processing and manipulation
* Database: **MySQL**
* **APIs**:
  - **Category API**
  - **Summary API**
  - **Sentiment API**
  - **Justification API**
  - **Law API**

### Database Dependencies
The project depends on the following input tables:
- **unbiased_data**: Contains raw unbiased data for processing.
- **category**: Holds the main categories.
- **subcategory**: Contains subcategory mappings.
- **comments**: Stores user comments.
- **preproceed_crawl_data**: Contains preprocessed data from crawled sources.

The output data is stored in the following tables:

AI agnet builder:
   - **analysis_table_output**: Stores analysis results.
   - **comments_table_output**: Contains processed comments data.
   - **mapped_table_output**: Stores mapped data results.
Direct:
   - **postproceed_crawl_data_table_output**: Contains post-processed crawled data.

### Configuration
1. Set up a `.env` file with the following parameters:
   ```plaintext
   api_ip=''
   # api_ip='localhost'
   port_manager='8001'

   table_name_input_1 = 'preprocessed_unbiased'
   table_name_input_2 = "comments_cat_subcat"
   table_name_input_3 = "mapped_cat_sub"
   table_name_input_4 = 'category'
   table_name_input_5 = 'sub_category'
   table_name_input_6 = 'preprocessed_crawled_data'

   table_name_output_1 = "analysis_output"
   table_name_output_2 = "mapped_output"
   table_name_output_3 = "comments_output"
   table_name_output_4 = "direct_output"

   justification_app_url = ""
   comment_risk_app_url = ""
   summary_app_url = ""
   category_app_url = ""
   law_regulated_app_url = ""
   law_regulated_direct_app_url = ""
   sentiment_app_url = ""

   mysql_host=""
   mysql_user=""
   mysql_password=""
   mysql_port=3306
   mysql_database=""
   output_mysql_database=""

   mongo_host=""
   mongo_user=""
   mongo_password=""
   mongo_port=""
   mongo_db = ""
   mongo_collection_name = ""

   redis_host = ""  
   redis_port = "" 
   redis_db = 0       
   redis_password = ""
   ```

## Build and Test
----------------

### Building the Application
1. Ensure all dependencies are installed.
2. Start the application:
   ```bash
   1- python api.py
   2- celery -A api.celery_app worker --loglevel=info -Q default
   ```

### Running Tests
1. Install test dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run unit tests:
   ```bash
   pytest tests/
   ```


## Version
---------

### Current Version: 1.0.0
* Initial release:
  - API orchestration logic
  - Database integration for input and output
  - Detailed logging and error handling
  - Unit tests for core features

## Contribute
-------------

We welcome contributions from the community! To contribute:
1. Fork the repository and create a new branch:
   ```bash
   git checkout -b feature-name
   ```
2. Make your changes and commit them:
   ```bash
   git commit -m "Description of changes"
   ```
3. Push your branch and create a pull request:
   ```bash
   git push origin feature-name
   ```

Follow the `CONTRIBUTING.md` file for detailed guidelines.

---

Developed by Mohsen.  
