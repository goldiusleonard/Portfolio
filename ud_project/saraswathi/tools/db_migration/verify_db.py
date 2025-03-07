import mysql.connector

# Source database connection details
source_host = "20.184.17.187"
source_user = "AdaDB"
source_password = "Admin@2024"
source_database = "ada_banks_data_asset"

# Target database connection details
target_host = "20.184.17.32"
target_user = "AdaDB"
target_password = "Admin@2024"
target_database = "ada_banks_data_asset"

# Connect to source database
source_conn = mysql.connector.connect(
    host=source_host,
    user=source_user,
    password=source_password,
    database=source_database,
)
source_cursor = source_conn.cursor()

# Connect to target database
target_conn = mysql.connector.connect(
    host=target_host,
    user=target_user,
    password=target_password,
    database=target_database,
)
target_cursor = target_conn.cursor()

# Get a list of all tables in the source database
source_cursor.execute("SHOW TABLES;")
source_tables = [table[0] for table in source_cursor.fetchall()]

# Verify each table exists in the target database and has the same structure and row count
for table_name in source_tables:
    # Check if table exists in target database
    target_cursor.execute(f"SHOW TABLES LIKE '{table_name}';")
    if not target_cursor.fetchone():
        print(f"Table '{table_name}' not found in target database.")
        continue

    # Compare table structure
    source_cursor.execute(f"SHOW CREATE TABLE {table_name};")
    source_structure = source_cursor.fetchone()[1]
    target_cursor.execute(f"SHOW CREATE TABLE {table_name};")
    target_structure = target_cursor.fetchone()[1]

    if source_structure != target_structure:
        print(f"Table '{table_name}' structure does not match.")
        continue

    # Compare row count
    source_cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    source_row_count = source_cursor.fetchone()[0]
    target_cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    target_row_count = target_cursor.fetchone()[0]

    if source_row_count != target_row_count:
        print(
            f"Table '{table_name}' row count does not match. Source: {source_row_count}, Target: {target_row_count}",
        )

print("Database migration verification complete.")

# Close database connections
source_conn.close()
target_conn.close()
