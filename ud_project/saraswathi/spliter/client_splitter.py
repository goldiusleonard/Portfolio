from typing import Tuple


class ClientSpliter:
    CLIENT_DATA: dict = {
        # MAG - Company Analysis
        "mag_001": {
            "table_collection": "chrmdb_mag_001_001_das_tbl_metadata_clnt",
            "column_collection": "chrmdb_mag_001_001_das_col_metadata_clnt",
            "sql_url": "mysql+pymysql://UserDataDb:sa_54321@20.212.32.214/ada_mag",  # Not Used Due to MAG uses their own databricks
            "sql_library": "Databricks SQL",
            "industry_domain": "airline",
            "company_name": "Malaysia Airlines",
            "task": "company_analysis",
            "is_mag": True,
        },
        # MAG - Company Analysis
        "mag001": {
            "table_collection": "chrmdb_mag_001_001_das_tbl_metadata_clnt",
            "column_collection": "chrmdb_mag_001_001_das_col_metadata_clnt",
            "sql_url": "mysql+pymysql://UserDataDb:sa_54321@20.212.32.214/ada_mag",  # Not Used Due to MAG uses their own databricks
            "sql_library": "Databricks SQL",
            "industry_domain": "airline",
            "company_name": "Malaysia Airlines",
            "task": "company_analysis",
            "is_mag": True,
        },
        # Starhub - Company Analysis
        "starhub_001": {
            "table_collection": "chrmdb_sth_001_001_das_tbl_metadata",
            "column_collection": "chrmdb_sth_001_001_das_col_metadata",
            "sql_url": "mysql+pymysql://UserDataDb:sa_54321@20.212.32.214/starhub_data_asset",
            "sql_library": "MySQL",
            "industry_domain": "telecommunication",
            "company_name": "Starhub",
            "task": "company_analysis",
            "is_mag": False,
        },
        # Starhub - Company Analysis
        "starhub001": {
            "table_collection": "chrmdb_sth_001_001_das_tbl_metadata",
            "column_collection": "chrmdb_sth_001_001_das_col_metadata",
            "sql_url": "mysql+pymysql://UserDataDb:sa_54321@20.212.32.214/starhub_data_asset",
            "sql_library": "MySQL",
            "industry_domain": "telecommunication",
            "company_name": "Starhub",
            "task": "company_analysis",
            "is_mag": False,
        },
        # Starhub - Competitive Analysis
        "starhub_002": {
            "table_collection": "chrmdb_starhub_tbl_lvl_meta_data_oo",
            "column_collection": "chrmdb_starhub_col_lvl_meta_data_oo",
            "sql_url": "mysql+pymysql://UserDataDb:sa_54321@20.212.32.214/datalake",
            "sql_library": "MySQL",
            "industry_domain": "telecommunication",
            "company_name": "Starhub",
            "task": "competitive_analysis",
            "is_mag": False,
        },
        # Starhub - Competitive Analysis
        "starhub002": {
            "table_collection": "chrmdb_starhub_tbl_lvl_meta_data_oo",
            "column_collection": "chrmdb_starhub_col_lvl_meta_data_oo",
            "sql_url": "mysql+pymysql://UserDataDb:sa_54321@20.212.32.214/datalake",
            "sql_library": "MySQL",
            "industry_domain": "telecommunication",
            "company_name": "Starhub",
            "task": "competitive_analysis",
            "is_mag": False,
        },
    }

    def __init__(self) -> None:
        pass

    def get_namespace(
        self,
        client_id: str,
    ) -> Tuple[str, str]:
        """Get Table Namespace and Column Namespace from Client ID.

        Args:
            client_id (str): ID of Client.

        Return:
            table_collection: str
            column_collection: str

        """
        table_collection: str = self.CLIENT_DATA[client_id]["table_collection"]
        column_collection: str = self.CLIENT_DATA[client_id]["column_collection"]

        return table_collection, column_collection

    def get_sqlurl(
        self,
        client_id: str,
    ) -> str:
        sql_url: str = self.CLIENT_DATA[client_id]["sql_url"]

        return sql_url

    def get_sqllibrary(
        self,
        client_id: str,
    ) -> str:
        sql_library: str = self.CLIENT_DATA[client_id]["sql_library"]

        return sql_library

    def get_industrydomain(
        self,
        client_id: str,
    ) -> str:
        industry_domain: str = self.CLIENT_DATA[client_id]["industry_domain"]

        return industry_domain

    def get_companyname(
        self,
        client_id: str,
    ) -> str:
        company_name: str = self.CLIENT_DATA[client_id]["company_name"]

        return company_name

    def get_task(
        self,
        client_id: str,
    ) -> str:
        task = self.CLIENT_DATA[client_id]["task"]
        return task

    def get_is_mag(
        self,
        client_id: str,
    ) -> str:
        is_mag = self.CLIENT_DATA[client_id]["is_mag"]
        return is_mag
