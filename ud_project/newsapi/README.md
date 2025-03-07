# Putumayo-Agent

Putumayo-Agent is a robust API built with FastAPI for retrieving and filtering news articles using the powerful NewsAPI service. This API allows users to access relevant news articles based on parameters such as category, sub-category, topic, date range, and more. It also provides the ability to expand topics and filter articles based on specific criteria. The API can be used for building news aggregation, analysis, and recommendation applications.

## Features

- **News Retrieval:** Fetch news articles based on category, sub-category, and topic.
- **Flexible Query Options:** Filter by date range and specify the maximum number of news articles to retrieve.
- **Topic Expansion:** Expand topics dynamically to retrieve related news content.
- **News Filtering:** Filter articles based on relevance to the given topic.
- **Cross-Origin Support:** Supports cross-origin requests for seamless integration with other web applications.

## Requirements

- Python 3.7+
- FastAPI
- Uvicorn (for development server)
- dotenv (for environment variables)
- EventRegistry (for interacting with the NewsAPI)
- MongoDB (for storing filtered news articles)

## Installation

1. Clone this repository:

```bash
git clone https://userdata-ada@dev.azure.com/userdata-ada/newsapi/_git/newsapi
cd putumayo-agent
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

Create a .env file in the root directory of the project and add your NewsAPI key:

```bash
NEWS_API_KEY=your_newsapi_key
```

## Running the Application

To run the API locally, use the following command:

```bash
python main.py
```

The application will start on http://localhost:8000.

## API Endpoints

### /news

Retrieve filtered news articles.

#### Query Parameters:

- category (string, required): The category to filter news by.
- sub_category (string, optional): The sub-category to filter news by.
- topic (string, optional): The AI topic to filter news by.
- max_news (integer, optional, default: 100): The maximum number of news articles to retrieve.
- start_date (string, optional, format: 'YYYY-MM-DD'): The start date for filtering news.
- end_date (string, optional, format: 'YYYY-MM-DD'): The end date for filtering news.

#### Response:

The response will contain a list of news articles filtered based on the provided query parameters.

Example:

```json
[
  {
    "title": "Breaking News: Tech Industry Insights",
    "url": "https://example.com/article1",
    "published_date": "2024-12-18T12:34:56",
    "source": "TechNews",
    "content": "Full content of the article..."
  },
  ...
]
```

#### Error Handling

404: If no news articles are found.
500: If an unexpected error occurs during the news retrieval process.

#### Notes

The NEWS_API_KEY is required to authenticate the requests. Make sure to generate and add your API key from NewsAPI.
MongoDB is used to save the filtered articles, ensuring persistence for future use and analysis.