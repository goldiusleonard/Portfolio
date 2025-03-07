"""Module to test generate keyword trends API."""

import sys
from datetime import datetime
from pathlib import Path

import pytz

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
import unittest
from unittest.mock import MagicMock, patch

import pandas as pd

from functions.wordcloud_process import (
    process_wordcloud,
)


class TestProcessWordCloud(unittest.TestCase):
    """Run test."""

    @patch("functions.wordcloud_process.push_tables")
    @patch("functions.wordcloud_process.get_wordcloud")
    @patch("functions.wordcloud_process.check_datetime")
    @patch("functions.wordcloud_process.get_azure_session")
    @patch("functions.wordcloud_process.get_azure_engine")
    @patch("functions.wordcloud_process.get_credentials")
    @patch("os.getenv")
    def test_process_wordcloud(
        self,
        mock_getenv: MagicMock,
        mock_get_credentials: MagicMock,
        mock_get_engine: MagicMock,
        mock_get_session: MagicMock,
        mock_check_datetime: MagicMock,
        mock_get_wordcloud: MagicMock,
        mock_push_tables: MagicMock,
    ) -> None:
        """Run test."""
        # Mock environment variable
        mock_getenv.return_value = "test_db"

        # Mock database credentials
        mock_get_credentials.return_value = ("user", "pass", "host", 1234)

        # Mock session and engine
        mock_get_engine.return_value = MagicMock()
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock check_datetime
        kuala_lumpur_tz = pytz.timezone("Asia/Kuala_Lumpur")
        mock_check_datetime.return_value = (
            False,
            datetime(2024, 1, 1, 14, 18, 21, tzinfo=kuala_lumpur_tz),
        )

        # Mock unique categories
        mock_session.query.return_value.distinct.return_value.all.return_value = [
            ("category1",),
            ("category2",),
        ]

        # Mock SQL query results
        mock_query = MagicMock()
        mock_query.statement = (
            "SELECT * FROM content_model WHERE category = 'category1'"
        )
        mock_session.query.return_value.filter.return_value = mock_query
        pd.read_sql = MagicMock(
            side_effect=[
                pd.DataFrame(
                    {
                        "ss_process_timestamp": [
                            datetime(2025, 1, 17, 14, 18, 21, tzinfo=kuala_lumpur_tz),
                        ],
                        "content": ["sample content"],
                    },
                ),
                pd.DataFrame(
                    {
                        "ss_process_timestamp": [
                            datetime(2025, 1, 17, 14, 18, 21, tzinfo=kuala_lumpur_tz),
                        ],
                        "content": ["another content"],
                    },
                ),
            ],
        )

        # Mock wordcloud processing
        mock_get_wordcloud.side_effect = [
            pd.DataFrame({"word": ["test1"], "count": [10], "category": ["category1"]}),
            pd.DataFrame({"word": ["test2"], "count": [20], "category": ["category2"]}),
        ]

        # Call the function
        result = process_wordcloud()

        # Assertions
        self.assertEqual(result, {"message": "Data processed."})
        mock_push_tables.assert_called_once()
        mock_session.close.assert_called()


if __name__ == "__main__":
    unittest.main()
