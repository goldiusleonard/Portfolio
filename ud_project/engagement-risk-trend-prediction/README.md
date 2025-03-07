# Engagement and Risk Trend Prediction API

This FastAPI-based API provides engagement and risk predictions for video content. It leverages the Prophet model for time series forecasting to predict metrics like total videos, likes, shares, views, and comments for different groups (e.g., users or categories) over a specified date range.

## Features

- **Prediction of Engagement Metrics**: Predict total likes, shares, views, comments, or videos for a given group (e.g., user handle, sub-category).
- **Time Series Forecasting**: Utilizes Prophet for accurate predictions based on historical video engagement data.
- **Flexible User Selection**: Allows selection of the group (e.g., 'user_handle') to generate predictions for.
- **Date Range Filtering**: Filter predictions based on a custom date range.
- **Customizable Prediction Types**: Predict various metrics (likes, shares, videos, etc.) using predefined prediction types.

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/engagement-risk-prediction-api.git
    cd engagement-risk-prediction-api
    ```

2. **Create a virtual environment** (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate   # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    Ensure that the following environment variables are configured in your `.env` file:
    - `DATA_ASSET_TABLE`: The name of the Azure data asset table containing the video data.
    - `NUM_OF_DAYS_TRAIN_DATA`: The number of days of historical data to fetch for training.
    
    Example `.env`:
    ```env
    DATA_ASSET_TABLE=video_engagement_data
    NUM_OF_DAYS_TRAIN_DATA=30
    ```

## Usage

1. **Start the FastAPI server**:
    ```bash
    uvicorn main:app --reload
    ```

2. **Access the API documentation**:
    Once the server is running, you can access the interactive Swagger UI at:
    ```
    http://127.0.0.1:8000/docs
    ```

    Alternatively, you can use the ReDoc documentation at:
    ```
    http://127.0.0.1:8000/redoc
    ```

## API Endpoints

### `GET /predict/trend`

Fetch predictions for a given user selection and date range.

#### Query Parameters:
- `user_selection` (str, required): The group to aggregate by (e.g., `user_handle`, `sub_category`).
- `start_date` (str, required): The start date for the prediction in `YYYY-MM-DD` format.
- `end_date` (str, required): The end date for the prediction in `YYYY-MM-DD` format.
- `prediction_type` (str, required): The type of prediction to make. Possible values:
  - `predict_total_videos`
  - `predict_total_likes`
  - `predict_total_shares`
  - `predict_total_views`
  - `predict_total_comments`
- `user_handle` (str, optional): Filter by a specific user handle (e.g., `user1`).

#### Example Request:
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/Trend?user_selection=sub_category&start_date=2025-01-01&end_date=2025-01-03&prediction_type=predict_total_likes' \
  -H 'accept: application/json'
```

#### Example Response:
```json
[
  {
    "Date": "2025-01-01",
    "Predicted Value": 150,
    "sub_category": "fitness"
  },
  {
    "Date": "2025-01-02",
    "Predicted Value": 160,
    "sub_category": "fitness"
  },
  {
    "Date": "2025-01-03",
    "Predicted Value": 170,
    "sub_category": "fitness"
  }
]
```

## Testing

Run tests with pytest:

```bash
pytest
```

The repository includes unit tests for the API endpoints, prediction logic, and various edge cases such as invalid dates or missing query parameters.

## Error Handling

- **400 Bad Request**: Invalid parameters or date format errors.
- **404 Not Found**: Endpoint not found.
- **500 Internal Server Error**: Unexpected errors in processing.

## Development

1. Fork the repository.
2. Create a feature branch.
3. Install dependencies and run the FastAPI app locally for testing.
4. Submit a pull request.