import pytest
import os
import json
import pandas as pd

from unittest.mock import MagicMock, patch
from components.summarizer import summarize
from qdrant_client import QdrantClient
from components.datamodel import DataSummary
from vector_db_utils.table import get_table_info
from vector_db_utils.column import get_column_info_list_from_table
from components.sql_query import generate_sql_query
from components.executor import execute_sql_query
from modules.query_generator_executor import query_generator_executor
from logging_library.applogger.log_manager import LogManager
from fastapi import HTTPException
from dotenv import load_dotenv


def test_query_generator_executor_valid():
    """Test SQL query generation and execution, ensuring correct handling of user intent and expected outputs."""
    load_dotenv()

    with patch("modules.query_generator_executor.summarize") as mock_summarize, patch(
        "modules.query_generator_executor.generate_sql_query"
    ) as mock_generate_sql, patch(
        "modules.query_generator_executor.execute_sql_query"
    ) as mock_execute_sql, patch(
        "modules.query_generator_executor.postprocess_chart_data"
    ) as mock_postprocess:
        mock_summarize.return_value = MagicMock()
        mock_generate_sql.return_value = "SELECT * FROM test_table;"
        mock_execute_sql.return_value = {
            "main_chart_sql": "SELECT * FROM test_table;",
            "chart_data": {"key": "value"},
        }
        mock_postprocess.return_value = {
            "main_chart_sql": "SELECT * FROM test_table;",
            "chart_data": pd.DataFrame({"key": ["value"]}),
        }

        user_intent = "Show me CASA penetration rate"
        database_name = "test_db"
        table_name = "test_table"
        db_tag = "label5"
        session_id = "46ddfcdb-e8a1-4733-b89f-0660c8854ec9"

        response = query_generator_executor(
            user_intent,
            database_name,
            table_name,
            db_tag,
            session_id,
        )

        assert "Chart_Query" in response
        assert "data" in response
        assert isinstance(response["data"], list)

        mock_summarize.assert_called_once()
        mock_generate_sql.assert_called_once()
        mock_execute_sql.assert_called_once()
        mock_postprocess.assert_called_once()

        assert response["Chart_Query"] == "SELECT * FROM test_table;"
        assert response["data"] == [{"key": "value"}]


def test_query_generator_executor_invalid_input():
    """Test the handling of invalid input types for general SQL query generator and extarctor."""
    load_dotenv()

    with patch("modules.query_generator_executor.summarize") as _, patch(
        "modules.query_generator_executor.generate_sql_query"
    ) as _, patch("modules.query_generator_executor.execute_sql_query") as _, patch(
        "modules.query_generator_executor.postprocess_chart_data"
    ) as _:
        with pytest.raises(HTTPException):
            query_generator_executor(
                1234,
                "test_db",
                "test_table",
                "test_db_tag",
                "161a3eb9-bd2e-40c1-9ad3-c35159113b37",
            )

        with pytest.raises(HTTPException):
            query_generator_executor(
                "Show me the data",
                1234,
                "test_table",
                "test_db_tag",
                "161a3eb9-bd2e-40c1-9ad3-c35159113b37",
            )

        with pytest.raises(HTTPException):
            query_generator_executor(
                "Show me the data",
                "test_db",
                1234,
                "test_db_tag",
                "161a3eb9-bd2e-40c1-9ad3-c35159113b37",
            )

        with pytest.raises(HTTPException):
            query_generator_executor(
                "Show me the data",
                "test_db",
                "test_table",
                1234,
                "161a3eb9-bd2e-40c1-9ad3-c35159113b37",
            )


@pytest.fixture
def mock_qdrant_client():
    """Fixture to mock QdrantClient"""
    load_dotenv()

    mock_client = MagicMock(QdrantClient)
    mock_client.get_collection.return_value = MagicMock(points_count=10)
    mock_client.scroll.return_value = ([{"metadata": {"test_key": "test_value"}}], None)
    return mock_client


@pytest.fixture
def patch_summarizer_functions():
    """Fixture to patch external functions used inside summarize"""
    load_dotenv()

    with patch("components.summarizer.get_table_info") as mock_get_table_info, patch(
        "components.summarizer.get_column_info_list_from_table"
    ) as mock_get_column_info_list_from_table, patch(
        "components.summarizer.get_column_name_list"
    ) as mock_get_column_name_list, patch(
        "components.summarizer.get_n_unique_value_dict"
    ) as mock_get_n_unique_value_dict, patch(
        "components.summarizer.generate_table_schema"
    ) as mock_generate_table_schema, patch(
        "components.summarizer.get_sql_library"
    ) as mock_get_sql_library, patch(
        "components.summarizer.get_column_data_tribes"
    ) as mock_get_column_data_tribes, patch(
        "components.summarizer.get_column_sql_data_types"
    ) as mock_get_column_sql_data_types:
        # Mock return values
        mock_get_table_info.return_value = {
            "metadata": {"database_identifier": "test_db_tag"}
        }
        mock_get_column_info_list_from_table.return_value = [
            {"name": "column1", "metadata": {"description": "Column 1 description"}}
        ]
        mock_get_column_name_list.return_value = ["column1"]
        mock_get_n_unique_value_dict.return_value = {"column1": 10}
        mock_generate_table_schema.return_value = (
            "CREATE TABLE test_table;",
            "test_table_description",
            {"column1": "Column 1 description"},
            {"column1": ["value1", "value2"]},
            {"column1": "Column 1 Display Name"},
        )
        mock_get_sql_library.return_value = "MySQL"
        mock_get_column_data_tribes.return_value = {"column1": "tribe1"}
        mock_get_column_sql_data_types.return_value = {"column1": "INTEGER"}

        yield {
            "mock_get_table_info": mock_get_table_info,
            "mock_get_column_info_list_from_table": mock_get_column_info_list_from_table,
            "mock_get_column_name_list": mock_get_column_name_list,
            "mock_get_n_unique_value_dict": mock_get_n_unique_value_dict,
            "mock_generate_table_schema": mock_generate_table_schema,
            "mock_get_sql_library": mock_get_sql_library,
            "mock_get_column_data_tribes": mock_get_column_data_tribes,
            "mock_get_column_sql_data_types": mock_get_column_sql_data_types,
        }


def test_summarize_valid(mock_qdrant_client, patch_summarizer_functions):
    """Test summarize function when everything works as expected"""
    load_dotenv()

    os.environ["CLIENT_DB"] = json.dumps(
        [{"db_tag": "test_db_tag", "database_type": "MySQL"}]
    )

    result = summarize(
        qdrant_client=mock_qdrant_client,
        database_name="test_db",
        database_identifier="test_db_tag",
        table_collection="test_table_collection",
        column_collection="test_column_collection",
        table_name="test_table",
        embedding_model_url="http://mock_embedding_url",
        logging_url="http://mock_logging_url",
        session_id="161a3eb9-bd2e-40c1-9ad3-c35159113b37",
        code_level_logger=LogManager(
            "161a3eb9-bd2e-40c1-9ad3-c35159113b37"
        ).get_logger_by_name(os.getenv("CODE_LEVEL_LOGGER_NAME")),
    )

    assert isinstance(result, DataSummary)
    assert result.database_schema_sql == "CREATE TABLE test_table;"
    assert result.table_description == "test_table_description"
    assert result.column_description_dict == {"column1": "Column 1 description"}
    assert result.column_sample_dict == {"column1": ["value1", "value2"]}
    assert result.sql_library == "MySQL"
    assert result.database_properties == {
        "db_tag": "test_db_tag",
        "database_type": "MySQL",
    }
    assert result.column_name_list == ["column1"]
    assert result.column_display_name_dict == {"column1": "Column 1 Display Name"}
    assert result.column_data_tribes == {"column1": "tribe1"}
    assert result.column_n_unique_value_dict == {"column1": 10}
    assert result.column_sql_data_types == {"column1": "INTEGER"}
    assert result.table_join_sql_query == ""


def test_summarize_no_metadata(mock_qdrant_client, patch_summarizer_functions):
    """Test summarize function when 'metadata' is missing in table_info"""
    load_dotenv()

    patch_summarizer_functions["mock_get_table_info"].return_value = {}

    with pytest.raises(KeyError, match="'metadata'"):
        summarize(
            qdrant_client=mock_qdrant_client,
            database_name="test_db",
            database_identifier="test_db_tag",
            table_collection="test_table_collection",
            column_collection="test_column_collection",
            table_name="test_table",
            embedding_model_url="http://mock_embedding_url",
            logging_url="http://mock_logging_url",
            session_id="161a3eb9-bd2e-40c1-9ad3-c35159113b37",
            code_level_logger=LogManager(
                "161a3eb9-bd2e-40c1-9ad3-c35159113b37"
            ).get_logger_by_name(os.getenv("CODE_LEVEL_LOGGER_NAME")),
        )


def test_summarize_invalid_db_tag(mock_qdrant_client, patch_summarizer_functions):
    """Test summarize function when 'metadata' is missing in table_info"""
    load_dotenv()

    patch_summarizer_functions["mock_get_table_info"].return_value = {
        "metadata": {"database_identifier": "incorrect_db_tag"}
    }

    os.environ["CLIENT_DB"] = json.dumps(
        [{"db_tag": "correct_db_tag", "database_type": "MySQL"}]
    )

    with pytest.raises(RuntimeError, match="Database Properties is not found!"):
        summarize(
            qdrant_client=mock_qdrant_client,
            database_name="test_db",
            database_identifier="test_db_tag",
            table_collection="test_table_collection",
            column_collection="test_column_collection",
            table_name="test_table",
            embedding_model_url="http://mock_embedding_url",
            logging_url="http://mock_logging_url",
            session_id="161a3eb9-bd2e-40c1-9ad3-c35159113b37",
            code_level_logger=LogManager(
                "161a3eb9-bd2e-40c1-9ad3-c35159113b37"
            ).get_logger_by_name(os.getenv("CODE_LEVEL_LOGGER_NAME")),
        )


def test_summarize_no_vectors(mock_qdrant_client):
    """Test the get_table_info function when there are no points in the collection"""
    load_dotenv()

    mock_qdrant_client.get_collection.return_value = MagicMock(points_count=0)

    with pytest.raises(
        RuntimeError,
        match="Qdrant table collection test_collection has no points/vectors!",
    ):
        get_table_info(
            embedding_model_url="http://mock_embedding_url",
            qdrant_client=mock_qdrant_client,
            table_name="test_table",
            database_name="test_db",
            database_identifier="test_db_tag",
            collection_name="test_collection",
            code_level_logger=LogManager(
                "161a3eb9-bd2e-40c1-9ad3-c35159113b37"
            ).get_logger_by_name(os.getenv("CODE_LEVEL_LOGGER_NAME")),
        )

    with pytest.raises(
        RuntimeError,
        match="Qdrant column collection test_collection has no points/vectors!",
    ):
        get_column_info_list_from_table(
            embedding_model_url="http://mock_embedding_url",
            qdrant_client=mock_qdrant_client,
            table_name="test_table",
            table_id="table1",
            database_identifier="test_db_tag",
            collection_name="test_collection",
            code_level_logger=LogManager(
                "161a3eb9-bd2e-40c1-9ad3-c35159113b37"
            ).get_logger_by_name(os.getenv("CODE_LEVEL_LOGGER_NAME")),
        )


@pytest.fixture
def mock_data():
    """Fixture to provide mock clients, chart data, and configurations"""
    load_dotenv()
    mock_llama70b_client = MagicMock()
    mock_data_summary = MagicMock(spec=DataSummary, sql_library="mysql")

    chart_data = {
        "main_instruction": "Show me CASA Product penetration",
        "main_chart_type": "table_chart",
        "main_chart_axis": {"xAxis": "all", "yAxis": "all"},
        "chart_id": 1,
        "sub_questions": [],
    }

    chart_data_execute = {
        "main_instruction": "Show me CASA Product penetration",
        "main_chart_sql": "SELECT * FROM table_name",
        "sub_questions": [],
        "main_chart_axis": {"xAxis_column": "all", "yAxis_column": "all"},
        "chart_id": 1,
        "main_chart_type": "table_chart",
    }
    chart_data_execute["main_chart_sql"] = "SELECT * FROM table_name"
    chart_data_execute["main_chart_sql_raw"] = "SELECT * FROM table_name"

    filters = {}
    aggregations = []
    database_name = "test_db"
    table_name = "test_table"
    logging_url = "http://logging.url"
    session_id = "46ddfcdb-e8a1-4733-b89f-0660c8854ec9"

    return {
        "mock_llama70b_client": mock_llama70b_client,
        "mock_data_summary": mock_data_summary,
        "chart_data": chart_data,
        "filters": filters,
        "aggregations": aggregations,
        "database_name": database_name,
        "table_name": table_name,
        "logging_url": logging_url,
        "chart_data_execute": chart_data_execute,
        "session_id": session_id,
    }


@pytest.fixture
def mock_generate_sql(monkeypatch):
    """Fixture to mock the _generate_sql function."""
    load_dotenv()

    _generate_sql_mock = MagicMock(
        return_value=("SELECT * FROM test_table;", "SELECT * FROM test_table;")
    )
    monkeypatch.setattr("components.sql_query._generate_sql", _generate_sql_mock)
    return _generate_sql_mock


def test_generate_sql_query_valid(mock_data, mock_generate_sql):
    """Test successful SQL generation for the main chart."""
    load_dotenv()

    result = generate_sql_query(
        mock_data["mock_llama70b_client"],
        mock_data["mock_data_summary"],
        mock_data["chart_data"],
        mock_data["filters"],
        mock_data["aggregations"],
        mock_data["database_name"],
        mock_data["table_name"],
        mock_data["logging_url"],
        mock_data["session_id"],
        LogManager(mock_data["session_id"]).get_logger_by_name(
            os.getenv("CODE_LEVEL_LOGGER_NAME")
        ),
    )

    assert "main_chart_sql" in result
    assert result["main_chart_sql"] == "SELECT * FROM test_table;"
    assert "main_chart_sql_raw" in result
    assert result["main_chart_sql_raw"] == "SELECT * FROM test_table;"


def test_generate_sql_query_missing_fields(mock_data, mock_generate_sql):
    """Test for missing question and instruction (for main chart)."""
    load_dotenv()

    chart_data_missing = {
        "main_chart_type": "table_chart",
        "main_chart_axis": {},
        "chart_id": 1,
        "sub_questions": [],
    }

    with pytest.raises(RuntimeError, match="Question and Instruction is empty!"):
        generate_sql_query(
            mock_data["mock_llama70b_client"],
            mock_data["mock_data_summary"],
            chart_data_missing,
            mock_data["filters"],
            mock_data["aggregations"],
            mock_data["database_name"],
            mock_data["table_name"],
            mock_data["logging_url"],
            mock_data["session_id"],
            LogManager(mock_data["session_id"]).get_logger_by_name(
                os.getenv("CODE_LEVEL_LOGGER_NAME")
            ),
        )


def test_generate_sql_query_fail(mock_data, monkeypatch, capsys):
    """Test the case where SQL generation fails."""
    load_dotenv()

    _generate_sql_mock_fail = MagicMock(side_effect=Exception("SQL generation error"))
    monkeypatch.setattr("components.sql_query._generate_sql", _generate_sql_mock_fail)

    try:
        generate_sql_query(
            mock_data["mock_llama70b_client"],
            mock_data["mock_data_summary"],
            mock_data["chart_data"],
            mock_data["filters"],
            mock_data["aggregations"],
            mock_data["database_name"],
            mock_data["table_name"],
            mock_data["logging_url"],
            mock_data["session_id"],
            LogManager(mock_data["session_id"]).get_logger_by_name(
                os.getenv("CODE_LEVEL_LOGGER_NAME")
            ),
        )
    except Exception:
        pass

    error_message = capsys.readouterr()

    assert "Traceback" in error_message.out
    assert "SQL generation error" in error_message.out


mock_return_data_execute_sql = {
    "main_instruction": "Show me CASA Product penetration",
    "main_chart_sql": "SELECT * FROM table_name",
    "sub_questions": [],
    "main_chart_axis": {"xAxis_column": "all", "yAxis_column": "all"},
    "chart_id": 1,
    "main_chart_type": "table_chart",
    "main_chart_sql_raw": "SELECT * FROM table_name",
    "chart_data": MagicMock(),
}


def test_execute_sql_query_valid(mock_data):
    """Test the execution of an SQL query with valid data"""
    load_dotenv()

    processed_data_mock = MagicMock()
    processed_data_mock.empty = False

    def mock_exec(code, local_vars):
        local_vars["processed_data"] = processed_data_mock
        local_vars["chart_data"] = mock_return_data_execute_sql["chart_data"]

    with patch(
        "components.executor.mysql.execute_mysql_mariadb",
        return_value=mock_return_data_execute_sql,
    ), patch(
        "components.executor.template.code_executor_template",
        {"mysql": "dummy_code_template"},
    ), patch("builtins.exec", side_effect=mock_exec):
        result = execute_sql_query(
            llama70b_client=mock_data["mock_llama70b_client"],
            data_summary=mock_data["mock_data_summary"],
            filters=mock_data["filters"],
            aggregations=mock_data["aggregations"],
            database_name=mock_data["database_name"],
            table_name=mock_data["table_name"],
            chart_query=mock_data["chart_data_execute"],
            sql_library="mysql",
            database_properties={
                "hostname": "localhost",
                "username": "root",
                "password": "password",
                "port": 3306,
            },
            chart_axis={},
            logging_url=mock_data["logging_url"],
            session_id=mock_data["session_id"],
            code_level_logger=LogManager(mock_data["session_id"]).get_logger_by_name(
                os.getenv("CODE_LEVEL_LOGGER_NAME")
            ),
        )

        assert isinstance(
            result["chart_data"], MagicMock
        ), f"Expected MagicMock, got {type(result['chart_data'])}"

        assert result["main_instruction"] == "Show me CASA Product penetration"
        assert result["main_chart_sql"] == "SELECT * FROM table_name"


def test_execute_sql_query_empty_data(mock_data, capsys):
    """Test the case where the chart data is empty and ensure that the appropriate error handling is triggered."""
    load_dotenv()

    processed_data_empty_mock = MagicMock()
    processed_data_empty_mock.empty = True

    def mock_exec_empty_processed_data(code, local_vars):
        local_vars["processed_data"] = processed_data_empty_mock
        local_vars["chart_data"] = mock_return_data_execute_sql["chart_data"]

    with patch(
        "components.executor.mysql.fix_sql_query",
        return_value=("SELECT * FROM table_name2", "SELECT * FROM table_name2"),
    ) as mock_fix_sql_query, patch(
        "components.executor.mysql.execute_mysql_mariadb",
        return_value=mock_return_data_execute_sql,
    ), patch(
        "components.executor.template.code_executor_template",
        {"mysql": "dummy_code_template"},
    ), patch("builtins.exec", side_effect=mock_exec_empty_processed_data):
        result_empty = execute_sql_query(
            llama70b_client=mock_data["mock_llama70b_client"],
            data_summary=mock_data["mock_data_summary"],
            filters=mock_data["filters"],
            aggregations=mock_data["aggregations"],
            database_name=mock_data["database_name"],
            table_name=mock_data["table_name"],
            chart_query=mock_data["chart_data_execute"],
            sql_library="mysql",
            database_properties={
                "hostname": "localhost",
                "username": "root",
                "password": "password",
                "port": 3306,
            },
            chart_axis={},
            logging_url=mock_data["logging_url"],
            session_id=mock_data["session_id"],
            code_level_logger=LogManager(mock_data["session_id"]).get_logger_by_name(
                os.getenv("CODE_LEVEL_LOGGER_NAME")
            ),
        )

        mock_fix_sql_query.assert_called_once()

        captured = capsys.readouterr()

        assert "Chart Data Empty. Need to Fix" in captured.out
        assert "Empty Data SQL:" in captured.out

        assert "SELECT * FROM table_name2" in captured.out

        with pytest.raises(RuntimeError, match="Chart data is empty"):
            if result_empty["chart_data"].empty:
                raise RuntimeError("Chart data is empty")


def test_execute_sql_query_unsupported_lib(mock_data):
    """Test the case where an unsupported SQL library is passed and verify that a RuntimeError is raised."""
    load_dotenv()

    llama70b_client = mock_data["mock_llama70b_client"]
    data_summary = mock_data["mock_data_summary"]
    filters = mock_data["filters"]
    aggregations = mock_data["aggregations"]
    database_name = mock_data["database_name"]
    table_name = mock_data["table_name"]
    chart_query = mock_data["chart_data_execute"]
    sql_library = "mongodb"
    database_properties = {
        "hostname": "localhost",
        "username": "root",
        "password": "password",
        "port": 3306,
    }
    chart_axis = {}
    logging_url = mock_data["logging_url"]
    session_id = mock_data["session_id"]

    with pytest.raises(
        RuntimeError, match=f"SQL Library {sql_library} is not supported!"
    ):
        execute_sql_query(
            llama70b_client,
            data_summary,
            filters,
            aggregations,
            database_name,
            table_name,
            chart_query,
            sql_library,
            database_properties,
            chart_axis,
            logging_url,
            session_id=session_id,
            code_level_logger=LogManager(session_id).get_logger_by_name(
                os.getenv("CODE_LEVEL_LOGGER_NAME")
            ),
        )
