import logging

from qdrant_client import QdrantClient


def convert_qdrant_to_pinecone_format(response: list) -> list:
    """
    Converts Qdrant response format to Pinecone format.

    Args:
        response (list): List of Qdrant points, each with an 'id', 'payload', and optionally 'vector' and 'score'.

    Returns:
        list: List of dictionaries in Pinecone format.
    """
    new_response = []

    for point in response:
        response_data = {
            "id": point.id,
            "metadata": point.payload,  # Metadata from Qdrant's payload
            "score": point.score
            if hasattr(point, "score")
            else 0.0,  # Use score if present, else 0.0
            "values": point.vector
            if hasattr(point, "vector")
            else [],  # Include vector if present
        }
        new_response.append(response_data)

    return new_response


def get_all_table_info(
    embedding_model_url: str,
    qdrant_client: QdrantClient,
    database_name: str,
    collection_name: str,
) -> list:
    """Get all table informations from given Pinecone Index.
    If no table found, it returns empty list.

    Args:
        index (pinecone.Index): Pinecone index class.
        database_name (str): Database name in Pinecone.
        namespace (str): Namespace in Pinecone.
        embedding_model (str): Embedding model.
        provider (str): Embedding model provider.

    Returns:
        list: table informations.

    """
    collection_info = qdrant_client.get_collection(collection_name=collection_name)
    total_points = collection_info.points_count

    if total_points == 0:
        raise RuntimeError("Qdrant table collection has no points/vectors!")

    response, _ = qdrant_client.scroll(
        collection_name=collection_name,
        scroll_filter={
            "must": [{"key": "database_name", "match": {"value": database_name}}]
        },
        limit=total_points,
    )

    # Process the response
    if response:
        table_info_list = convert_qdrant_to_pinecone_format(response)
        return table_info_list
    return []


def get_table_info(
    embedding_model_url: str,
    qdrant_client: QdrantClient,
    table_name: str,
    database_name: str,
    database_identifier: str,
    collection_name: str,
    code_level_logger: logging.Logger,
) -> dict:
    """Get table information based on the embeddings from the table name given on given Pinecone Index.
    If no table found, it returns empty dictionary.

    Args:
        index (pinecone.Index): Pinecone index class.
        table_name (str): Table name in Pinecone.
        database_name (str): Database name in Pinecone.
        namespace (str): Namepsace in Pinecone.
        embedding_model (str): Embedding model.
        provider (str): Embedding model provider.

    Returns:
        dict: table information

    """
    collection_info = qdrant_client.get_collection(collection_name=collection_name)
    total_points = collection_info.points_count

    if total_points == 0:
        code_level_logger.error(
            f"Qdrant table collection {collection_name} has no points/vectors!"
        )
        raise RuntimeError(
            f"Qdrant table collection {collection_name} has no points/vectors!"
        )

    response, _ = qdrant_client.scroll(
        collection_name=collection_name,
        scroll_filter={
            "must": [
                {"key": "database_name", "match": {"value": database_name}},
                {"key": "table_name", "match": {"value": table_name}},
                {"key": "database_identifier", "match": {"value": database_identifier}},
            ]
        },
        limit=total_points,
    )

    if response:
        table_info = convert_qdrant_to_pinecone_format(response)[0]
        return table_info

    return {}


def get_table_metadata(
    embedding_model_url: str,
    qdrant_client: QdrantClient,
    database_name: str,
    table_name: str,
    collection_name: str,
) -> dict:
    """Get table metadata based on the embeddings from the table name given on given Pinecone Index.
    If no table found, it returns empty dictionary.

    Args:
        index (pinecone.Index): Pinecone index class.
        table_name (str): Table name in Pinecone.
        database_name (str): Database name in Pinecone.
        namespace (str): Namepsace in Pinecone.
        embedding_model (str): Embedding model.
        provider (str): Embedding model provider.

    Returns:
        dict: table metadata.

    """
    collection_info = qdrant_client.get_collection(collection_name=collection_name)
    total_points = collection_info.points_count

    if total_points == 0:
        raise RuntimeError("Qdrant table collection has no points/vectors!")

    response, _ = qdrant_client.scroll(
        collection_name=collection_name,
        scroll_filter={
            "must": [
                {"key": "database_name", "match": {"value": database_name}},
            ]
        },
        limit=total_points,
    )

    # Process the response if not empty
    if response:
        table_metadata = convert_qdrant_to_pinecone_format(response)[0]["metadata"]
        return table_metadata

    return {}


def get_joined_table_info(
    database_name: str,
    table_name: str,
    combined_table_description: str,
    table_level_metadata_list: list,
    code_level_logger: logging.Logger,
):
    """The function `get_joined_table_info` creates a dictionary containing information about a combined
    table from multiple table level metadata.

    :param database_name: The `database_name` parameter is a string that represents the name of the
    database where the table is located
    :type database_name: str
    :param table_name: The `table_name` parameter is a string that represents the name of the table for
    which you want to retrieve information from the database
    :type table_name: str
    :param combined_table_description: The function `get_joined_table_info` takes in several parameters
    to create a dictionary containing information about a joined table. The `combined_table_description`
    parameter is a string that describes the combined table
    :type combined_table_description: str
    :param table_level_metadata_list: A list containing metadata information for each table level. Each
    item in the list should be a dictionary with keys such as "column_list", "database_identifier",
    "last_metadata_update", "row_description", "source", "sql_database_name", etc
    :type table_level_metadata_list: list
    :return: The function `get_joined_table_info` returns a dictionary containing information about a
    joined table. The dictionary includes details such as the table ID, metadata (column list, database
    identifier, database name, foreign key, last metadata update, number of columns, primary key, row
    description, source, SQL database name, table description, table name, table short description, and
    table type), score, and
    """
    table_info: dict = {}

    combined_column_list: list = []

    for table_level_metadata in table_level_metadata_list:
        combined_column_list.extend(
            list(table_level_metadata["column_list"].split("|")),
        )

    combined_column_list = list(set(combined_column_list))
    combined_column_str = "|".join(map(str, combined_column_list))

    table_info["id"] = table_name
    table_info["metadata"] = {
        "column_list": combined_column_str,
        "database_identifier": table_level_metadata_list[0]["database_identifier"],
        "database_name": database_name,
        "foreign_key": "N/A",
        "last_metadata_update": table_level_metadata_list[0]["last_metadata_update"],
        "number_of_columns": len(combined_column_list),
        "primary_key": "N/A",
        "row_description": table_level_metadata_list[0]["row_description"],
        "source": table_level_metadata_list[0]["source"],
        "sql_database_name": table_level_metadata_list[0]["sql_database_name"],
        "table_description": combined_table_description,
        "table_name": table_name,
        "table_short_description": combined_table_description,
        "table_type": "FACT",
    }
    table_info["score"] = 0.0
    table_info["values"] = []

    return table_info
