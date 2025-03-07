from typing import List, Dict, Any, Union
from pydantic.dataclasses import dataclass


@dataclass
class DataSummary:
    """A Summary of Database"""

    database_schema_sql: str
    table_description: str
    column_description_dict: Dict[str, str]
    column_sample_dict: Dict[str, Union[List[Any], str, int]]
    sql_library: str
    database_properties: Dict[str, Any]
    column_name_list: List[str]
    column_display_name_dict: Dict[str, str]
    column_data_tribes: Dict[str, str]
    column_n_unique_value_dict: Dict[str, int]
    column_sql_data_types: Dict[str, str]
    table_join_sql_query: str

    def __init__(
        self,
        database_schema_sql: str,
        table_description: str,
        column_description_dict: Dict[str, str],
        column_sample_dict: Dict[str, Union[List[Any], str, int]],
        sql_library: str,
        database_properties: Dict[str, Any],
        column_name_list: List[str],
        column_display_name_dict: Dict[str, str],
        column_data_tribes: Dict[str, str],
        column_n_unique_value_dict: Dict[str, int],
        column_sql_data_types: Dict[str, str],
        table_join_sql_query: str,
    ):
        # Type validation
        if not isinstance(database_schema_sql, str):
            raise TypeError("database_schema_sql must be a string")
        if not isinstance(table_description, str):
            raise TypeError("table_description must be a string")
        if not isinstance(column_description_dict, dict):
            raise TypeError("column_description_dict must be a dictionary")
        if not isinstance(column_sample_dict, dict):
            raise TypeError("column_sample_dict must be a dictionary")
        if not isinstance(sql_library, dict):
            raise TypeError("sql_library must be a dictionary")
        if not isinstance(database_properties, dict):
            raise TypeError("database_properties must be a dictionary")
        if not isinstance(column_name_list, list):
            raise TypeError("column_name_list must be a list")
        if not isinstance(column_display_name_dict, dict):
            raise TypeError("column_display_name_dict must be a dictionary")
        if not isinstance(column_data_tribes, dict):
            raise TypeError("column_data_tribes must be a dictionary")
        if not isinstance(column_n_unique_value_dict, dict):
            raise TypeError("column_n_unique_value_dict must be a dictionary")
        if not isinstance(column_sql_data_types, dict):
            raise TypeError("column_sql_data_types must be a dictionary")
        if not isinstance(table_join_sql_query, str):
            raise TypeError("table_join_sql_query must be a string")

        # Consistency validation
        if not all(isinstance(name, str) for name in column_name_list):
            raise ValueError("All column names must be strings")

        # Validate that all column-related dictionaries have consistent keys
        column_names_set = set(column_name_list)
        for dict_name, dict_obj in [
            ("column_description_dict", column_description_dict),
            ("column_display_name_dict", column_display_name_dict),
            ("column_data_tribes", column_data_tribes),
            ("column_n_unique_value_dict", column_n_unique_value_dict),
            ("column_sql_data_types", column_sql_data_types),
        ]:
            if not set(dict_obj.keys()).issubset(column_names_set):
                raise ValueError(
                    f"{dict_name} contains keys that are not in column_name_list",
                )

        # Validate that column_n_unique_value_dict contains only integers
        if not all(isinstance(val, int) for val in column_n_unique_value_dict.values()):
            raise ValueError(
                "All values in column_n_unique_value_dict must be integers",
            )

        # Assign values after validation
        self.database_schema_sql = database_schema_sql
        self.table_description = table_description
        self.column_description_dict = column_description_dict
        self.column_sample_dict = column_sample_dict
        self.sql_library = sql_library
        self.database_properties = database_properties
        self.column_name_list = column_name_list
        self.column_display_name_dict = column_display_name_dict
        self.column_data_tribes = column_data_tribes
        self.column_n_unique_value_dict = column_n_unique_value_dict
        self.column_sql_data_types = column_sql_data_types
        self.table_join_sql_query = table_join_sql_query

    def __repr__(self):
        """Return a string representation of the DataSummary object"""
        return f"DataSummary(columns={len(self.column_name_list)})"


@dataclass
class StorySkeleton:
    """A Skeleton of Story Telling Plan"""

    objectives: str
    storytelling_flow: str
    audiences: str
    narrative_flow: str
    assumptions: list
    scope: str
    context: dict
    possible_insights: list
    possible_outcomes: list


@dataclass
class StoryNarrative:
    """A Skeleton of Story Telling Plan"""

    narrative: str
    main_questions: List[dict]
