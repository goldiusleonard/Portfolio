import os
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    MetaData,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Declare the base class for SQLAlchemy
Base = declarative_base()
# Step 1: Read the CSV file into a pandas DataFrame
csv_file_path = "sub_category.csv"
df = pd.read_csv(csv_file_path)
print(df.head())

load_dotenv()

mysql_user = os.getenv("mysql_user")
mysql_password = os.getenv("mysql_password")
mysql_host = os.getenv("mysql_host")
mysql_port = os.getenv("mysql_port")
input_mysql_database = os.getenv("mysql_database")
output_mysql_database = os.getenv("output_mysql_database")

# Replace with your actual MySQL credentials
DATABASE_URI = f"mysql+pymysql://{mysql_user}:{quote_plus(mysql_password)}@{mysql_host}:{mysql_port}/{input_mysql_database}"


metadata = MetaData()


# Define the table schema for category_table
class CategoryTableSchema(Base):
    __tablename__ = "category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(
        String(50),
        nullable=False,
    )  # Category name (e.g., scam, 3r, atipsom, etc.)


class YourTable(Base):
    __tablename__ = "sub_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sub_category_name = Column(
        String(50),
        nullable=False,
    )  # Sub-category name (e.g., gold, forex, human trafficking)
    category_id = Column(
        Integer,
        ForeignKey(CategoryTableSchema.id),
        nullable=False,
    )  # ForeignKey to category_table


engine = create_engine(DATABASE_URI)


# Create the table
metadata.create_all(engine)
YourTable.metadata.create_all(engine)

# Step 3: Create a session for interaction with the database
Session = sessionmaker(bind=engine)
session = Session()

# Step 5: Insert DataFrame rows into MySQL table
# Loop through each row in the DataFrame and insert it into the table
for index, row in df.iterrows():
    record = YourTable(
        sub_category_name=row["sub_category_name"],
        category_id=row["category_id"],
    )
    session.add(record)

# Step 6: Commit the transaction to the database
session.commit()

# Step 7: Close the session
session.close()

print("CSV data successfully loaded into MySQL!")
