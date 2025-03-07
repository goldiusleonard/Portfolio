import sys

sys.stdout.reconfigure(encoding="utf-8")
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

from db.db import Database

load_dotenv()

api_ip = os.getenv("api_ip")
port_manager = int(os.getenv("port_manager"))


load_dotenv()

mysql_user = os.getenv("mysql_user")
mysql_password = os.getenv("mysql_password")
mysql_host = os.getenv("mysql_host")
mysql_port = os.getenv("mysql_port")
input_mysql_database = os.getenv("mysql_database")
output_mysql_database = os.getenv("output_mysql_database")


def db_to_csv():
    url = f"mysql+pymysql://{mysql_user}:{quote_plus(mysql_password)}@{mysql_host}:{mysql_port}/{input_mysql_database}"
    db = Database(url, [], None)

    # Read the CSV file and drop the unnecessary column
    # df = pd.read_csv('comments_output.csv', index_col=0)
    df = db._fetch_data_from_source("comments_output")

    # Replace NaN values with empty strings in the DataFrame
    # df_final = df_final.fillna('').copy()
    # print(df.head())
    file_path = "comments_output.csv"
    # df.to_csv(file_path, encoding='utf-8', errors='ignore', index=False)
    # df = df.reset_index(drop=True)
    df.to_csv(file_path, index=False)
    print("inserting data to table...")
    print("Done...")


if __name__ == "__main__":
    db_to_csv()
