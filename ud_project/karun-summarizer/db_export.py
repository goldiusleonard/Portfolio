import csv
import os
from typing import Dict, List

import mysql.connector
from dotenv import load_dotenv

# Create data directory (if not exists)
os.makedirs("data", exist_ok=True)


# Establish MySQL database connection
def connect_to_db():
    load_dotenv()
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        database=os.getenv("MYSQL_DATABASE"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
    )


# Fetch data from MySQL database
def fetch_table_data(table_name: str) -> List[Dict]:
    # Establish database connection
    conn = connect_to_db()
    try:
        # Create cursor that returns results as dictionary
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name}")

        # Fetch and return all rows as list of dictionaries
        return cursor.fetchall()
    finally:
        # Clean up resources
        cursor.close()
        conn.close()


# Export database records to CSV file
def export_to_csv(data: List[Dict], table_name: str) -> str:
    if not data:
        return None

    # Generate CSV filename using table name
    filename = f"data/{table_name}.csv"

    # Write dictionary data to CSV file
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        # Create CSV writer using dictionary keys as headers
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()  # Columns data
        writer.writerows(data)  # Rows data

    return filename


# Get all table names from the database
def get_all_tables(conn) -> List[str]:
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        return [table[0] for table in cursor.fetchall()]
    finally:
        cursor.close()


# Main function to export all tables to CSV files
def export_database_tables():
    print("\nConnecting to database...")
    try:
        conn = connect_to_db()

        # Get all tables from the database
        tables = get_all_tables(conn)
        print(f"Found {len(tables)} tables in database")

        for table in tables:
            print(f"\nProcessing {table}...")
            try:
                # Fetch all records from table
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                print(f"Found {len(rows)} rows")

                if rows:
                    csv_file = export_to_csv(rows, table)
                    print(f"Data exported to: {csv_file}")
                else:
                    print("No data to export")

            except Exception as e:
                print(f"Error processing {table}: {e!s}")
            finally:
                cursor.close()

    except Exception as e:
        print(f"Database connection error: {e!s}")
    finally:
        conn.close()
        print("\nExport process completed!")


# Run main function
if __name__ == "__main__":
    export_database_tables()
