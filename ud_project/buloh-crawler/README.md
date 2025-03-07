
# Buloh Crawler Agent

## Overview

The Automated Video and News Crawler is a powerful tool designed to fetch trending content from TikTok and aggregate top news stories from various sources. It includes functionality to manage **live TikTok recordings**, allowing users to record and process live streams in real time. The system also retrieves TikTok videos using keyword or username searches. All collected data, including videos, audio, metadata, and comments, is processed and stored in unstructured formats across multiple databases for efficient analysis. Video and audio files are stored in Azure Blob Storage, while metadata and comments are saved in MongoDB.

## Key Features
- **Live TikTok Recording**: Record live TikTok streams for real-time processing and storage.
- **TikTok Crawling**: Automatically searches for videos using keywords or usernames and retrieves metadata, comments, and other relevant details.
- **News Crawling**: Fetches trending and top news articles from various sources.
- **Data Storage**: Videos and audio files are stored in Azure Blob Storage; metadata and comments are stored in MongoDB for efficient retrieval and processing.
- **API Access**: User-friendly APIs for starting, stopping, and managing the crawling and recording processes.
- **Scalable Architecture**: Supports multiple user IDs and usernames simultaneously.
- **Customizable Settings**: Allows users to define save intervals and crawling parameters.

## Installation
1. Clone the repository:
    ```bash
    git clone <repository-url>
    ```
2. Navigate to the project directory:
    ```bash
    cd buloh-crawler
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Prerequisites

- Python 3.10 or later
- Azure Blob Storage account and credentials
- MongoDB database server and credentials
- API Key for Rapids TikTok API and news API

## Usage

### Run

1. Start the application:
    ```bash
    python main.py
    ```

2. Access the API documentation (e.g., Swagger UI) at http://localhost:<port>/docs. port: 8000

#### API Endpoints

- Start TikTok Recording:
`POST /live/crawl/tiktok/video/start`
Parameters: `username, user_id, save_interval`

- Stop TikTok Recording:
`POST /live/crawl/tiktok/video/stop`
Parameters: `username, user_id`

- Start General Crawling:
`POST /crawl/start`
Request Body:

```json
{
    "tags": [{"type": "string", "value": "string"}],
    "perspective": "string",
    "fromDate": "string",
    "toDate": "string",
    "tiktok": true,
    "news": true
}
```

### Project Structure

```
./
├── crawlers/
│   ├── __init__.py
│   ├── base.py
│   ├── comment.py
│   ├── keyword_video.py
│   ├── news.py
│   ├── profile.py
│   ├── reply.py
│   ├── trending_video.py
│   ├── url_video.py
│   └── user_video.py
│
├── data/
│   ├── keywords.txt
│   ├── usernames.txt
│   └── watchlist.txt
│
├── db/
│   │
│   ├── __init__.py
│   └── connection.py
│
├── logs/
│   ├── app.log
│   └── app.log.2024-11-25
│
├── routes/
│   ├── keyword_video.py
│   ├── url_video.py
│   └── user_video.py
│
├── src/
│   │
│   ├── __pycache__/
│   │   ├── http_client.cpython-310.pyc
│   │   ├── tiktok_live_recorder.cpython-310.pyc
│   │   └── utils.cpython-310.pyc
│   │
│   ├── modules/
│   │   │
│   │   ├── __pycache__/
│   │   │   ├── live_recorder.cpython-310.pyc
│   │   │   ├── live_video_crawler.cpython-310.pyc
│   │   │   └── video_crawler.cpython-310.pyc
│   │   │
│   │   ├── live_video_crawler.py
│   │   └── video_crawler.py
│   │
│   ├── cookies.json
│   ├── http_client.py
│   ├── tiktok_live_recorder.py
│   └── utils.py
│
├── tests/
│   │
│   ├── cassettes/
│   │   │
│   │   ├── test_fetch_comments/
│   │   │   └── test_fetch_comments.yaml
│   │   │
│   │   ├── test_fetch_replies/
│   │   │   └── test_fetch_replies.yaml
│   │   │
│   │   ├── test_send_api_request/
│   │   │   └── test_send_api_request.yaml
│   │   │
│   │   └── test_trending_fetch_videos/
│   │       └── test_trending_fetch_videos.yaml
│   │
│   │
│   ├── __init__.py
│   ├── test_fetch_comments.py
│   ├── test_fetch_replies.py
│   ├── test_main.py
│   ├── test_send_api_request.py
│   ├── test_trending_fetch_videos.py
│   └── test_utils.py
│
├── utils/
│   │
│   ├── __pycache__/
│   │   ├── __init__.cpython-310.pyc
│   │   ├── exceptions.cpython-310.pyc
│   │   ├── helpers.cpython-310.pyc
│   │   └── logger.cpython-310.pyc
│   │
│   ├── __init__.py
│   ├── exceptions.py
│   ├── helpers.py
│   └── logger.py
│
├── .dockerignore
├── .env
├── .gitignore
├── .pre-commit-config.yaml
├── API_test.ipynb
├── API_test2.ipynb
├── CHANGELOG.md
├── Dockerfile
├── README.md
├── __init__.py
├── azure-aks.yml
├── docker-compose.yaml
├── main.py
├── requirements.txt
├── run.py
├── run_bulk.py
├── scheduler.py
├── tasks.py
├── usage.py
└── vers.py
```

## Key Success Factors

- Efficient and scalable architecture that supports concurrent requests.
- Secure data storage in Azure Blob Storage and MongoDB.
- Intuitive and user-friendly API interface for easy integration.

## Development and Contribution

- Tiktok Crawler System Design

<img src="https://i.ibb.co/27n9JBf/Screenshot-2024-12-12-at-4-13-34-PM.png" width="320"/>


### Setting Up a Development Environment

To set up the project for development, first install the necessary dependencies and activate your virtual environment.

```bash
pip install -r requirements.txt
```

Run the FastAPI server locally for development.

```bash
uvicorn main:app --reload
```

### Testing

To run the test suite, use the following command:

```bash
pytest
```

Tests are stored in the `tests/` directory and cover unit tests for each module and API endpoint.

### Contribution Guidelines

1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/my-new-feature`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature/my-new-feature`).
5. Create a new Pull Request.
