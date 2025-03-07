import random
import pandas as pd
import mysql.connector
from tqdm import tqdm
import time
import numpy as np
import os
import re
import json
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import var
import chromadb
from chromadb.config import Settings
import nest_asyncio 
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import warnings
warnings.filterwarnings("ignore")

app = FastAPI()

allowed_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,  # If you want to allow cookies to be sent
#    allow_methods=["*"],  # Specify the HTTP methods you want to allow
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],  # You can customize the allowed headers or use "*" to allow any header
)
# filename = 'config.json'
# with open(filename, 'r') as file:
#     config = json.load(file)

# dataAssetName = databaseName.split(".")[1]

def call_chromadb():    

    username = var.CHROMA_DB_USERNAME
    password = var.CHROMA_DB_PASSWORD
    host = var.CHROMA_DB_HOST
    port = var.CHROMA_DB_PORT

    credentials = f"{username}:{password}"

    settings = Settings(chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                        chroma_client_auth_credentials=credentials)

    # Connection
    chroma_client = chromadb.HttpClient(host=host, port=port, settings=settings)

    return chroma_client

def get_yamuna_and_data_asset_table_from_sql(dataAssetName, config):    
    relevant_cols = ['DB_A', 'Table_A', 'Table_A_Column', 'DB_B', 'Table_B',
        'Table_B_Column', 'Flag_prim_table_A', 'Flag_prim_table_B',
        'Final_Score']

    connection = mysql.connector.connect(
        host=config['DataAssetDB']['host'],
        user=config['DataAssetDB']['user'],
        password=config['DataAssetDB']['password']
        )

    cursor = connection.cursor()
    query1 = f"""
    SELECT DISTINCT DB_A, Table_A, Table_A_Column, DB_B,Table_B, Table_B_Column, Flag_prim_table_A, Flag_prim_table_B, Final_Score
    FROM relationship_data.banking_demo 
    WHERE Table_A = '{dataAssetName}'
    AND Final_Score > 50
    """
                    
    query2 = "SELECT * FROM datalake.dev_business_agent WHERE `Data_Asset_Name` = %s"
    try:
        #get yamuna output
        cursor.execute(query1)
        rows = cursor.fetchall()
        df1 = pd.DataFrame(rows, columns=[column[0] for column in cursor.description])
        
        #get data asset table
        cursor.execute(query2, (dataAssetName,))
        rows = cursor.fetchall()
        df2 = pd.DataFrame(rows, columns=[column[0] for column in cursor.description])
        highlighted_ids = df2['Database_Name'].apply(lambda x: x.split('.')[1]).tolist()

    except mysql.connector.Error as e:
        print(f"Error fetching data for second query: {e}")

    cursor.close()
    connection.close()
    return df1,df2,highlighted_ids

# df1,df2,highlighted_ids= get_yamuna_and_data_asset_table_from_sql(dataAssetName, config)

def call_chromadb():    
    username = var.CHROMA_DB_USERNAME
    password = var.CHROMA_DB_PASSWORD
    host = var.CHROMA_DB_HOST
    port = var.CHROMA_DB_PORT

    credentials = f"{username}:{password}"

    settings = Settings(chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                        chroma_client_auth_credentials=credentials)

    # Connection
    chroma_client = chromadb.HttpClient(host=host, port=port, settings=settings)

    return chroma_client

def merged_metadata(unique_table_A):
    column_namespace = "test.ADA.banking.columnLevel"
    table_namespace = "test.ADA.banking.tableLevel"
    client = call_chromadb()
    col_column = client.get_collection(column_namespace)
    col_table = client.get_collection(table_namespace)

    column_metadata = col_column.get()
    table_metadata = col_table.get()

    column_metadata =  pd.DataFrame(column_metadata["metadatas"])
    column_metadata = column_metadata[column_metadata['table_name'].isin(unique_table_A)]
    column_metadata = column_metadata.drop_duplicates(subset=['cleaned_column_name'])

    table_metadata =  pd.DataFrame(table_metadata["metadatas"])
    table_metadata = table_metadata[table_metadata['table_name'].isin(unique_table_A)]
    table_metadata = table_metadata.drop_duplicates(subset=['table_name'])
     
    return column_metadata,table_metadata

# column_metadata,table_metadata= merged_metadata(unique_table_A)
def merge_tables_single_node(column_metadata,table_metadata,df1):
    df_table_metadata = table_metadata[['table_name', 'source', 'table_description']].copy()
    column_table_metadata_merged = pd.merge(column_metadata, df_table_metadata, on='table_name',how = 'left')
    temp = df1.copy()
    df_other_sub = column_table_metadata_merged[["table_name","original_sql_column_name","data_tribe","sql_data_type", "table_description", "source"]].copy()
    result = pd.merge(temp, df_other_sub, left_on=['Table_A', 'Table_A_Column'],right_on=['table_name', 'original_sql_column_name'], how='inner')

    condition = (result["data_tribe"] == 'date_related' ) | (result["sql_data_type"] == 'datetime' )
    filtered_df = result[~condition]
    filtered_df = filtered_df.drop(['data_tribe','sql_data_type'], axis=1)

    # result = pd.merge(filtered_df, df_other_sub, left_on=['Table_B', 'Table_B_Column'],right_on=['table_name', 'original_sql_column_name'], how='inner')
    # condition = (result["data_tribe"] == 'date_related' ) | (result["sql_data_type"] == 'datetime' )

    # filtered_df = result[~condition]
    # filtered_df = filtered_df.drop(['data_tribe','sql_data_type'], axis=1)
    df = filtered_df.copy()
    return df,column_table_metadata_merged

def filter_and_rename(databaseName,df):

    db_tb_nam = databaseName
    left_part, right_part = db_tb_nam.split(".", 1)

    df_tmp_A = df[(df["DB_A"] ==  left_part) & (df["Table_A"] ==  right_part)]
    df_tmp_A.reset_index(drop=True,inplace = True)
    df_tmp_B = df[(df["DB_B"] ==  left_part) & (df["Table_B"] ==  right_part)]
    df_tmp_B.reset_index(drop=True,inplace = True)

    dct_a = {"DB_A": "DB_A_CH", "Table_A": "Table_A_CH","Table_A_Column" : "Table_A_Column_CH","Flag_prim_table_A" : "Flag_prim_table_A_CH"}
    df_tmp_B.rename(columns=dct_a, inplace=True)

    dct_b =  {"DB_B": "DB_A", "Table_B": "Table_A","Table_B_Column" : "Table_A_Column","Flag_prim_table_B" : "Flag_prim_table_A"}
    df_tmp_B.rename(columns=dct_b, inplace=True)

    dct_a_ch = {"DB_A_CH": "DB_B", "Table_A_CH": "Table_B","Table_A_Column_CH" : "Table_B_Column","Flag_prim_table_A_CH" : "Flag_prim_table_B"}
    df_tmp_B.rename(columns=dct_a_ch, inplace=True)

    df_required = pd.concat([df_tmp_A, df_tmp_B], ignore_index=True)
    df_required = df_required.sort_values(by='Final_Score',ascending = False).reset_index(drop=True)
    df_required = df_required[df_required["Final_Score"] >= 50] # [CHANGE]: should be 80
    df_required = df.drop(columns=['DB_B', 'Table_B','Table_B_Column'])
    df_required = df_required.drop_duplicates(subset=['Table_A_Column'])

    return df_required

def form_nodes_and_edges(column_table_metadata_merged,df_required,highlighted_ids):   
    column_table_metadata_merged["source"].fillna("Flat_File", inplace=True)
    column_table_metadata_merged["source"].replace("SAP", "sap_combo", inplace=True)
    column_table_metadata_merged["source"].replace("N/A", "flat_file_combo", inplace=True)
    column_table_metadata_merged["source"].replace("data_asset_combo", "data_asset_combo", inplace=True)
    df_intm = column_table_metadata_merged[["table_name","source"]].copy()
    df_intm = df_intm.drop_duplicates()

    combo_info = {row["table_name"]: row["source"] for index, row in df_intm.iterrows()} ## This is the Dictionary that has the Table Information as the Key and the Value as the Source File 
    ##### Logic Close #######

    ##### Logic Open Nodes#######
    dct = {"id": '',
    "label": '',
    "type": '',
    "comboId": ''}

    dct_col = {"id": '',
    "label": '',
    "data": { "type": '',"description": ''},
    "type": '',
    "comboId": ''}

    dct_lst = []
    jss = []
    dtst = df_required.loc[0,'Table_A']
    dt_dsc = column_table_metadata_merged.loc[0, 'table_description']
    dt_src = column_table_metadata_merged.loc[0, 'source']

    # Initialize the dictionary for Table_A
    dct = {}
    dct["id"] = dtst
    dct["label"] = dtst.upper()
    dct["type"] = 'table'
    dct["comboId"] = 'data_asset_combo'  ### Make Change Here When the required info comes
    dct["data"] = {"description": dt_dsc, 'source': "" if pd.isna(dt_src) else dt_src, 'quality': "100%"}
    dct["highlighted"] = True
    tmp = dct.copy()

    dct_lst.append(tmp)

    remn = df_required['Table_A'].unique()
    for i in remn:
        print("i")
        print(i)
        # Filter df_required for the current 'Table_B' value
        filtered_df = df_required[df_required['Table_A'] == i]

        # Assuming there's exactly one matching row for each unique 'Table_B' value,
        # or taking the first one if there are multiple
        if not filtered_df.empty:
            # Get details from the first row
            dt_src = filtered_df.iloc[0]['source']
            dt_dsc = filtered_df.iloc[0]['table_description']

            dct = {}
            dct["id"] = i
            dct["label"] = i.upper()
            dct["type"] = 'table'
            dct["comboId"] = combo_info[i]  # Ensure combo_info is defined and has all necessary keys
            dct["data"] = {
                "description": dt_dsc,
                'source': "" if pd.isna(dt_src) else dt_src,
                'quality': "100%"
            }
            
            # Append a copy of the dictionary to the list to avoid overwriting
            dct_lst.append
            
    df_unique = df_required.drop_duplicates(subset="Table_A_Column")
    
    
    for index, row in df_unique.iterrows():
        dt_trb = column_table_metadata_merged["data_tribe"][(column_table_metadata_merged["table_name"] == row["Table_A"]) & (column_table_metadata_merged["original_sql_column_name"] == row["Table_A_Column"])].values[0]
        dt_dscr = column_table_metadata_merged["column_description"][(column_table_metadata_merged["table_name"] == row["Table_A"]) & (column_table_metadata_merged["original_sql_column_name"] == row["Table_A_Column"])].values[0]
        dt_src = column_table_metadata_merged["source"][(column_table_metadata_merged["table_name"] == row["Table_A"]) & (column_table_metadata_merged["original_sql_column_name"] == row["Table_A_Column"])].values[0]

        dictionary = {"id": row["Table_A"]+ "_"+ row["Table_A_Column"],
                "label": row["Table_A_Column"],
                "data": { "type": dt_trb,"description": dt_dscr, "source": dt_src, "quality": "100%"},
                "type": 'column',
                "comboId": "Flat_File"
        }
        dct_lst.append(dictionary)
        table_a_col_a = []   
    df_unique = df_required.drop_duplicates(subset="Table_A_Column") 

    # Connecting Table A to Columns A
    for index, row in df_unique.iterrows():
        src = row["Table_A"]
        trgt = row["Table_A"] + "_" + row["Table_A_Column"]
        dictionary = {
            "source": src,
            "target": trgt
        } 
        table_a_col_a.append(dictionary)

    col_a_col_b = []
    for index, row in df_required.iterrows():
        src = row["Table_A"] + "_" + row["Table_A_Column"]
        trgt = row.get("Table_B")  # Use .get() to safely retrieve the value
        if trgt and pd.notna(trgt):  # Check if target is not None and not NaN
            trgt += "_" + row["Table_B_Column"]
            dictionary = {
                "source": src,
                "target": trgt
            }
            col_a_col_b.append(dictionary)

    table_b_col_b = []

    # Ensure the columns exist before processing
    if 'Table_B' in df_required.columns and 'Table_B_Column' in df_required.columns:
        df_unique_b = df_required.drop_duplicates(subset=['Table_B', 'Table_B_Column'])

        for index, row in df_unique_b.iterrows():
            # Retrieve the target and source values safely
            trgt = row.get("Table_B")
            col_b = row.get("Table_B_Column")
            
            if pd.notna(trgt) and pd.notna(col_b):  # Check if both values are not NaN
                trgt = f"{trgt}_{col_b}"
                src = trgt.split('_')[0]  # Extract the source from target (if needed)
                dictionary = {
                    "source": src,
                    "target": trgt
                }
                table_b_col_b.append(dictionary)
    else:
        print("Required columns 'Table_B' or 'Table_B_Column' are missing in the dataframe.")

    # Building a mapping of columns to tables for lookup
    column_to_table_a = {d['target']: d['source'] for d in table_a_col_a}
    column_to_table_b = {d['target']: d['source'] for d in table_b_col_b}

    # Merge logic
    result_edge = []

    # For each colA to colB mapping
    for col_a_b in col_a_col_b:
        source_table = column_to_table_a.get(col_a_b['source'])
        target_table = column_to_table_b.get(col_a_b['target'])

        if source_table and target_table:  # Check if both source and target are valid
            # Check if the table combination already exists in output
            existing_entry = next((item for item in result_edge if item['source'] == source_table and item['target'] == target_table), None)
            
            if existing_entry:
                # Append columns to the existing table mapping
                existing_entry['columns']['table_1'].append(col_a_b['source'])
                existing_entry['columns']['table_2'].append(col_a_b['target'])
            else:
                # Create new entry if it doesn't exist
                result_edge.append({
                    'source': source_table,
                    'target': target_table,
                    'columns': {
                        'table_1': [col_a_b['source']],
                        'table_2': [col_a_b['target']]
                    }
                })

    # Logic Close Edges

    # Logic Open Combos
    combos = [
        {"id": "data_asset_combo", "label": "Data_Asset", "collapsed": False, "padding": [50, 50, 50, 50]},
        {"id": "sap_combo", "label": "SAP", "collapsed": False, "padding": [50, 50, 50, 50]},
        {"id": "flat_file_combo", "label": "Flat_File", "collapsed": False, "padding": [50, 50, 50, 50]}
    ]

    # Logic Close Combos

    # Remove columns from nodes
    dct_lst = [dct for dct in dct_lst if dct['type'] == 'table']

    # Logic Add Highlights
    for item in dct_lst[1:]:
        item['highlighted'] = item['id'] in highlighted_ids

    # Logic Unite as one dictionary
    final_dct = {}
    final_dct["nodes"] = dct_lst
    final_dct["edges"] = result_edge
    final_dct["combos"] = combos

    return final_dct

import warnings
warnings.filterwarnings("ignore")

@app.get("/")
async def main_test():
    return "Hello Hii"
     
@app.get("/mek_str_2_jsn")
# async def main1(query, databaseName:str,subjectIntent:str):
async def main(databaseName:str,subjectIntent:str,query):

    filename = 'config.json'
    with open(filename, 'r') as file:
        config = json.load(file)

    dataAssetName = databaseName.split(".")[1]

    df1,df2,highlighted_ids= get_yamuna_and_data_asset_table_from_sql(dataAssetName, config)

    if df2 is None or df2.empty:
        # Retrieve unique values from df1's 'Table_A' column
        unique_table_A = df1['Table_A'].unique()
        print(unique_table_A)
        column_metadata,table_metadata= merged_metadata(unique_table_A)
        df,column_table_metadata_merged= merge_tables_single_node(column_metadata,table_metadata,df1)
        df_required = filter_and_rename(databaseName,df)
        final_dict = form_nodes_and_edges(column_table_metadata_merged,df_required,highlighted_ids)
        print(final_dict)
        return final_dict

    else:
        
        # Your logic for when df2 is not null (if needed)
        pass



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)