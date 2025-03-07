import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import mysql.connector

# Connection details for source and destination MySQL servers
SOURCE_CONFIG = {
    "user": "AdaDB",
    "password": "Admin@2024",
    "host": "20.184.17.187",
    "database": "ada_banks_data_asset",
    "connect_timeout": 60000,
    "use_pure": True,
    "autocommit": False,
    "pool_name": "source_pool",
    "pool_size": 5,
}

DESTINATION_CONFIG = {
    "user": "AdaDB",
    "password": "Admin@2024",
    "host": "20.184.17.32",
    "database": "ada_banks_data_asset",
    "connect_timeout": 60000,
    "use_pure": True,
    "autocommit": False,
    "pool_name": "dest_pool",
    "pool_size": 5,
}

# List of tables to migrate
TABLES_TO_MIGRATE = {
    "report_cross_selling_performance_saleschannel_171024",
}


def verify_table_migration(source_connection, destination_connection, table_name):
    """Verifies if a table has been completely migrated by comparing:
    1. Row counts
    2. Schema structure
    3. Sample data checksums
    Returns: (is_migrated, details)
    """
    try:
        with source_connection.cursor(
            buffered=True,
        ) as source_cursor, destination_connection.cursor(
            buffered=True,
        ) as destination_cursor:
            # Check 1: Compare row counts
            source_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            source_count = source_cursor.fetchone()[0]
            destination_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            dest_count = destination_cursor.fetchone()[0]
            if source_count != dest_count:
                return (
                    False,
                    f"Row count mismatch. Source: {source_count}, Destination: {dest_count}",
                )

            # Check 2: Compare schema structure
            source_cursor.execute(f"SHOW CREATE TABLE {table_name}")
            source_schema = source_cursor.fetchone()[1]
            destination_cursor.execute(f"SHOW CREATE TABLE {table_name}")
            dest_schema = destination_cursor.fetchone()[1]
            if source_schema != dest_schema:
                return (False, "Schema structures don't match")

            # Check 3: Compare checksums of sample data
            # Use MD5 hash of concatenated primary key values from first and last 100 rows
            checksum_query = f"""
                SELECT MD5(GROUP_CONCAT(CAST(t.* AS CHAR) ORDER BY 1))
                FROM (
                    SELECT *
                    FROM {table_name}
                    ORDER BY 1
                    LIMIT 100
                ) t
            """
            source_cursor.execute(checksum_query)
            source_checksum = source_cursor.fetchone()[0]
            destination_cursor.execute(checksum_query)
            dest_checksum = destination_cursor.fetchone()[0]
            if source_checksum != dest_checksum:
                return (False, "Data checksums don't match")

    except mysql.connector.Error as err:
        return (False, f"Error during verification: {err!s}")

    return (True, "Table appears to be fully migrated")


def log_message(message):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()  # Ensure immediate output


def execute_with_retry(
    connection,
    cursor,
    query,
    params=None,
    max_retries=3,
    retry_delay=5,
):
    """Execute a query with retry logic."""
    for attempt in range(max_retries):
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return True
        except Exception as err:
            log_message(f"Query failed, attempt {attempt + 1}/{max_retries}: {err}")
            time.sleep(retry_delay)
            # Try to reconnect if connection was lost
            if not connection.is_connected():
                connection.reconnect(attempts=3, delay=retry_delay)
                cursor = connection.cursor(buffered=True)


def executemany_with_retry(
    connection,
    cursor,
    query,
    params,
    batch_size=100000,
    max_retries=3,
    retry_delay=5,
):
    """Execute a batch insert with retry logic and smaller sub-batches."""
    for i in range(0, len(params), batch_size):
        batch = params[i : i + batch_size]
        for attempt in range(max_retries):
            try:
                cursor.executemany(query, batch)
                connection.commit()
                break
            except mysql.connector.Error as err:
                if attempt == max_retries - 1:  # Last attempt
                    raise
                log_message(
                    f"Batch insert failed, attempt {attempt + 1}/{max_retries}: {err}",
                )
                time.sleep(retry_delay)
                if not connection.is_connected():
                    connection.reconnect(attempts=3, delay=retry_delay)
                    cursor = connection.cursor(buffered=True)


def create_connection_with_retries(config, max_retries=3, retry_delay=5):
    """Attempts to connect to a database with retries."""
    for attempt in range(max_retries):
        try:
            connection = mysql.connector.connect(**config)
            cursor = connection.cursor(buffered=True)

            # Set session variables for better stability
            session_settings = [
                "SET SESSION net_read_timeout=600000",
                "SET SESSION net_write_timeout=600000",
                "SET SESSION wait_timeout=600000",
                "SET SESSION interactive_timeout=600000",
            ]

            for setting in session_settings:
                execute_with_retry(connection, cursor, setting)

            cursor.close()
            return connection
        except mysql.connector.Error as err:
            if attempt == max_retries - 1:
                log_message(f"Failed to connect after {max_retries} attempts: {err}")
                raise
            log_message(
                f"Connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...",
            )
            time.sleep(retry_delay)


def get_table_info(connection, cursor, table_name):
    """Get table size and chunk count for optimal processing."""
    execute_with_retry(connection, cursor, f"ANALYZE TABLE {table_name}")
    execute_with_retry(connection, cursor, f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]

    # Calculate optimal chunk size based on table size
    chunk_size = 100000
    return row_count, chunk_size


def migrate_table(source_config, destination_config, table_name, create_statement):
    """Migrates the schema and data for a single table in a separate thread."""
    source_connection = None
    destination_connection = None

    try:
        source_connection = create_connection_with_retries(source_config)
        destination_connection = create_connection_with_retries(destination_config)

        # First, verify if the table is already migrated
        is_migrated, details = verify_table_migration(
            source_connection,
            destination_connection,
            table_name,
        )

        if is_migrated:
            log_message(f"Table '{table_name}' is already fully migrated. Skipping.")
            return
        log_message(f"Table '{table_name}' needs migration. Reason: {details}")

        source_cursor = source_connection.cursor(buffered=True)
        destination_cursor = destination_connection.cursor(buffered=True)

        # Drop and create the table in the destination
        execute_with_retry(
            destination_connection,
            destination_cursor,
            f"DROP TABLE IF EXISTS {table_name}",
        )
        execute_with_retry(destination_connection, destination_cursor, create_statement)
        log_message(f"Table '{table_name}' schema migrated successfully.")

        # Rest of the migration logic remains the same...
        # Get table information and optimal chunk size
        total_rows, chunk_size = get_table_info(
            source_connection,
            source_cursor,
            table_name,
        )

        # Disable indexes and foreign key checks for faster inserts
        execute_with_retry(
            destination_connection,
            destination_cursor,
            "SET FOREIGN_KEY_CHECKS=0",
        )
        execute_with_retry(
            destination_connection,
            destination_cursor,
            f"ALTER TABLE {table_name} DISABLE KEYS",
        )

        # Migrate data in chunks
        offset = 0
        total_migrated = 0

        while True:
            query = f"SELECT * FROM {table_name} LIMIT {chunk_size} OFFSET {offset}"

            for trial in range(3):
                execute_with_retry(source_connection, source_cursor, query)

                rows = source_cursor.fetchall() if source_cursor.with_rows else []

                if rows != []:
                    break

            if not rows or rows == []:
                log_message(f"No more rows to fetch for table '{table_name}'")
                break

            placeholders = ", ".join(["%s"] * len(rows[0]))
            insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"

            executemany_with_retry(
                destination_connection,
                destination_cursor,
                insert_query,
                rows,
                batch_size=100000,
            )

            total_migrated += len(rows)
            progress = (total_migrated / total_rows) * 100 if total_rows > 0 else 100
            log_message(
                f"Table '{table_name}': {progress:.2f}% complete ({total_migrated:,}/{total_rows:,} rows)",
            )

            offset += chunk_size

        # Re-enable indexes and foreign key checks
        execute_with_retry(
            destination_connection,
            destination_cursor,
            f"ALTER TABLE {table_name} ENABLE KEYS",
        )
        execute_with_retry(
            destination_connection,
            destination_cursor,
            "SET FOREIGN_KEY_CHECKS=1",
        )

        log_message(f"Table '{table_name}' migration completed successfully.")

    except Exception as e:
        log_message(f"Error migrating table '{table_name}': {e!s}")
        raise
    finally:
        if source_connection:
            source_connection.close()
        if destination_connection:
            destination_connection.close()


def get_source_schema(connection, cursor, db_name):
    """Fetches schema details for specified tables in the source database."""
    schema = {}
    for table_name in TABLES_TO_MIGRATE:
        try:
            execute_with_retry(
                connection,
                cursor,
                f"SHOW CREATE TABLE {db_name}.{table_name}",
            )
            schema[table_name] = cursor.fetchone()[1]
        except mysql.connector.Error as err:
            log_message(
                f"Warning: Could not fetch schema for table {table_name}: {err}",
            )
    return schema


def main():
    try:
        # Connect to source database to get schema
        source_connection = create_connection_with_retries(SOURCE_CONFIG)
        source_cursor = source_connection.cursor(buffered=True)

        log_message("Starting migration for specified tables...")
        source_schema = get_source_schema(
            source_connection,
            source_cursor,
            SOURCE_CONFIG["database"],
        )

        if not source_schema:
            raise Exception("No valid tables found for migration!")

        source_cursor.close()
        source_connection.close()

        # Sort tables by name to ensure consistent migration order
        sorted_tables = sorted(source_schema.items())

        log_message(
            f"Found {len(sorted_tables)} tables to migrate: {', '.join(table[0] for table in sorted_tables)}",
        )

        # Use ThreadPoolExecutor with reduced worker count
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = []
            for table_name, create_statement in sorted_tables:
                future = executor.submit(
                    migrate_table,
                    SOURCE_CONFIG,
                    DESTINATION_CONFIG,
                    table_name,
                    create_statement,
                )
                futures.append((table_name, future))

            # Wait for all migrations to complete
            for table_name, future in futures:
                try:
                    future.result()
                except Exception as e:
                    log_message(f"Migration failed for table {table_name}: {e!s}")
                    raise

        log_message("Database migration completed successfully!")

    except Exception as e:
        log_message(f"Migration failed: {e!s}")
        raise


if __name__ == "__main__":
    main()
