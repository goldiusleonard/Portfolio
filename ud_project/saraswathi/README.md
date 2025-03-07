
# Saraswathi LLM Agent

## Overview

The Saraswathi LLM Agent is an AI-powered tool designed to facilitate interactions with a language model (LLM) for chart generation aimed at data analysis. This agent focuses on delivering fast, intelligent responses to support analytical tasks while maintaining high accuracy. It enhances user experience by streamlining the process of creating insightful visualizations, making it a valuable tool for applications where LLM-driven chart generation is central to effective data analysis.

### Key Features

- **Chart Generation & Insight Creation**: Automatically generates charts based on user inputs or data requests, along with visual descriptions and actionable business recommendations. Optimized for performance even under concurrent loads, ensuring fast and accurate insights.
- **Data Querying**: Integrates with MySQL databases for seamless data retrieval and analysis.
- **Predefined KPI Integration**: Easily integrates with predefined KPIs, enabling seamless analysis and visualization of key performance metrics tailored to specific business needs.
- **Real-time Data Updates**: Automatically updates charts with the latest data based on SQL queries, ensuring that visualizations reflect the most current information available.

## Installation

To run the Saraswathi LLM Agent, you'll need Python 3.9+ and several Python libraries. Clone this repository and install the required dependencies.

```bash
git clone https://userdata-ada@dev.azure.com/userdata-ada/saraswathi/_git/saraswathi
cd saraswathi
pip3 install -r requirements.txt
```

### Prerequisites

- **Python 3.9+**: Ensure Python 3.9 or higher is installed for compatibility with the latest features and dependencies.
- **vLLM Server Setup**: Set up a vLLM server with **Llama 3.1 70B Instruct AWQ** model for optimized LLM-based tasks.
- **Embedding Server Setup**: Set up an embedding server with **Nomic V1** model for querying metadata.
- **Database Setup**: MySQL database configuration, including necessary permissions for data querying and updates.
- **Environment Configuration**: Set the vLLM API URL, Embedding API URL, API key, and database credentials in the `.env` file for secure access.

## Usage

### Running the Agent

To start the Saraswathi LLM Agent, run the `main.py` script. This will initialize the agent and start the FastAPI server for handling API requests.

```bash
python main.py
```

Once the server is running, you can interact with the agent through the API. By default, it will be available at `http://localhost:8000`.

### API Endpoints

### PUT /feedback/save

Save feedback to MongoDB and Qdrant.

**Request Body:**

- `feedback_json`: Feedback JSON to be saved.

**Example Input:**

<details>
<summary>Sample Input JSON</summary>

```json
{
  "chart_id": "442b2d55-b758-42a9-8b84-0f1a90251f68",
  "chart_data": {
    "chart_id": "442b2d55-b758-42a9-8b84-0f1a90251f68",
    "user_id": "goldius.leo@userdata.tech",
    "session_id": "baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9",
    "request_time": "2024-11-12T11:51:59.560000",
    "last_updated": "2024-11-12T11:53:15.936000",
    "user_query": " The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.",
    "narrative": "To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.",
    "question": "What is the product penetration rate for debit cards across different income levels?",
    "time_frame": "",
    "time_duration": "",
    "chart_name": "Visual 5",
    "chart_title": "Debit Card Penetration Rate by Income Level",
    "chart_category": "comparison",
    "chart_type": "grouped_bar_chart",
    "chart_position": 1,
    "chart_axis": {
      "xAxis_title": "Income Level",
      "xAxis_column": "income_level",
      "yAxis_title": "Debit Card Penetration Rate",
      "yAxis_column": "has_debit_card",
      "yAxis_aggregation": "COUNT",
      "yAxis2_title": "",
      "yAxis2_column": "",
      "yAxis2_aggregation": "",
      "yAxis3_title": "",
      "yAxis3_column": "",
      "yAxis3_aggregation": "",
      "series_title": "",
      "series_column": ""
    },
    "sql_query": "SELECT income_level AS xAxis, COUNT(has_debit_card) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new WHERE has_debit_card = 'TRUE' GROUP BY income_level;",
    "status": "Success",
    "chart_json": {
      "Subscription_ID": "",
      "Subscription_Name": "",
      "Shared_User_ID": "",
      "Chart_SQL_Library": "MySQL",
      "xAxis": "Income Level",
      "yAxis": "Total Debit Card Penetration Rate",
      "Aggregated_Table_JSON": {
        "Visual_Title": "Debit Card Penetration Rate by Income Level",
        "Chart_Axis": {},
        "Chart_Size": 120
      },
      "Aggregated_Table_Column": [
        "has_debit_card",
        "income_level"
      ],
      "Database_Identifier": "label1"
    },
    "module_version": "0.1.0",
    "db_tag": "label1",
    "total_inference_time": 30.391773499999545
  }
}
```

</details>

### GET /feedback/search/user_query/{user_query}

Search relevant chart samples based on user query.

**Request Body**

- `user_query`: chart user query.

**Example Input:**

`They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.`

**Responses:**

- Returns a JSON response suitable containing one or more chart data with its feedback which is/are relevant to the user query.

**Example Output:**

<details>
<summary>Sample Output JSON</summary>

```json
{
  "results": [
    "{\"chart_id\": \"442b2d55-b758-42a9-8b84-0f1a90251f68\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T16:17:34.472879\", \"last_updated\": \"2024-11-15T16:17:34.472899\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the product penetration rate for debit cards across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 5\", \"chart_title\": \"Debit Card Penetration Rate by Income Level\", \"chart_category\": \"comparison\", \"chart_type\": \"grouped_bar_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"income_level\", \"yAxis_title\": \"Debit Card Penetration Rate\", \"yAxis_column\": \"has_debit_card\", \"yAxis_aggregation\": \"COUNT\", \"yAxis2_title\": \"\", \"yAxis2_column\": \"\", \"yAxis2_aggregation\": \"\", \"yAxis3_title\": \"\", \"yAxis3_column\": \"\", \"yAxis3_aggregation\": \"\", \"series_title\": \"\", \"series_column\": \"\"}, \"sql_query\": \"SELECT income_level AS xAxis, COUNT(has_debit_card) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new WHERE has_debit_card = 'TRUE' GROUP BY income_level;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"xAxis\": \"Income Level\", \"yAxis\": \"Total Debit Card Penetration Rate\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Debit Card Penetration Rate by Income Level\", \"Chart_Axis\": {}, \"Chart_Size\": 120}, \"Aggregated_Table_Column\": [\"has_debit_card\", \"income_level\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 30.391773499999545, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"True\"}}",
    "{\"chart_id\": \"6c422aec-24eb-406c-b850-6e74af459e34\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T16:17:34.616542\", \"last_updated\": \"2024-11-15T16:17:34.616544\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the distribution of customers across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 1\", \"chart_title\": \"Income Level Distribution\", \"chart_category\": \"distribution\", \"chart_type\": \"histogram_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"age\"}, \"sql_query\": \"SELECT age AS xAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"Number_of_Bins\": {\"sqrt\": 1069, \"sturges\": 22, \"rice\": 210}, \"xAxis\": \"Income Level\", \"yAxis\": \"Frequency\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Income Level Distribution\", \"Chart_Axis\": {}, \"Chart_Size\": 9504856}, \"Aggregated_Table_Column\": [\"age\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 29.657983790995786, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}",
    "{\"chart_id\": \"0adf6ec3-09e0-4777-9995-d5112d765244\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T16:17:34.767455\", \"last_updated\": \"2024-11-15T16:17:34.767457\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the product penetration rate for loans across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 4\", \"chart_title\": \"Loan Penetration Rate by Income Level\", \"chart_category\": \"comparison\", \"chart_type\": \"grouped_bar_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"income_level\", \"yAxis_title\": \"Loan Penetration Rate\", \"yAxis_column\": \"has_loan\", \"yAxis_aggregation\": \"COUNT\", \"yAxis2_title\": \"\", \"yAxis2_column\": \"\", \"yAxis2_aggregation\": \"\", \"yAxis3_title\": \"\", \"yAxis3_column\": \"\", \"yAxis3_aggregation\": \"\", \"series_title\": \"\", \"series_column\": \"\"}, \"sql_query\": \"SELECT income_level AS xAxis, COUNT(CASE WHEN has_loan = 'TRUE' THEN 1 END) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new GROUP BY income_level;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"xAxis\": \"Income Level\", \"yAxis\": \"Total Loan Penetration Rate\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Loan Penetration Rate by Income Level\", \"Chart_Axis\": {}, \"Chart_Size\": 120}, \"Aggregated_Table_Column\": [\"has_loan\", \"income_level\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 32.35852458298905, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}",
    "{\"chart_id\": \"442b2d55-b758-42a9-8b84-0f1a90251f68\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T16:17:34.905499\", \"last_updated\": \"2024-11-15T16:17:34.905502\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the product penetration rate for debit cards across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 5\", \"chart_title\": \"Debit Card Penetration Rate by Income Level\", \"chart_category\": \"comparison\", \"chart_type\": \"grouped_bar_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"income_level\", \"yAxis_title\": \"Debit Card Penetration Rate\", \"yAxis_column\": \"has_debit_card\", \"yAxis_aggregation\": \"COUNT\", \"yAxis2_title\": \"\", \"yAxis2_column\": \"\", \"yAxis2_aggregation\": \"\", \"yAxis3_title\": \"\", \"yAxis3_column\": \"\", \"yAxis3_aggregation\": \"\", \"series_title\": \"\", \"series_column\": \"\"}, \"sql_query\": \"SELECT income_level AS xAxis, COUNT(has_debit_card) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new WHERE has_debit_card = 'TRUE' GROUP BY income_level;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"xAxis\": \"Income Level\", \"yAxis\": \"Total Debit Card Penetration Rate\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Debit Card Penetration Rate by Income Level\", \"Chart_Axis\": {}, \"Chart_Size\": 120}, \"Aggregated_Table_Column\": [\"has_debit_card\", \"income_level\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 30.391773499999545, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"True\"}}",
    "{\"chart_id\": \"0d87b1f1-865c-4d41-bf3c-1be606507bfc\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T16:17:35.053509\", \"last_updated\": \"2024-11-15T16:17:35.053511\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the product penetration rate for credit cards across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 2\", \"chart_title\": \"Credit Card Penetration Rate by Income Level\", \"chart_category\": \"comparison\", \"chart_type\": \"grouped_bar_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"income_level\", \"yAxis_title\": \"Credit Card Penetration Rate\", \"yAxis_column\": \"has_credit_card\", \"yAxis_aggregation\": \"COUNT\", \"yAxis2_title\": \"\", \"yAxis2_column\": \"\", \"yAxis2_aggregation\": \"\", \"yAxis3_title\": \"\", \"yAxis3_column\": \"\", \"yAxis3_aggregation\": \"\", \"series_title\": \"\", \"series_column\": \"\"}, \"sql_query\": \"SELECT income_level AS xAxis, COUNT(CASE WHEN has_credit_card = 'TRUE' THEN 1 END) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new GROUP BY income_level;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"xAxis\": \"Income Level\", \"yAxis\": \"Total Credit Card Penetration Rate\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Credit Card Penetration Rate by Income Level\", \"Chart_Axis\": {}, \"Chart_Size\": 120}, \"Aggregated_Table_Column\": [\"has_credit_card\", \"income_level\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 33.927351041988004, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}",
    "{\"chart_id\": \"1f0ca50d-121b-4623-a7ac-49ceff4d290a\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T16:17:35.202507\", \"last_updated\": \"2024-11-15T16:17:35.202511\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the product penetration rate for current accounts across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 3\", \"chart_title\": \"Current Account Penetration Rate by Income Level\", \"chart_category\": \"comparison\", \"chart_type\": \"grouped_bar_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"income_level\", \"yAxis_title\": \"Current Account Penetration Rate\", \"yAxis_column\": \"has_current_account\", \"yAxis_aggregation\": \"COUNT\", \"yAxis2_title\": \"\", \"yAxis2_column\": \"\", \"yAxis2_aggregation\": \"\", \"yAxis3_title\": \"\", \"yAxis3_column\": \"\", \"yAxis3_aggregation\": \"\", \"series_title\": \"\", \"series_column\": \"\"}, \"sql_query\": \"SELECT income_level AS xAxis, COUNT(CASE WHEN has_current_account = 'TRUE' THEN 1 END) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new GROUP BY income_level;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"xAxis\": \"Income Level\", \"yAxis\": \"Current Account Penetration Rate\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Current Account Penetration Rate by Income Level\", \"Chart_Axis\": {}, \"Chart_Size\": 120}, \"Aggregated_Table_Column\": [\"has_current_account\", \"income_level\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 32.37729849999596, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}",
    "{\"chart_id\": \"283f05b0-fb4d-42f8-9ef0-121d795d8a74\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"fb680974-7123-439e-bccb-9c0347ab0295\", \"request_time\": \"2024-11-15T16:17:35.346551\", \"last_updated\": \"2024-11-15T16:17:35.346556\", \"user_query\": \" The user's primary intent is to analyze the average number of products per customer, specifically focusing on the marital status dimension, in order to gain insights into customer cross-sell performance.\", \"narrative\": \"To gain a deeper understanding of customer cross-sell performance, we need to analyze the average number of products per customer, with a focus on the marital status dimension. This will help us identify trends and patterns in customer behavior, enabling us to tailor our marketing strategies and improve customer engagement. By examining the average number of products per customer across different marital statuses, we can uncover insights that inform our business decisions and drive growth.\", \"question\": \"What is the percentage of customers with multiple products across different marital statuses?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": null, \"chart_title\": \"Percentage of Customers with Multiple Products by Marital Status\", \"chart_category\": \"composition\", \"chart_type\": \"pie_chart\", \"chart_position\": null, \"chart_axis\": null, \"sql_query\": null, \"status\": \"Fail\", \"chart_json\": null, \"module_version\": \"0.1.2\", \"db_tag\": null, \"total_inference_time\": null, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}",
    "{\"chart_id\": \"51fb648b-e5f8-4e71-bce9-764574304acc\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"fb680974-7123-439e-bccb-9c0347ab0295\", \"request_time\": \"2024-11-15T16:17:35.492605\", \"last_updated\": \"2024-11-15T16:17:35.492608\", \"user_query\": \" The user's primary intent is to analyze the average number of products per customer, specifically focusing on the marital status dimension, in order to gain insights into customer cross-sell performance.\", \"narrative\": \"Analyzing the average number of products per customer by marital status helps to understand customer cross-sell performance. This analysis can provide insights into the effectiveness of marketing strategies and product offerings for different customer segments. By examining the average number of products per customer across various marital statuses, businesses can identify opportunities to improve customer engagement and increase revenue through targeted marketing efforts.\", \"question\": \"What is the relationship between the number of dependents and the average number of products per customer by marital status?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": null, \"chart_title\": \"Number of Dependents vs. Average Number of Products per Customer by Marital Status\", \"chart_category\": \"relationship\", \"chart_type\": \"scatterplot_chart\", \"chart_position\": null, \"chart_axis\": null, \"sql_query\": null, \"status\": \"Fail\", \"chart_json\": null, \"module_version\": \"0.1.2\", \"db_tag\": null, \"total_inference_time\": null, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}",
    "{\"chart_id\": \"b2f345a2-c7a4-417b-a83f-16ebbfff3f58\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"fb680974-7123-439e-bccb-9c0347ab0295\", \"request_time\": \"2024-11-15T16:17:35.619400\", \"last_updated\": \"2024-11-15T16:17:35.619403\", \"user_query\": \" The user's primary intent is to analyze the average number of products per customer, specifically focusing on the marital status dimension, in order to gain insights into customer cross-sell performance.\", \"narrative\": \"To gain a deeper understanding of customer cross-sell performance, we need to analyze the average number of products per customer, with a focus on the marital status dimension. This will help us identify trends and patterns in customer behavior, enabling us to tailor our marketing strategies and improve customer engagement. By examining the average number of products per customer across different marital statuses, we can uncover insights that inform our business decisions and drive growth.\", \"question\": \"How does the average number of products per customer vary across different marital statuses and regions?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": null, \"chart_title\": \"Average Number of Products per Customer by Marital Status and Region\", \"chart_category\": \"comparison\", \"chart_type\": \"grouped_bar_chart\", \"chart_position\": null, \"chart_axis\": null, \"sql_query\": null, \"status\": \"Fail\", \"chart_json\": null, \"module_version\": \"0.1.2\", \"db_tag\": null, \"total_inference_time\": null, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}",
    "{\"chart_id\": \"6c528596-451b-42c7-869c-32953c33e682\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"fb680974-7123-439e-bccb-9c0347ab0295\", \"request_time\": \"2024-11-15T16:17:35.742641\", \"last_updated\": \"2024-11-15T16:17:35.742642\", \"user_query\": \" The user's primary intent is to analyze the average number of products per customer, specifically focusing on the marital status dimension, in order to gain insights into customer cross-sell performance.\", \"narrative\": \"Analyzing the average number of products per customer by marital status helps to understand customer cross-sell performance. This analysis can provide insights into the effectiveness of marketing strategies and product offerings for different customer segments. By examining the average number of products per customer across various marital statuses, businesses can identify opportunities to improve customer engagement and increase revenue through targeted marketing efforts.\", \"question\": \"How does the total product count vary among customers with different marital statuses?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": null, \"chart_title\": \"Total Product Count by Marital Status\", \"chart_category\": \"distribution\", \"chart_type\": \"histogram_chart\", \"chart_position\": null, \"chart_axis\": null, \"sql_query\": null, \"status\": \"Fail\", \"chart_json\": null, \"module_version\": \"0.1.2\", \"db_tag\": null, \"total_inference_time\": null, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}"
  ]
}
```

</details>

### GET /feedback/search/question/{question}

Search relevant chart samples based on question.

**Request Body**

- `question`: chart question query.

**Example Input:**

`What is the product penetration rate for debit cards across different income levels?`

**Responses:**

- Returns a JSON response suitable containing one or more chart data with its feedback which is/are relevant to the question query.

**Example Output:**

<details>
<summary>Sample Output JSON</summary>

```json
{
  "results": [
    "{\"chart_id\": \"442b2d55-b758-42a9-8b84-0f1a90251f68\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T15:46:11.319740\", \"last_updated\": \"2024-11-15T15:46:11.319743\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the product penetration rate for debit cards across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 5\", \"chart_title\": \"Debit Card Penetration Rate by Income Level\", \"chart_category\": \"comparison\", \"chart_type\": \"grouped_bar_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"income_level\", \"yAxis_title\": \"Debit Card Penetration Rate\", \"yAxis_column\": \"has_debit_card\", \"yAxis_aggregation\": \"COUNT\", \"yAxis2_title\": \"\", \"yAxis2_column\": \"\", \"yAxis2_aggregation\": \"\", \"yAxis3_title\": \"\", \"yAxis3_column\": \"\", \"yAxis3_aggregation\": \"\", \"series_title\": \"\", \"series_column\": \"\"}, \"sql_query\": \"SELECT income_level AS xAxis, COUNT(has_debit_card) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new WHERE has_debit_card = 'TRUE' GROUP BY income_level;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"xAxis\": \"Income Level\", \"yAxis\": \"Total Debit Card Penetration Rate\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Debit Card Penetration Rate by Income Level\", \"Chart_Axis\": {}, \"Chart_Size\": 120}, \"Aggregated_Table_Column\": [\"has_debit_card\", \"income_level\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 30.391773499999545, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"True\"}}",
    "{\"chart_id\": \"442b2d55-b758-42a9-8b84-0f1a90251f68\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T15:46:11.467266\", \"last_updated\": \"2024-11-15T15:46:11.467269\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the product penetration rate for debit cards across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 5\", \"chart_title\": \"Debit Card Penetration Rate by Income Level\", \"chart_category\": \"comparison\", \"chart_type\": \"grouped_bar_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"income_level\", \"yAxis_title\": \"Debit Card Penetration Rate\", \"yAxis_column\": \"has_debit_card\", \"yAxis_aggregation\": \"COUNT\", \"yAxis2_title\": \"\", \"yAxis2_column\": \"\", \"yAxis2_aggregation\": \"\", \"yAxis3_title\": \"\", \"yAxis3_column\": \"\", \"yAxis3_aggregation\": \"\", \"series_title\": \"\", \"series_column\": \"\"}, \"sql_query\": \"SELECT income_level AS xAxis, COUNT(has_debit_card) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new WHERE has_debit_card = 'TRUE' GROUP BY income_level;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"xAxis\": \"Income Level\", \"yAxis\": \"Total Debit Card Penetration Rate\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Debit Card Penetration Rate by Income Level\", \"Chart_Axis\": {}, \"Chart_Size\": 120}, \"Aggregated_Table_Column\": [\"has_debit_card\", \"income_level\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 30.391773499999545, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"True\"}}",
    "{\"chart_id\": \"0d87b1f1-865c-4d41-bf3c-1be606507bfc\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T15:46:11.648409\", \"last_updated\": \"2024-11-15T15:46:11.648412\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the product penetration rate for credit cards across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 2\", \"chart_title\": \"Credit Card Penetration Rate by Income Level\", \"chart_category\": \"comparison\", \"chart_type\": \"grouped_bar_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"income_level\", \"yAxis_title\": \"Credit Card Penetration Rate\", \"yAxis_column\": \"has_credit_card\", \"yAxis_aggregation\": \"COUNT\", \"yAxis2_title\": \"\", \"yAxis2_column\": \"\", \"yAxis2_aggregation\": \"\", \"yAxis3_title\": \"\", \"yAxis3_column\": \"\", \"yAxis3_aggregation\": \"\", \"series_title\": \"\", \"series_column\": \"\"}, \"sql_query\": \"SELECT income_level AS xAxis, COUNT(CASE WHEN has_credit_card = 'TRUE' THEN 1 END) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new GROUP BY income_level;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"xAxis\": \"Income Level\", \"yAxis\": \"Total Credit Card Penetration Rate\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Credit Card Penetration Rate by Income Level\", \"Chart_Axis\": {}, \"Chart_Size\": 120}, \"Aggregated_Table_Column\": [\"has_credit_card\", \"income_level\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 33.927351041988004, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}",
    "{\"chart_id\": \"1f0ca50d-121b-4623-a7ac-49ceff4d290a\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T15:46:12.024065\", \"last_updated\": \"2024-11-15T15:46:12.024067\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the product penetration rate for current accounts across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 3\", \"chart_title\": \"Current Account Penetration Rate by Income Level\", \"chart_category\": \"comparison\", \"chart_type\": \"grouped_bar_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"income_level\", \"yAxis_title\": \"Current Account Penetration Rate\", \"yAxis_column\": \"has_current_account\", \"yAxis_aggregation\": \"COUNT\", \"yAxis2_title\": \"\", \"yAxis2_column\": \"\", \"yAxis2_aggregation\": \"\", \"yAxis3_title\": \"\", \"yAxis3_column\": \"\", \"yAxis3_aggregation\": \"\", \"series_title\": \"\", \"series_column\": \"\"}, \"sql_query\": \"SELECT income_level AS xAxis, COUNT(CASE WHEN has_current_account = 'TRUE' THEN 1 END) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new GROUP BY income_level;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"xAxis\": \"Income Level\", \"yAxis\": \"Current Account Penetration Rate\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Current Account Penetration Rate by Income Level\", \"Chart_Axis\": {}, \"Chart_Size\": 120}, \"Aggregated_Table_Column\": [\"has_current_account\", \"income_level\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 32.37729849999596, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}",
    "{\"chart_id\": \"6c422aec-24eb-406c-b850-6e74af459e34\", \"user_id\": \"goldius.leo@userdata.tech\", \"session_id\": \"baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9\", \"request_time\": \"2024-11-15T15:46:12.733673\", \"last_updated\": \"2024-11-15T15:46:12.733674\", \"user_query\": \" The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.\", \"narrative\": \"To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.\", \"question\": \"What is the distribution of customers across different income levels?\", \"time_frame\": \"\", \"time_duration\": \"\", \"chart_name\": \"Visual 1\", \"chart_title\": \"Income Level Distribution\", \"chart_category\": \"distribution\", \"chart_type\": \"histogram_chart\", \"chart_position\": 1, \"chart_axis\": {\"xAxis_title\": \"Income Level\", \"xAxis_column\": \"age\"}, \"sql_query\": \"SELECT age AS xAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new;\", \"status\": \"Success\", \"chart_json\": {\"Subscription_ID\": \"\", \"Subscription_Name\": \"\", \"Shared_User_ID\": \"\", \"Chart_SQL_Library\": \"MySQL\", \"Number_of_Bins\": {\"sqrt\": 1069, \"sturges\": 22, \"rice\": 210}, \"xAxis\": \"Income Level\", \"yAxis\": \"Frequency\", \"Aggregated_Table_JSON\": {\"Visual_Title\": \"Income Level Distribution\", \"Chart_Axis\": {}, \"Chart_Size\": 9504856}, \"Aggregated_Table_Column\": [\"age\"], \"Database_Identifier\": \"label1\"}, \"module_version\": \"0.1.0\", \"db_tag\": \"label1\", \"total_inference_time\": 29.657983790995786, \"feedback\": {\"chart_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_title\": {\"selected_options\": [], \"other\": \"\"}, \"xaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"yaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"zaxis_data\": {\"selected_options\": [], \"other\": \"\"}, \"overall_chart\": {\"selected_options\": [], \"other\": \"\"}, \"like\": \"False\"}}"
  ]
}
```

</details>

### GET /feedback/chart_id/{chart_id}

Get feedback data for specified chart id.

**Request Body:**

- `chart_id`: ID of chart.

**Example Input:**

`442b2d55-b758-42a9-8b84-0f1a90251f68`

**Example Output:**

<details>
<summary>Sample Output JSON</summary>

```json
{
  "chart_id": "442b2d55-b758-42a9-8b84-0f1a90251f68",
  "chart_data": {
    "chart_id": "442b2d55-b758-42a9-8b84-0f1a90251f68",
    "user_id": "goldius.leo@userdata.tech",
    "session_id": "baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9",
    "request_time": "2024-11-12T11:51:59.560000",
    "last_updated": "2024-11-12T11:53:15.936000",
    "user_query": " The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.",
    "narrative": "To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.",
    "question": "What is the product penetration rate for debit cards across different income levels?",
    "time_frame": "",
    "time_duration": "",
    "chart_name": "Visual 5",
    "chart_title": "Debit Card Penetration Rate by Income Level",
    "chart_category": "comparison",
    "chart_type": "grouped_bar_chart",
    "chart_position": 1,
    "chart_axis": {
      "xAxis_title": "Income Level",
      "xAxis_column": "income_level",
      "yAxis_title": "Debit Card Penetration Rate",
      "yAxis_column": "has_debit_card",
      "yAxis_aggregation": "COUNT",
      "yAxis2_title": "",
      "yAxis2_column": "",
      "yAxis2_aggregation": "",
      "yAxis3_title": "",
      "yAxis3_column": "",
      "yAxis3_aggregation": "",
      "series_title": "",
      "series_column": ""
    },
    "sql_query": "SELECT income_level AS xAxis, COUNT(has_debit_card) / COUNT(*) * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new WHERE has_debit_card = 'TRUE' GROUP BY income_level;",
    "status": "Success",
    "chart_json": {
      "Subscription_ID": "",
      "Subscription_Name": "",
      "Shared_User_ID": "",
      "Chart_SQL_Library": "MySQL",
      "xAxis": "Income Level",
      "yAxis": "Total Debit Card Penetration Rate",
      "Aggregated_Table_JSON": {
        "Visual_Title": "Debit Card Penetration Rate by Income Level",
        "Chart_Axis": {},
        "Chart_Size": 120
      },
      "Aggregated_Table_Column": [
        "has_debit_card",
        "income_level"
      ],
      "Database_Identifier": "label1"
    },
    "module_version": "0.1.0",
    "db_tag": "label1",
    "total_inference_time": 30.391773499999545
  }
}
```

</details>

### POST /streaming/GraphUpsSummary/d3

Generates charts based on the provided input parameters and streams the response for real-time data visualization using D3.js library.

**Request Body:**

- `input_list`: A list of input parameters. The structure depends on the flow, whether `table join flow` or `non-table join flow`.

**Example Input:**

<details>
<summary>Non-Table Join Flow</summary>

<br>**Index 0:** Database name + table name<br>**Index 1:** Database Identifier to obtain database credential and database language<br>**Index 2:** Summarized user Intent<br>**Index 3:** Filter by column with its respective value<br>**Index 4:** Group by column<br>**Index 5:** Client ID<br>**Index 6:** User ID<br>**Index 7:** Session ID

```json
[
    "ada_banks_data_asset.product_gap_new",
    "label1",
    " The user's primary intent is to obtain advice from ADA, the virtual assistant, on strategies for handling orphan products. They specifically want to know what offers to make to customers who own such products. The user has expressed a preference for filtering data related to this issue by 'marital status', indicating an interest in segmenting their customer base according to this criterion.",
    {"gender": ["male"]},
    ["marital_status"],
    "\"starhub_001\"",
    "\"choong.yh@userdata.tech\"",
    "\"c4a72b20-3136-406f-bd5f-408a8e077e4e\"",
]
```

</details>

<details>
<summary>Table Join Flow</summary>

<br>**Index 0:** Summarized user Intent<br>**Index 1:** Session ID<br>**Index 2:** Client ID<br>**Index 3:** User ID<br>**Index 4:** Brahmaputra Reply Response (Not Used by Saraswathi agent)

```json
[
    "I want to get customer transaction analysis",
    "c4a72b20-3136-406f-bd5f-408a8e077e4e",
    "starhub_001",
    "goldius.leo@userdata.tech",
    "I'd be happy to assist you with customer transaction analysis. To provide a comprehensive analysis, I'll need to join the necessary tables. Please note that this may take some time.\n\nOnce completed, I will generate relevant charts and insights to help you better understand your customers' transaction patterns. You can expect to see information on:\n\n* Customer demographics\n* Transaction frequency and value\n* Product popularity and trends\n* Geographic distribution of customers\n\nPlease stand by while I work on generating the analysis. I'll",
]
```

`Blue River` agent output contains joined table level metadata, joined table column level metadata. Below is the JSON sample of `Blue River` agent output.

```json
[
    {
        "Table_A": "blueriver_rdbms.trx_07_data",
        "Table_B": "blueriver_rdbms.customer_05_2024",
        "Join_Key": "customer_ID",
        "Join_Type": "LEFT JOIN",
        "SQL_Query": "SELECT blueriver_rdbms.trx_07_data.account_id, blueriver_rdbms.trx_07_data.account_type, blueriver_rdbms.trx_07_data.branch_name, blueriver_rdbms.trx_07_data.customer_ID, blueriver_rdbms.trx_07_data.first_name, blueriver_rdbms.trx_07_data.last_name, blueriver_rdbms.trx_07_data.transaction_amount, blueriver_rdbms.trx_07_data.transaction_date, blueriver_rdbms.trx_07_data.transaction_description, blueriver_rdbms.trx_07_data.transaction_id, blueriver_rdbms.trx_07_data.transaction_type, COALESCE(blueriver_rdbms.customer_05_2024.bank_account_id, NULL) AS bank_account_id, COALESCE(blueriver_rdbms.customer_05_2024.company_name, NULL) AS company_name, COALESCE(blueriver_rdbms.customer_05_2024.email, NULL) AS email, COALESCE(blueriver_rdbms.customer_05_2024.gender, NULL) AS gender, COALESCE(blueriver_rdbms.customer_05_2024.job_title, NULL) AS job_title FROM blueriver_rdbms.trx_07_data LEFT JOIN blueriver_rdbms.customer_05_2024 ON blueriver_rdbms.trx_07_data.customer_ID = blueriver_rdbms.customer_05_2024.customer_ID;",
        "Database_Name": "MySQL",
        "Table_Relation": "PK",
        "Confidence_Rank": 1,
        "Confidence_Score": 0.7238618537278425,
        "Table_A_Name_noDB": "trx_07_data",
        "Table_B_Name_noDB": "customer_05_2024",
        "Table_Level_Metadata": [
            {
                "source": "N/A",
                "table_name": "trx_07_data",
                "table_type": "FACT",
                "column_list": "account_id|account_type|branch_name|customer_ID|first_name|last_name|transaction_amount|transaction_date|transaction_description|transaction_id|transaction_type",
                "foreign_key": "N/A",
                "primary_key": "N/A",
                "table_match": "blueriver_rdbms.trx_07_data",
                "database_name": "blueriver_rdbms",
                "row_description": " The row represents an online transaction of $99,267.67 from the Nantes branch by Maryjo Ellingsworth (customer ID 73-3680662) on June 12, 2023, which was a withdrawal, as indicated by the transaction type.",
                "number_of_columns": "11",
                "sql_database_name": "MySQL",
                "table_description": " The \"trx_07_data\" table is a fact table that captures detailed transaction data for July, encompassing account, customer, and transaction-related information. It includes essential identifiers such as account ID, account type, branch name, customer ID, first name, last name, and transaction type. The table records transaction amounts and dates, along with descriptions, providing a comprehensive view of transaction activities. This table is instrumental in generating transaction-based reports, facilitating financial analysis, and supporting strategic decision-making for the specified period. This table contains transactional data with columns for account information (account_id, account_type, branch_name), customer identification (customer_ID, first_name, last_name), and transaction details (transaction_amount, transaction_date, transaction_description, transaction_type). The KPIs that can be calculated from this table include Customer Payment Performance, Accounts Receivable Aging Report, Average Billing Amount per Customer, and Customer Segmentation based on interests.",
                "database_identifier": "label1",
                "last_metadata_update": "2024-07-16 13:05:57",
                "table_short_description": " The \"trx_07_data\" table is a fact table capturing detailed transaction data for July, including account, customer, and transaction-related information. This table is essential for generating transaction-based reports, facilitating financial analysis, and supporting strategic decision-making, with KPIs such as Customer Payment Performance and Accounts Receivable Aging Report.",
            },
            {
                "source": "N/A",
                "table_name": "customer_05_2024",
                "table_type": "DIMENSION",
                "column_list": "bank_account_id|company_name|customer_ID|email|first_name|gender|job_title|last_name",
                "foreign_key": "N/A",
                "primary_key": "N/A",
                "table_match": "blueriver_rdbms.customer_05_2024",
                "database_name": "blueriver_rdbms",
                "row_description": " The row represents a customer, Sheelagh Harral, with ID 45-9343936, associated with company 9936, and fhaving the email [sharral1@earthlink.net](mailto:sharral1@earthlink.net). She is a female Environmental Tech and her gender is BZNJ, with the bank account ID FR10 and last name Harral.",
                "number_of_columns": "8",
                "sql_database_name": "MySQL",
                "table_description": " The \"customer_05_2024\" table is a dimension table that stores detailed customer information for May 2024, including bank account IDs, company names, customer IDs, email addresses, first and last names, job titles, and genders. This table is essential for maintaining an up-to-date customer database for the specified month, aiding in personalized marketing, customer relationship management, and sales analytics. By providing comprehensive customer profiles, it supports targeted customer analysis and strategic decision-making for May 2024. This table is a crucial component for understanding customer demographics and behavior, enabling organizations to optimize their marketing strategies and improve overall customer satisfaction. This table contains customer information with the following columns: Bank_Account_ID, company_name, customer_ID, email, first_name, gender, job_title, and last_name. The KPIs that can be calculated from this table include Customer Payment Performance, Accounts Receivable Aging Report, Average Billing Amount per Customer, and Customer Segmentation (Interests).",
                "database_identifier": "label1",
                "last_metadata_update": "2024-07-16 13:05:57",
                "table_short_description": " The \"customer_05_2024\" table is a dimension table that stores detailed customer information for May 2024, enabling targeted customer analysis and strategic decision-making. It provides comprehensive customer profiles, aiding in personalized marketing, customer relationship management, and sales analytics, and allows for calculating KPIs such as Customer Payment Performance and Accounts Receivable Aging Report.",
            },
        ],
        "Column_Level_Metadata": [
            {
                "n_unique": 966,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": 375081948390421900,
                "max_value": 6771676543769412000,
                "min_value": 4017950000000,
                "row_count": 1000,
                "std_value": 1365162670797093600,
                "10_samples": "4017950000000|4041380000000|4041590000000|4041600000000|4064400000000|4416010000000|4952670000000|30018300000000|30023900000000|30024500000000",
                "data_tribe": "id",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "double",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "",
                "column_description": "Account ID",
                "cleaned_column_name": "account_id",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 0.966,
                "original_sql_column_name": "account_id",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.account_id",
            },
            {
                "n_unique": 10,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "basic|business|corporate|current|joint|online|personal|retirement|savings|student",
                "data_tribe": "categorical",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Payment Performance, Acounts Receivable Aging Report, Average Billing Amount per Customer",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "",
                "column_description": "Account Type",
                "cleaned_column_name": "account_type",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "Has_Current_Account_Flag",
                "n_unique_per_row_count": 0.01,
                "original_sql_column_name": "account_type",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.account_type",
            },
            {
                "n_unique": 984,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "‘Aqrah|Afareaitu|Aghada|Agía Varvára|Ágios Spyrídon|Água Retorta|Aimorés|Aix-en-Provence|Aiximan|Akureyri",
                "data_tribe": "categorical",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "",
                "column_description": "Branch Name",
                "cleaned_column_name": "branch_name",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 0.984,
                "original_sql_column_name": "branch_name",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.branch_name",
            },
            {
                "n_unique": 1000,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "00-1662667|00-3418626|00-4722195|00-5362154|00-5585088|00-5655982|00-6292647|00-6881844|00-7943937|00-7997137",
                "data_tribe": "id",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "",
                "column_description": "Customer ID",
                "cleaned_column_name": "customer_ID",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 1,
                "original_sql_column_name": "customer_ID",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.customer_ID",
            },
            {
                "n_unique": 950,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "Aaren|Abby|Abe|Ada|Adelaida|Adelind|Adlai|Adolf|Adrea|Adriaens",
                "data_tribe": "categorical",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "",
                "column_description": "First Name",
                "cleaned_column_name": "first_name",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 0.95,
                "original_sql_column_name": "first_name",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.first_name",
            },
            {
                "n_unique": 986,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "Abbati|Abrahamsson|Abrams|Ackenhead|Adame|Adamiak|Adamsen|Adriaens|Aim|Aitchison",
                "data_tribe": "categorical",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "",
                "column_description": "Last Name",
                "cleaned_column_name": "last_name",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 0.986,
                "original_sql_column_name": "last_name",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.last_name",
            },
            {
                "n_unique": 1000,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "$10114.83|$10386.81|$10522.75|$10574.60|$10767.90|$10774.89|$10821.90|$10828.69|$10949.39|$11266.24",
                "data_tribe": "numerical",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Payment Performance, Acounts Receivable Aging Report, Average Billing Amount per Customer",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "",
                "column_description": "Transaction Amount",
                "cleaned_column_name": "transaction_amount",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "Transaction_Channel",
                "n_unique_per_row_count": 1,
                "original_sql_column_name": "transaction_amount",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.transaction_amount",
            },
            {
                "n_unique": 596,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "01/01/2023|01/01/2024|01/02/2023|01/02/2024|01/03/2022|01/03/2023|01/03/2024|01/04/2022|01/05/2024|01/06/2022",
                "data_tribe": "date_related",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "",
                "column_description": "Transaction Date",
                "cleaned_column_name": "transaction_date",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "Industry",
                "n_unique_per_row_count": 0.596,
                "original_sql_column_name": "transaction_date",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.transaction_date",
            },
            {
                "n_unique": 22,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "Automotive|Baby|Beauty|Books|Clothing|Computers|Electronics|Games|Garden|Grocery",
                "data_tribe": "categorical",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Payment Performance, Acounts Receivable Aging Report, Average Billing Amount per Customer",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "",
                "column_description": "Transaction Description",
                "cleaned_column_name": "transaction_description",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "Transaction_Channel",
                "n_unique_per_row_count": 0.022,
                "original_sql_column_name": "transaction_description",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.transaction_description",
            },
            {
                "n_unique": 1000,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "AD29 6650 2328 YTPS WRLO VLQN|AD54 6453 8754 6ZFA YXOP TMAW|AD62 7546 5974 YN6G AFJ0 IK6J|AD69 0563 0984 AV0T FRBA WWMR|AD71 8115 8430 7ZMA OLJQ J3RT|AD77 9386 3661 CASI JVIN WP0M|AD82 8103 2448 WFUE XCSW ZAEJ|AD85 6098 7347 IMRF P4LS 5IAC|AD96 7383 4000 AXLH ICZR 84FD|AE11 7305 4601 5159 2238 126",
                "data_tribe": "id",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "",
                "column_description": "Transaction ID",
                "cleaned_column_name": "transaction_id",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "Transactions_Type",
                "n_unique_per_row_count": 1,
                "original_sql_column_name": "transaction_id",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.transaction_id",
            },
            {
                "n_unique": 10,
                "sql_path": "blueriver_rdbms.trx_07_data",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "deposit|donation|exchange|fee|loan|purchase|refund|subscription|transfer|withdrawal",
                "data_tribe": "categorical",
                "table_name": "trx_07_data",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "Transaction Type, a categorical value that describes the type of financial transaction, such as deposit, donation, exchange, fee, loan, purchase, refund, subscription, transfer, or withdrawal.",
                "column_description": "Transaction Type",
                "cleaned_column_name": "transaction_type",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "Transactions_Type",
                "n_unique_per_row_count": 0.01,
                "original_sql_column_name": "transaction_type",
                "sql_path_original_column_name": "blueriver_rdbms.trx_07_data.transaction_type",
            },
            {
                "n_unique": 1000,
                "sql_path": "blueriver_rdbms.customer_05_2024",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "AD05 9959 2223 FWEC XJR4 QKGI|AD14 4707 7001 1ZVZ IRSY XPDN|AD17 3872 7448 BGSG 6ADT OGAB|AD25 0190 8133 63HC LHXW XWXQ|AD27 3598 0778 8JBK V9VC ZLNK|AD31 6483 0114 YD6U OTM5 N5NG|AD35 0143 4996 VN73 CD6K QIHV|AD55 6367 6729 ORHL Z2IE VFUI|AD70 2464 9693 2AU1 APBU WVCS|AD74 9377 4714 0QN9 LIXG UYWJ",
                "data_tribe": "id",
                "table_name": "customer_05_2024",
                "kpi_def_from": "Customer Payment Performance, Acounts Receivable Aging Report, Average Billing Amount per Customer",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "Bank Account ID is a unique identifier for a customer's bank account, consisting of a combination of letters and numbers, which is used to facilitate financial transactions.",
                "column_description": "Bank Account ID",
                "cleaned_column_name": "bank_account_id",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "Has_Current_Account_Flag",
                "n_unique_per_row_count": 1,
                "original_sql_column_name": "bank_account_id",
                "sql_path_original_column_name": "blueriver_rdbms.customer_05_2024.bank_account_id",
            },
            {
                "n_unique": 362,
                "sql_path": "blueriver_rdbms.customer_05_2024",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "Abata|Agimba|Aibox|Ailane|Aimbo|Aimbu|Ainyx|Aivee|Avamba|Avamm",
                "data_tribe": "categorical",
                "table_name": "customer_05_2024",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "Company Name refers to the name of the company where the customer is employed, providing context for the customer's job title and role.",
                "column_description": "Company Name",
                "cleaned_column_name": "company_name",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "Industry",
                "n_unique_per_row_count": 0.362,
                "original_sql_column_name": "company_name",
                "sql_path_original_column_name": "blueriver_rdbms.customer_05_2024.company_name",
            },
            {
                "n_unique": 1000,
                "sql_path": "blueriver_rdbms.customer_05_2024",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "00-1033717|00-1499639|00-1537576|00-2364491|00-2435085|00-2602569|00-3463157|00-6079924|00-6843781|00-6930131",
                "data_tribe": "id",
                "table_name": "customer_05_2024",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "Customer ID is a unique identifier assigned to each customer, allowing for easy tracking and management of customer information and transactions.",
                "column_description": "Customer ID",
                "cleaned_column_name": "customer_ID",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 1,
                "original_sql_column_name": "customer_ID",
                "sql_path_original_column_name": "blueriver_rdbms.customer_05_2024.customer_ID",
            },
            {
                "n_unique": 1000,
                "sql_path": "blueriver_rdbms.customer_05_2024",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "aaxcell8q@dagondesign.com|abaldingq@jalbum.net|abanbrookgz@a8.net|abantingh2@desdev.cn|abishopppg@boston.com|aboakesoj@rakuten.co.jp|abroseman9h@google.pl|abubbinsqs@twitpic.com|acamelian9@umich.edu|acaserls@sohu.com",
                "data_tribe": "textual",
                "table_name": "customer_05_2024",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "Email is the electronic mail address of the customer, used for communication and electronic transactions.",
                "column_description": "Email",
                "cleaned_column_name": "email",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 1,
                "original_sql_column_name": "email",
                "sql_path_original_column_name": "blueriver_rdbms.customer_05_2024.email",
            },
            {
                "n_unique": 946,
                "sql_path": "blueriver_rdbms.customer_05_2024",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "Aarika|Ab|Abdel|Abigale|Abram|Adah|Adelice|Adriaens|Adrianne|Adriano",
                "data_tribe": "categorical",
                "table_name": "customer_05_2024",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "First Name is the given name of the customer, representing the initial part of their personal identity.",
                "column_description": "First Name",
                "cleaned_column_name": "first_name",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 0.946,
                "original_sql_column_name": "first_name",
                "sql_path_original_column_name": "blueriver_rdbms.customer_05_2024.first_name",
            },
            {
                "n_unique": 8,
                "sql_path": "blueriver_rdbms.customer_05_2024",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "Agender|Bigender|Female|Genderfluid|Genderqueer|Male|Non-binary|Polygender",
                "data_tribe": "categorical",
                "table_name": "customer_05_2024",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "Gender is the self-identified gender of the customer, which can include various categories such as Female, Male, Agender, Bigender, Genderfluid, Genderqueer, Non-binary, Polygender, etc.",
                "column_description": "Gender",
                "cleaned_column_name": "gender",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 0.008,
                "original_sql_column_name": "gender",
                "sql_path_original_column_name": "blueriver_rdbms.customer_05_2024.gender",
            },
            {
                "n_unique": 180,
                "sql_path": "blueriver_rdbms.customer_05_2024",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "Account Coordinator|Account Executive|Account Representative I|Account Representative II|Account Representative III|Account Representative IV|Accountant I|Accountant III|Accountant IV|Accounting Assistant I",
                "data_tribe": "categorical",
                "table_name": "customer_05_2024",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "Job Title is the official title of the customer's position within their company, reflecting their role and responsibilities.",
                "column_description": "Job Title",
                "cleaned_column_name": "job_title",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 0.18,
                "original_sql_column_name": "job_title",
                "sql_path_original_column_name": "blueriver_rdbms.customer_05_2024.job_title",
            },
            {
                "n_unique": 989,
                "sql_path": "blueriver_rdbms.customer_05_2024",
                "avg_value": "None",
                "max_value": "None",
                "min_value": "None",
                "row_count": 1000,
                "std_value": "None",
                "10_samples": "Abelov|Abelovitz|Abethell|Achromov|Adnams|Adolfsen|Adshede|Advani|Akester|Albany",
                "data_tribe": "categorical",
                "table_name": "customer_05_2024",
                "kpi_def_from": "Customer Segmentation (Career)",
                "database_name": "blueriver_rdbms",
                "sql_data_type": "text",
                "sql_tool_name": "MySQL",
                "pct_null_values": 0,
                "possible_values": "None",
                "long_description": "Last Name is the family name or surname of the customer, representing the final part of their personal identity.",
                "column_description": "Last Name",
                "cleaned_column_name": "last_name",
                "data_dictionary_flag": "None",
                "final_kpi_column_match": "customer_ID",
                "n_unique_per_row_count": 0.989,
                "original_sql_column_name": "last_name",
                "sql_path_original_column_name": "blueriver_rdbms.customer_05_2024.last_name",
            },
        ],
        "Combined_LLM_Description": "This table is a comprehensive data asset, merging transaction data from 'trx_07_data' with customer information from 'customer_05_2024'. It facilitates in-depth transactional and customer analysis, supporting strategic decision-making and enhancing financial, marketing, and sales performance insights.",
    }
]
```

</details>

<br>

**Responses:**
- Returns a streamed JSON response suitable for D3.js library visualizations.

**Example Output:**

<details>
<summary>Sample Output JSON</summary>

```json
[
    {
        "Subscription_ID": "",
        "Subscription_Name": "",
        "Client_ID": "starhub_001",
        "User_ID": "ahmedalla@userdata.tech",
        "Shared_User_ID": "",
        "Chart_Name": "Visual 1",
        "Visual_Title": "Overall Product Penetration Rate for Current Account Holders",
        "Chart_Axis": {
            "xAxis_title": "Income Level",
            "xAxis_column": "income_level",
            "yAxis_title": "Overall Product Penetration Rate",
            "yAxis_column": "has_current_account",
            "yAxis_aggregation": "COUNT"
        },
        "Chart_Data": [
            {
                "Group_Name": "Low Income",
                "Y_Value": 20.9772
            },
            {
                "Group_Name": "High Income",
                "Y_Value": 20.0268
            },
            {
                "Group_Name": "Very Low Income",
                "Y_Value": 20.0066
            },
            {
                "Group_Name": "Upper-Middle Income",
                "Y_Value": 19.9961
            },
            {
                "Group_Name": "Lower-Middle Income",
                "Y_Value": 18.9932
            }
        ],
        "Chart_Query": "SELECT income_level AS xAxis, COUNT(has_current_account) / (SELECT COUNT(has_current_account) FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new WHERE has_loan = 'true') * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new WHERE has_loan = 'true' GROUP BY income_level;",
        "Chart_SQL_Library": "MySQL",
        "Chart_Position": "1",
        "Chart_Type": "pie_chart",
        "Chart_Title": "Overall Product Penetration Rate for Current Account Holders",
        "xAxis": "Income Level",
        "yAxis": "Overall Product Penetration Rate",
        "Aggregated_Table_JSON": {
            "Subscription_ID": "",
            "Subscription_Name": "",
            "Client_ID": "starhub_001",
            "User_ID": "ahmedalla@userdata.tech",
            "Shared_User_ID": "",
            "Chart_Name": "Visual 1",
            "Chart_Axis": {},
            "Chart_Query": "SELECT income_level AS xAxis, COUNT(has_current_account) / (SELECT COUNT(has_current_account) FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new WHERE has_loan = 'true') * 100 AS yAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new WHERE has_loan = 'true' GROUP BY income_level;",
            "Chart_SQL_Library": "MySQL",
            "Chart_Position": "1",
            "Chart_Type": "aggregated_table_chart",
            "Chart_Size": 120,
            "data": [
                {
                    "Income Level": "High Income",
                    "Overall Product Penetration Rate": 20.0268
                },
                {
                    "Income Level": "Low Income",
                    "Overall Product Penetration Rate": 20.9772
                },
                {
                    "Income Level": "Lower-Middle Income",
                    "Overall Product Penetration Rate": 18.9932
                },
                {
                    "Income Level": "Upper-Middle Income",
                    "Overall Product Penetration Rate": 19.9961
                },
                {
                    "Income Level": "Very Low Income",
                    "Overall Product Penetration Rate": 20.0066
                }
            ],
            "Database_Identifier": "label1"
        },
        "Aggregated_Table_Column": [
            "income_level",
            "has_current_account"
        ],
        "Database_Identifier": "label1",
        "yName": "Overall Product Penetration Rate"
    },
    {
        "Subscription_ID": "",
        "Subscription_Name": "",
        "Client_ID": "starhub_001",
        "User_ID": "ahmedalla@userdata.tech",
        "Shared_User_ID": "",
        "Chart_Name": "Visual 1",
        "Chart_Type": "text_content",
        "Chart_Position": "2",
        "Chart_Title": "Visual Description",
        "Card_Content": "* The 'Low Income' group has the highest overall product penetration rate for current account holders, at approximately 21%.\n* The 'High Income' group has a slightly lower overall product penetration rate, at around 20%, compared to the 'Low Income' group.\n* The 'Lower-Middle Income' group has the lowest overall product penetration rate, at approximately 19%, which is roughly 1% lower than the 'Upper-Middle Income' and 'Very Low Income' groups."
    },
    {
        "Subscription_ID": "",
        "Subscription_Name": "",
        "Client_ID": "starhub_001",
        "User_ID": "ahmedalla@userdata.tech",
        "Shared_User_ID": "",
        "Chart_Name": "Visual 1",
        "Chart_Type": "text_content",
        "Chart_Position": "3",
        "Chart_Title": "Business Recommendation",
        "Card_Content": "Based on the chart data, we observe a relatively flat product penetration rate across all income levels, with 'Low Income' and 'High Income' groups showing the highest rates. This suggests that cross-selling performance is not strongly correlated with income level. To improve cross-selling, focus on targeting 'Low Income' and 'High Income' groups, and explore other demographic factors that may influence cross-selling propensity, such as age or occupation, to identify new opportunities."
    }
]
```

</details>

### PUT /chart-llm-calls

Logs details of LLM calls associated with a chart.

**Request Body:**

- `chart_id`: str — The unique identifier for the chart being logged.
- `module_id`: int — The identifier for the module.
- `user_prompts`: str — The user prompts sent to the LLM.
- `system_prompts`: str — The system prompts sent to the LLM.
- `output`: str — The model’s output based on the prompts.
- `inference_time`: float — The time taken by the model for inference.
- `llm_model`: str — The name of the LLM model used.

**Example Input:**

<details>
<summary>Sample Input</summary>

```json
{
  "chart_id": "7dda9677-8ce9-4221-abb7-a1bbdf3c3a53",
  "module_id": 5,
  "user_prompts": "Please sort this ['Divorced', 'Married', 'Single', 'Widowed']",
  "system_prompts": "Sort the given list in chronological order and return only the sorted list as a Python list, without any explanations.",
  "output": "['Divorced', 'Married', 'Single', 'Widowed']",
  "inference_time": 0.6636304590000037,
  "llm_model": "hugging-quants/Meta-Llama-3.1-70B-Instruct-AWQ-INT4",
}
```
</details><br/> 

**Responses:**
- Returns a JSON object containing the logging status and message.

**Example Output:**

<details>
<summary>Sample Output JSON</summary>

```json
{
  "status": "success",
  "message": "LLM call entry logged successfully."
}
```
</details>

### GET /module-id/{module_id}

Retrieves module name by its unique module_id.

**Request Body:**

- `module_id`: int - The unique identifier of the module to retrieve.

**Example Input:**

<details>
<summary>Sample Input</summary>

```json
{
  "module_id": 1,
}
```
</details><br/>

**Responses:**
- Returns a JSON object containing the module_id and the corresponding module_name.

**Example Output:**

<details>
<summary>Sample Output JSON</summary>

```json
{
  "module_id": 1,
  "module_name": "generate_narrative_question_d3"
}
```
</details>

### GET /module-name/{module_name}

Retrieves module_id by its module_name.

**Request Body:**

- `module_name`: str - The name of the module to retrieve.

**Example Input:**

<details>
<summary>Sample Input</summary>

```json
{
  "module_name": "generate_narrative_question_d3"
}
```
</details><br/>

**Responses:**
- Returns a JSON object containing the module_name and the corresponding module_id.

**Example Output:**

<details>
<summary>Sample Output JSON</summary>

```json
{
  "module_id": 1,
  "module_name": "generate_narrative_question_d3"
}
```
</details>

### GET /chart/{chart_id}

Retrieves chart data by its chart_id.

**Request Body:**

- `chart_id`: str - The unique identifier for the chart.

**Example Input:**

<details>
<summary>Sample Input</summary>

```json
{
  "chart_id": "7dda9677-8ce9-4221-abb7-a1bbdf3c3a53"
}
```
</details><br/>

**Responses:**
- Returns a JSON object containing the chart logging data.

**Example Output:**

<details>
<summary>Sample Output JSON</summary>

```json
{
  "_id": {
    "$oid": "6732d0df15c3bdfa067c1ce5"
  },
  "chart_id": "6c422aec-24eb-406c-b850-6e74af459e34",
  "user_id": "goldius.leo@userdata.tech",
  "session_id": "baff16cf-21ab-48f5-b5bc-e1dfd3b6d5a9",
  "request_time": {
    "$date": "2024-11-12T11:51:59.130Z"
  },
  "last_updated": {
    "$date": "2024-11-12T11:52:12.876Z"
  },
  "user_query": " The user's primary intent is to analyze the product penetration rate with a focus on the 'income level' dimension. They have requested information on customer financial product usage, relationships, and demographics, and are expecting a data asset visualization from the virtual assistant, ADA, to gain insights on this specific aspect.",
  "narrative": "To analyze the product penetration rate with a focus on the 'income level' dimension, we will examine the usage of various financial products across different income levels. This will provide insights into customer financial behavior and demographics, enabling the identification of trends and patterns in product adoption. By visualizing the data, we can gain a better understanding of how income level influences product penetration rates, and identify opportunities to tailor financial products to specific customer segments.",
  "question": "What is the distribution of customers across different income levels?",
  "time_frame": "",
  "time_duration": "",
  "chart_name": "Visual 1",
  "chart_title": "Income Level Distribution",
  "chart_category": "distribution",
  "chart_type": "histogram_chart",
  "chart_position": 1,
  "chart_axis": {
    "xAxis_title": "Income Level",
    "xAxis_column": "age"
  },
  "sql_query": "SELECT age AS xAxis FROM ada_banks_data_asset.report_cross_selling_performance_product_type_new;",
  "status": "Success",
  "chart_json": {
    "Subscription_ID": "",
    "Subscription_Name": "",
    "Shared_User_ID": "",
    "Chart_SQL_Library": "MySQL",
    "Number_of_Bins": {
      "sqrt": 1069,
      "sturges": 22,
      "rice": 210
    },
    "xAxis": "Income Level",
    "yAxis": "Frequency",
    "Aggregated_Table_JSON": {
      "Visual_Title": "Income Level Distribution",
      "Chart_Axis": {},
      "Chart_Size": 9504856
    },
    "Aggregated_Table_Column": [
      "age"
    ],
    "Database_Identifier": "label1"
  },
  "module_version": "0.1.0",
  "db_tag": "label1",
  "total_inference_time": 29.657983790995786
}
```
</details>


### Chart JSON Output Format

JSON output for each chart type are stored in `json_samples` for Apex library and `d3_json_samples` for D3.js library.

### Environment Variables

- `CHROMA_DB_USERNAME`: Chroma DB username.
- `CHROMA_DB_PASSWORD`: Chroma DB password.
- `CHROMA_DB_HOST`: Chroma DB host IP/URL.
- `CHROMA_DB_PORT`: Chroma DB host port.
- `CHROMA_DB_TABLE_NAMESPACE`: Table level chroma DB namespace.
- `CHROMA_DB_COLUMN_NAMESPACE`: Column level chroma DB namespace.
- `MIXTRAL_LLM_BASE_URL`: LLM API URL.
- `MIXTRAL_LLM_API_KEY`: LLM API key.
- `MIXTRAL_MODEL`: LLM model name.
- `EMBEDDING_BASE_URL`: Embedding model API URL.
- `CLIENT_DB`: List of dictionary containing database credentials with its database identifier.
- `BRAHMAPUTRA_DB`: Databased used by Brahmaputra to store `Blue River` agent output.
- `COMPANY_NAME`: Client's company name.
- `INDUSTRY_DOMAIN`: Client's industry domain.
  
## Project Structure

```
saraswathi/
│   spliter/
│   ├── __init__.py
│   └── client_splitter.py
├── requirements-streaming-dummy.txt
├── tools/
│   ├── sql_inference.ipynb
│   ├── .DS_Store
│   ├── concurrent_user_testing.py
│   ├── db_migration/
│   │   ├── verify_db.py
│   │   └── migrate_db.py
│   ├── chromadb_check.ipynb
│   ├── inference_sample.ipynb
│   └── API_test.ipynb
├── run_testcase_json_no_llm_evaluation_new_flow_streaming.py
├── .DS_Store
├── run_testcase_json_no_llm_evaluation_new_flow_streaming_postgresql.py
├── requirements.txt
├── streaming_fastapi_dummy_v40.py
├── CHANGELOG.md
├── .pre-commit-config.yaml
├── Dockerfile
├── run_testcase_json_no_llm_evaluation_new_flow_postgresql.py
├── run_testcase_json_no_llm_evaluation_new_flow.py
├── Saraswati v1.1.0 - ADA Release Notes.docx
├── test.py
├── input_output_sample/
│   ├── sample_output_saraswati_semi_finalized_mvp2_starhub.json
│   ├── streaming_output.txt
│   ├── JSON_updater_API_sample.py
│   ├── input.txt
│   └── sample_output_saraswati_semi_finalized_mvp2_starhub_6_visuals.json
├── README.md
├── components/
│   ├── story.py
│   ├── axis.py
│   ├── .DS_Store
│   ├── postprocess.py
│   ├── sql_query.py
│   ├── datamodel.py
│   ├── question.py
│   ├── __init__.py
│   ├── utils/
│   │   ├── validator.py
│   │   ├── token.py
│   │   ├── pandas.py
│   │   ├── __init__.py
│   │   ├── chart.py
│   │   ├── brahmaputra_retrieval.py
│   │   ├── prompt.py
│   │   └── general.py
│   ├── updater/
│   │   ├── __init__.py
│   │   └── general.py
│   ├── extractor/
│   │   ├── __init__.py
│   │   └── general.py
│   ├── progress_messages.py
│   │   cmysql/
│   │   └── native.py
│   ├── summarizer.py
│   ├── executor/
│   │   ├── postgresql.py
│   │   ├── sqlserver.py
│   │   ├── sql_fixer.py
│   │   ├── __init__.py
│   │   ├── sqlite.py
│   │   ├── template.py
│   │   ├── oracle.py
│   │   ├── executor.py
│   │   └── mysql.py
│   ├── insights.py
│   ├── evaluator.py
│   ├── visualizer.py
│   └── api_logging_and_modules/
│       ├── log_api.py
│       └── modules.py
├── vers.py
├── .dockerignore
├── Saraswati-MVP2-Flow.excalidraw
├── .gitignore
├── run_testcase_json_no_llm_evaluation_new_flow_streaming_tablejoin.py
├── azure-aks.yaml
├── .env
├── test.txt
├── main.py
└── vector_db_utils/
    ├── __init__.py
    ├── table.py
    └── column.py
```

## Key Success Factors

The Saraswathi LLM Agent is optimized for the following performance metrics:
- **Time to First Response (TTFR)**: Ensures the first response to the user is delivered in less than 1 minute.
- **Total Inference Time**: Ensures the whole chart generation is delivered in less than 5 minutes.
- **Valid SQL Query Rate**: Ensures the SQL query generated for each chart is runnable and outputs data with current performance at 68.35% for `userdata_saraswati_starhub_v1` test case.
- **Valid JSON Rate**: Ensures the SQL query result can be converted to chart JSON with current performance on 68.01% for `userdata_saraswati_starhub_v1` test case.
- **Human Evaluation (Satisfactied / Not Satisfied with the charts)**: How satisfy the charts in chart title clarity, chart axis title clarity, user intent to chart alignment, etc.

## Development and Contribution

### Setting Up a Development Environment

To set up the project for development, first install the necessary dependencies and activate your virtual environment.

```bash
pip install -r requirements.txt
```

Run the FastAPI server locally for development.

```bash
uvicorn main:app --reload
```

### Testing

To run the test suite, use the following command:

```bash
pytest
```

Tests are stored in the `tests/` directory and cover unit tests for each module and API endpoint.

### Contribution Guidelines

1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/my-new-feature`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature/my-new-feature`).
5. Create a new Pull Request.
