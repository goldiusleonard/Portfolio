
# Comment Risk Status Agent

---

## Overview

This agent utilizes the LLaMA 3.1 model to generate risk status based on comment. 

---

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Installation Process](#installation-process)
- [Software Dependencies](#software-dependencies)
- [Latest Releases](#latest-releases)
- [API References](#api-references)
- [Build and Test](#build-and-test)
- [Version](#version)
- [Developer](#developer)

---

## Introduction

The **Comment Risk Status Agent** is designed to analyze comment to generate:
- **Risk Status**: Assessments of risk levels based on the analyzed content.

---

## Getting Started

This section will guide you through setting up the agent on your local machine.

### Installation Process

1. Clone the repository:
   ```bash
   git clone https://dev.azure.com/userdata-ada/marketplace/_git/marketplace -b koohrang_commentrisk
   cd marketplace
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv .venv
   ```
   - For Windows, activate it using:
     ```bash
     .venv\Scripts\activate
     ```
   - For macOS/Linux, activate it using:
     ```bash
     source .venv/bin/activate
     ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Software Dependencies

The following dependencies are required for running the agent:

- Python 3.11.5 or higher
- LLaMA 3.1 model (integrated via the OpenAI API)
- FastAPI (for API-based functionalities)
- Logging (for progress tracking and debugging)

Ensure all dependencies are installed via the `requirements.txt` file.

---

## Latest Releases

Check the **Releases** section in the Azure DevOps repository for the latest version and feature updates.

- [Releases Section](https://dev.azure.com/userdata-ada/marketplace/_git/marketplace)

---

## API References

The agent leverages the LLaMA 3.1 OpenAI API for processing video descriptions. It provides:

- **Risk Level Assessment**: Assigns risk categories (e.g., high, medium, low, no risk) based on contextual analysis.

### API Input/Output

- **Input**: Video Summary and Comment in plain text format.
- **Output**: JSON objects containing risk level data.

---

## Build and Test

Follow these steps to run and test the agent:

1. Run the application:
   ```bash
   python api.py
   ```

2. Use FastAPI's interactive API documentation to test endpoints:
   - Navigate to `http://localhost:8002/docs` in your browser.
   - Test the sentiment and risk status analysis endpoints.

3. Run unit tests to validate functionality:
   ```bash
   pytest tests/
   ```

---

## Version

### Current Version: 1.0.0

- Initial release of the Comment Risk Status Agent.
- Key Features:
  - Risk level analysis.
  - FastAPI integration.
  - Enhanced logging for debugging.
  - Modularized code structure.

### Previous Versions

- None (this is the initial release).

---

## Developer

Developed by **Mohsen**.

For queries or contributions, contact the developer via the Azure DevOps repository or provide an appropriate contact mechanism here.
