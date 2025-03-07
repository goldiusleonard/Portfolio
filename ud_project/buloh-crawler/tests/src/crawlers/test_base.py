import pytest
from unittest.mock import patch, MagicMock

from src.crawlers.base import VideoCrawler  # Replace with actual import path


class TestVideoCrawler:
    @pytest.fixture
    def video_crawler(self):
        """Create a concrete implementation of VideoCrawler for testing"""

        class TestableVideoCrawler(VideoCrawler):
            def crawl(self, *args, **kwargs):
                # Implement a minimal concrete method for abstract base class
                pass

        return TestableVideoCrawler()

    def test_choose_querystring_username(self, video_crawler):
        """Test _choose_querystring method for username type"""
        kwargs = {
            "type": "username",
            "username": "testuser",
            "video_count": 10,
            "cursor": "0",
        }
        querystring = video_crawler._choose_querystring(**kwargs)

        assert querystring == {"unique_id": "testuser", "count": 10, "cursor": "0"}

    def test_choose_querystring_keyword(self, video_crawler):
        """Test _choose_querystring method for keyword type"""
        kwargs = {
            "type": "keyword",
            "keyword": "test",
            "region": "US",
            "count": 20,
            "cursor": "0",
        }
        querystring = video_crawler._choose_querystring(**kwargs)

        assert querystring == {
            "keywords": "test",
            "region": "US",
            "count": 20,
            "cursor": "0",
            "publish_time": "180",
            "sort_type": "0",
        }

    def test_choose_querystring_trending(self, video_crawler):
        """Test _choose_querystring method for trending type"""
        kwargs = {"type": "trending", "region": "US", "count": 30}
        querystring = video_crawler._choose_querystring(**kwargs)

        assert querystring == {"region": "US", "count": 30}

    def test_choose_querystring_invalid_type(self, video_crawler):
        """Test _choose_querystring method with invalid type"""
        kwargs = {"type": "invalid_type"}
        querystring = video_crawler._choose_querystring(**kwargs)

        assert querystring == {
            "error": "Please choose a valid type. [username, keyword, trending]"
        }

    @patch("src.crawlers.base.send_api_request")  # Replace with actual import path
    def test_fetch_videos_trending(self, mock_send_api_request, video_crawler):
        """Test fetch_videos method for trending type"""
        # Mock API response
        mock_response = {"data": {"videos": [{"id": "1", "region": "MY"}]}}
        mock_send_api_request.return_value = mock_response

        # Prepare kwargs
        kwargs = {"type": "trending", "region": "US", "count": 10}

        # Call method
        with patch("time.sleep", return_value=None):
            result = video_crawler.fetch_videos("test_url", **kwargs)

        # Assertions
        assert len(result) == 1
        assert result == mock_response["data"]
        mock_send_api_request.assert_called_once()

    @patch("src.crawlers.base.send_api_request")  # Replace with actual import path
    def test_fetch_videos_error_response(self, mock_send_api_request, video_crawler):
        """Test fetch_videos method with error in API response"""
        # Mock API response with error
        mock_response = {"error": "Test error message"}
        mock_send_api_request.return_value = mock_response

        # Prepare kwargs
        kwargs = {
            "type": "username",
            "username": "testuser",
            "video_count": 10,
            "cursor": "0",
        }

        # Call method
        with patch("time.sleep", return_value=None), patch("builtins.print"), patch(
            "src.crawlers.base.log.info"
        ):
            result = video_crawler.fetch_videos("test_url", **kwargs)

        # Assertions
        assert result == []
        mock_send_api_request.assert_called_once()

    @patch("src.crawlers.base.send_api_request")  # Replace with actual import path
    def test_fetch_more_videos(self, mock_send_api_request, video_crawler):
        """Test _fetch_more_videos method"""
        # Initial response
        initial_response = {
            "data": {
                "hasMore": True,
                "cursor": "initial_cursor",
                "videos": [{"id": "1", "region": "MY"}],
            }
        }

        # Second response
        second_response = {
            "msg": "success",
            "data": {
                "hasMore": False,
                "cursor": "final_cursor",
                "videos": [{"id": "2", "region": "MY"}],
            },
        }

        # Mocking API responses
        mock_send_api_request.side_effect = [second_response]

        # Call the method
        with patch("time.sleep", return_value=None):  # Skip sleep for testing
            result = video_crawler._fetch_more_videos(
                response=initial_response,
                url="test_url",
                querystring={"cursor": "initial_cursor"},
                tmp_video_list=[{"id": "1", "region": "MY"}],
            )

        # Assertions
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"
        mock_send_api_request.assert_called_once()

    @patch("src.crawlers.base.MongoDBClient")  # Replace with actual import path
    @patch("src.crawlers.base.helpers.download_file")  # Replace with actual import path
    def test_save_videos_to_db(
        self, mock_download_file, mock_mongodb_client, video_crawler
    ):
        """Test save_videos_to_db method"""
        # Mock MongoDB client and its methods
        mock_db = MagicMock()
        mock_mongodb_client.return_value.__enter__.return_value = mock_db
        mock_db["video"].find_one.return_value = None  # No existing video

        # Mock file download and upload
        mock_download_file.return_value = b"test_video_data"

        # Prepare video list
        video_list = [
            {
                "id": "test_video_id",
                "video_id": "test_video_id",
                "region": "MY",
                "play": "video_url",
                "cover": "cover_url",
                "created_at": "2023-01-01 00:00:00",
            }
        ]

        # Call method
        with patch("builtins.print"), patch("src.crawlers.base.log.info"):
            video_crawler.save_videos_to_db(video_list, "test_type", 1)

        # Assertions
        mock_db["video"].insert_one.assert_called_once()
        mock_download_file.assert_called()

    def test_headers_initialization(self, video_crawler):
        """Test headers initialization"""
        assert "x-rapidapi-key" in video_crawler.headers
        assert "x-rapidapi-host" in video_crawler.headers
