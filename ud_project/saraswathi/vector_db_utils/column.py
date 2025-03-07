import logging

from qdrant_client import QdrantClient


def convert_joined_table_column_to_pinecone_format(joined_table_column_list: list):
    new_response: list = []

    for metadata in joined_table_column_list:
        response_data = {
            "id": f"{metadata['database_name']}.{metadata['cleaned_column_name']}",
            "metadata": metadata,
            "score": 0.0,
            "values": [],
        }
        new_response.append(response_data)

    return new_response


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


def get_column_info_list_from_table(
    embedding_model_url: str,
    qdrant_client: QdrantClient,
    table_name: str,
    table_id: str,
    database_identifier: str,
    collection_name: str,
    code_level_logger: logging.Logger,
) -> list:
    """Get column informations based on the table name and table id given.
    If no columns found, it returns empty list.

    Args:
        index (pinecone.Index): Pinecone index class.
        table_name (str): Table name in Pinecone.
        table_id (str): Table id in Pinecone.
        namespace (str): Namespace in Pinecone.
        embedding_model (str): Embedding model.
        provider (str): Embedding model provider.

    Returns:
        list: column informations

    """
    collection_info = qdrant_client.get_collection(collection_name=collection_name)
    total_points = collection_info.points_count

    if total_points == 0:
        code_level_logger.error(
            f"Qdrant column collection {collection_name} has no points/vectors!"
        )
        raise RuntimeError(
            f"Qdrant column collection {collection_name} has no points/vectors!"
        )

    response, _ = qdrant_client.scroll(
        collection_name=collection_name,
        scroll_filter={
            "must": [
                {"key": "sql_path", "match": {"value": table_id}},
                {"key": "db_identifier", "match": {"value": database_identifier}},
            ]
        },
        limit=1_000,  # Adjust the limit as needed
    )

    # Process the response if results are found
    if response:
        column_info_list = convert_qdrant_to_pinecone_format(response)
        return column_info_list

    # Return an empty list if no results are found
    return []
