#!/usr/bin/env python
# coding: utf-8

# In[1]:


import random
    # to connect to mysql
import pandas as pd
import mysql.connector

# to push data into mysql
from tqdm import tqdm
import time
import numpy as np
import os
import re
# import pinecone
import json
import numpy as np
# from langchain.embeddings import OpenAIEmbeddings
# import openai
# import nest_asyncio  # Import nest_asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse


# In[2]:

# nest_asyncio.apply()  # Apply nest_asyncio to allow asyncio.run() inside Jupyter


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



def metadata_input(path = None):
    # Input DB Metadata / CSV 
    
    ### Rename To 'dbname', 'table_name', 'original_column_name', 'samples','data_dictionary_flag', 'data_tribe', 'column_description', 'max_value','min_value', 'n_unique', 'n_unique_per_row_count', 'pct_null_values','possible_values', 'sql_path', 'data_type'
    ### Convert all Columns that need to be vectorized and used as vector IDs into string for each row.
    import pandas as pd
    df =  pd.read_csv(path)
    df["table_name"] =  df['table_name'].astype(str)
    df["original_column_name"]=  df['original_column_name'].astype(str)
    df["column_description"]=  df['column_description'].astype(str)
    df["samples"]=  df['samples'].astype(str)
    
    df["non_null_fract"] = 1-df['pct_null_values']/100
    
    for column in df.columns:
        if df[column].apply(lambda x: isinstance(x, str) and x.strip() != x).any():
            pass
    
    def clean_unicode(text):
        try:
            # Try to decode the text as UTF-8
            cleaned_text = text.encode('utf-8').decode('utf-8')
        except UnicodeDecodeError:
            # If decoding fails, replace non-compliant characters with a replacement character
            cleaned_text = text.encode('utf-8', 'replace').decode('utf-8')
        return cleaned_text

    # Apply the cleaning function to the column
    df['original_column_name_unicode'] = df['original_column_name'].apply(clean_unicode)
    df['id'] = df['table_name']+ "." + df['original_column_name_unicode']
    df['id'] = df['id'].str.replace(' ', '|')  ##This is because, if ID has space in Pinecone "fetching_not possible"

    return df


@app.get("/DataObserAvinash_jsn")
async def main(query, databaseName:str,subjectIntent:str):
    #     val = "relationship_data.new_final_score_60"


    

    # print("databaseName")

    # print(databaseName)

    # print('subjectIntent')

    # print(subjectIntent)

    table_name_tmp:str

    indent:str

 

    

    array_param=str(query)

    table_name_tmp:str

    indent:str

 

    array=array_param.split(',')

       # print(type(array[0]))

    val=array[0]

    resultant_string = val[2:]

    resultant_string=resultant_string[:-1]

    print(resultant_string)

    table_name_tmp=resultant_string

    # array_Indent=array[1].split(':')

    # str_Indent=array_Indent[1]

    # str_Indent=str_Indent[:-4]

    # str_Indent=str_Indent[2:]

    # indent=str_Indent

    table_name_tmp=table_name_tmp.replace(" ","")

 

    # print("table_name_tmp: " + table_name_tmp)

    # print("indent: " + indent)

    # print(type(table_name_tmp))

    # print(type(indent))

    databaseName=databaseName.replace("+","")

    table_name_tmp=databaseName.replace(" ","")

    # if subjectIntent.find(':') != -1:

    #     array_Indent=subjectIntent.split(':')

 

    #     str_Indent  =array_Indent[1]

        

    #.replace('"','').strip()

    # else :

    #     str_Indent=subjectIntent

 

    # str_Indent=str_Indent.replace("+","").replace("}","")

    # indent=str_Indent.replace('\\',' ').replace(" ","")

    return table_name_tmp




   

 

   
    

 

    

  
 





import random
    # to connect to mysql
import pandas as pd
import mysql.connector

# to push data into mysql
import pymysql
import glob
from tqdm import tqdm
import time
import numpy as np
import os
import re
# import pinecone
import json
import numpy as np
# from langchain.embeddings import OpenAIEmbeddings
# import openai
# import nest_asyncio  # Import nest_asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse
import chromadb
import json
import var
# import chromadb
from chromadb.config import Settings

filename = 'config.json'

with open(filename, 'r') as file:
    config = json.load(file)
## password for sql
# password = urllib.parse.quote_plus(config['UserDataDB']['password'])
    
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

def retrieve_data_from_chromadb(collection_name):
    client = call_chromadb()
    client = chromadb.PersistentClient(path=config['ChromaDB']['path'])
    collection = client.get_collection(collection_name.lower())
    results = collection.get()
    data = [doc for doc in results["metadatas"]]
    ids = results['ids']

    df = pd.DataFrame(data)
    df.index = ids
    df.index.name = 'Chroma_ID'

    return df


# In[2]:

# nest_asyncio.apply()  # Apply nest_asyncio to allow asyncio.run() inside Jupyter


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



def metadata_input(path = None):
    # Input DB Metadata / CSV 
    
    ### Rename To 'dbname', 'table_name', 'original_column_name', 'samples','data_dictionary_flag', 'data_tribe', 'column_description', 'max_value','min_value', 'n_unique', 'n_unique_per_row_count', 'pct_null_values','possible_values', 'sql_path', 'data_type'
    ### Convert all Columns that need to be vectorized and used as vector IDs into string for each row.
    import pandas as pd
    df =  pd.read_csv(path)
    df["table_name"] =  df['table_name'].astype(str)
    df["original_column_name"]=  df['original_column_name'].astype(str)
    df["column_description"]=  df['column_description'].astype(str)
    df["samples"]=  df['samples'].astype(str)
    
    df["non_null_fract"] = 1-df['pct_null_values']/100
    
    for column in df.columns:
        if df[column].apply(lambda x: isinstance(x, str) and x.strip() != x).any():
            pass
    
    def clean_unicode(text):
        try:
            # Try to decode the text as UTF-8
            cleaned_text = text.encode('utf-8').decode('utf-8')
        except UnicodeDecodeError:
            # If decoding fails, replace non-compliant characters with a replacement character
            cleaned_text = text.encode('utf-8', 'replace').decode('utf-8')
        return cleaned_text

    # Apply the cleaning function to the column
    df['original_column_name_unicode'] = df['original_column_name'].apply(clean_unicode)
    df['id'] = df['table_name']+ "." + df['original_column_name_unicode']
    df['id'] = df['id'].str.replace(' ', '|')  ##This is because, if ID has space in Pinecone "fetching_not possible"

    return df




@app.get("/mek_str_2_jsn1")
async def main1(query, databaseName:str,subjectIntent:str):
#     val = "relationship_data.new_final_score_60"

#     val = "relationship_data.new_final_score_60"


    

    # print("databaseName")

    # print(databaseName)

    # print('subjectIntent')

    # print(subjectIntent)

    table_name_tmp:str

    indent:str

 

    

    array_param=str(query)

    table_name_tmp:str

    indent:str

 

    array=array_param.split(',')

       # print(type(array[0]))

    val=array[0]

    resultant_string = val[2:]

    resultant_string=resultant_string[:-1]

    print(resultant_string)

    table_name_tmp=resultant_string

    array_Indent=array[1].split(':')

    str_Indent=array_Indent[1]

    str_Indent=str_Indent[:-4]

    str_Indent=str_Indent[2:]

    indent=str_Indent

    table_name_tmp=table_name_tmp.replace(" ","")

 

    # print("table_name_tmp: " + table_name_tmp)

    # print("indent: " + indent)

    # print(type(table_name_tmp))

    # print(type(indent))

    databaseName=databaseName.replace("+","")

    table_name_tmp=databaseName.replace(" ","")

    if subjectIntent.find(':') != -1:

        array_Indent=subjectIntent.split(':')

 

        str_Indent  =array_Indent[1]

        

    #.replace('"','').strip()

    else :

        str_Indent=subjectIntent

 

    str_Indent=str_Indent.replace("+","").replace("}","")

    indent=str_Indent.replace('\\',' ').replace(" ","")
    
    
    print("hello")
    
@app.get("/")
async def main_test():
    return "Hello Hii"
     
@app.get("/mek_str_2_jsn")
async def main1(query, databaseName:str,subjectIntent:str):
    dataAssetName = databaseName.split(".")[1]
    print(dataAssetName)
    print("Input", databaseName, dataAssetName)

    table_name_tmp:str

    indent:str

    array_param=str(query)

    table_name_tmp:str

    indent:str

    array=array_param.split(',')

    val=array[0]

    resultant_string = val[2:]

    resultant_string=resultant_string[:-1]

    table_name_tmp=resultant_string

    table_name_tmp=table_name_tmp.replace(" ","")


    databaseName=databaseName.replace("+","")

    table_name_tmp=databaseName.replace(" ","")

    val = table_name_tmp

    # collection_name = config['ChromaDB']['relationships_namespace']
    relevant_cols = ['DB_A', 'Table_A', 'Table_A_Column', 'DB_B', 'Table_B',
        'Table_B_Column', 'Flag_prim_table_A', 'Flag_prim_table_B',
        'Final_Score']

    connection = mysql.connector.connect(
        host=config['DataAssetDB']['host'],
        user=config['DataAssetDB']['user'],
        password=config['DataAssetDB']['password']      
        )

    cursor = connection.cursor()
    query1 = "SELECT * FROM relationship_data.relationship_metadata_211123"
    query2 = "SELECT * FROM datalake.dev_business_agent WHERE `Data_Asset_Name` = %s"
    try:
        cursor.execute(query2, ('bike',))
        rows = cursor.fetchall()
        df2 = pd.DataFrame(rows, columns=[column[0] for column in cursor.description])
        highlighted_ids = df2['Database_Name'].apply(lambda x: x.split('.')[1]).tolist()

        cursor.execute(query1)
        rows = cursor.fetchall()
        df1 = pd.DataFrame(rows, columns=[column[0] for column in cursor.description])
    except mysql.connector.Error as e:
        print(f"Error fetching data for second query: {e}")

    cursor.close()
    connection.close()
    ######## Get relationship data from chroma ########
    # collection_name = config['ChromaDB']['relationships_namespace']
    relevant_cols = ['DB_A', 'Table_A', 'Table_A_Column', 'DB_B', 'Table_B',
        'Table_B_Column', 'Flag_prim_table_A', 'Flag_prim_table_B',
        'Final_Score']
    
    df = df1
    df = df.drop([col for col in df.columns if col not in relevant_cols], axis=1)

    ######## Get highlights from client_business_agent ########
    
    ####### Import the Metadata ########
    # [CHANGE]: Get Metadata from chroma
    df_othr_info = metadata_input(path = "1_oct_metadata.csv")
    dftemp2 = pd.read_csv('metadat_latest_1oct.csv') #####
    dftemp2 = dftemp2[['table_name', 'source', 'table_description']].copy()
    df_other = pd.merge(df_othr_info, dftemp2, on='table_name',how = 'left')

    ###### Logic Open ########
    ####  Logic : Date Column Removal in all the RelationShip data, this can be ignored for the Next vesion of the Relationship data
    temp = df.copy()
    df_other_sub = df_other[["table_name","original_column_name","data_tribe","data_type", "table_description", "source"]].copy()
    result = pd.merge(temp, df_other_sub, left_on=['Table_A', 'Table_A_Column'],right_on=['table_name', 'original_column_name'], how='inner')
    condition = (result["data_tribe"] == 'date_related' ) | (result["data_type"] == 'datetime' )


    # Use the condition to filter the DataFrame
    filtered_df = result[~condition]
    filtered_df = filtered_df.drop(['data_tribe','data_type'], axis=1)

    #### Date Column Removal in all the RelationShip data, this can be ignored for the Next vesion of the Relationship data

    result = pd.merge(filtered_df, df_other_sub, left_on=['Table_B', 'Table_B_Column'],right_on=['table_name', 'original_column_name'], how='inner')
    condition = (result["data_tribe"] == 'date_related' ) | (result["data_type"] == 'datetime' )


    # Use the condition to filter the DataFrame
    filtered_df = result[~condition]
    filtered_df = filtered_df.drop(['data_tribe','data_type'], axis=1)
    ###### Logic Close  #########
    df = filtered_df.copy()

    seed_value = 42
    np.random.seed(seed_value)  # Set the random seed for NumPy

    # Get a random sample of one row from the DataFrame df with the specified seed
    random_row = df.sample(n=1, random_state=seed_value)

    #     # Select specific columns from the randomly selected row
    #     selected_columns = random_row[['DB_A', 'Table_A']]
    #     selected_columns = selected_columns.reset_index(drop=True)
    #     a = selected_columns.at[0, 'DB_A']
    #     b = selected_columns.at[0, 'Table_A']
    # #     db_tb_nam = a + "." + b                 ############################ Input Value here
    #     # db_tb_nam
    db_tb_nam = val
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
    df_required = df_required[df_required["Final_Score"] >= 65] # [CHANGE]: should be 80


    ##### Logic Open #######
    ###### Combo Information for Each tAble ####3
    df_other["source"].fillna("Flat_File", inplace=True)
    df_other["source"].replace("SAP", "sap_combo", inplace=True)
    df_other["source"].replace("Flat_File", "flat_file_combo", inplace=True)
    df_other["source"].replace("data_asset_combo", "data_asset_combo", inplace=True)
    df_intm = df_other[["table_name","source"]].copy()
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


    # [CHANGE]: quality is being hardcoded
    dct_lst = []
    jss = []
    dtst = df_required.loc[0,'Table_A']
    dt_dsc = df_required.loc[0, 'table_description_x']
    dt_src = df_required.loc[0, 'source_x']

    dct["id"] = dtst
    dct["label"] = dtst.upper()
    dct["type"] = 'table'
    dct["comboId"] = 'data_asset_combo'  ### Make Change Here When the required info comes
    dct["data"] = {"description": dt_dsc, 'source': "" if np.isnan(dt_src) else dt_src, 'quality': "100%"}
    dct["highlighted"] = True
    tmp = dct.copy()
    
    dct_lst.append(tmp)
    
    remn = df_required['Table_B'].unique()
    for i in remn.tolist():
        filtered_df = df_required[df_required['Table_B'] == i]

        # Assuming there's exactly one matching row for each unique Table_B value,
        # or taking the first one if there are multiple
        if not filtered_df.empty:
            dt_src = filtered_df.iloc[0]['source_y']
            dt_dsc = filtered_df.iloc[0]['table_description_y']

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
            dct_lst.append(dct.copy()) 



    df_unique = df_required.drop_duplicates(subset="Table_A_Column") 
    for index, row in df_unique.iterrows():
        dt_trb = df_other["data_tribe"][(df_other["table_name"] == row["Table_A"]) & (df_other["original_column_name"] == row["Table_A_Column"])].values[0]
        dt_dscr = df_other["column_description"][(df_other["table_name"] == row["Table_A"]) & (df_other["original_column_name"] == row["Table_A_Column"])].values[0]
        dt_src = df_other["source"][(df_other["table_name"] == row["Table_A"]) & (df_other["original_column_name"] == row["Table_A_Column"])].values[0]

        dictionary = {"id": row["Table_A"]+ "_"+ row["Table_A_Column"],
                "label": row["Table_A_Column"],
                "data": { "type": dt_trb,"description": dt_dscr, "source": dt_src, "quality": "100%"},
                "type": 'column',
                "comboId": "data_asset_combo"
        }
        dct_lst.append(dictionary)
    df_unique_b     = df_required.drop_duplicates(subset=['Table_B', 'Table_B_Column']) ### There might be repetation of the Same table and Same column name again
    for index, row in df_unique_b.iterrows():
        dt_trb = df_other["data_tribe"][(df_other["table_name"] == row["Table_B"]) & (df_other["original_column_name"] == row["Table_B_Column"])].values[0]
        dt_dscr = df_other["column_description"][(df_other["table_name"] == row["Table_B"]) & (df_other["original_column_name"] == row["Table_B_Column"])].values[0]
        dt_src = df_other["source"][(df_other["table_name"] == row["Table_B"]) & (df_other["original_column_name"] == row["Table_B_Column"])].values[0]

        dictionary = {"id": row["Table_B"]+ "_"+ row["Table_B_Column"],
                    "label": row["Table_B_Column"],
                    "data": { "type": dt_trb,"description": dt_dscr, "source": dt_src, "quality": "100%"},
                    "type": 'column',
                    "comboId": combo_info[row["Table_B"]]
        }
        dct_lst.append(dictionary)



    ##### Logic Close Nodes#######



    ##### Logic Open Edges#######
    table_a_col_a = []   
    df_unique = df_required.drop_duplicates(subset="Table_A_Column") 
    for index, row in df_unique.iterrows(): #### Here We are Connecting Table A to Columns A, When Taking the Unique the duplicate nodes are removed
        src = row["Table_A"]
        trgt = row["Table_A"]+"_"+row["Table_A_Column"]
        dictionary = {
            "source": src,
            "target": trgt
        } 
        table_a_col_a.append(dictionary)

    col_a_col_b = []
    for index, row in df_required.iterrows():  ### Here Connecting the Columns of A to Columns of B
        src = row["Table_A"]+"_"+row["Table_A_Column"]
        trgt = row["Table_B"]+"_"+row["Table_B_Column"]
        dictionary = {
            "source": src,
            "target": trgt
        }
        col_a_col_b.append(dictionary)

    table_b_col_b = []
    df_unique_b     = df_required.drop_duplicates(subset=['Table_B', 'Table_B_Column'])    
    for index, row in df_unique_b.iterrows():  ### Here Connecting the Tables of B to Columns of B 
        trgt = row["Table_B"]+"_"+row["Table_B_Column"]
        src = row["Table_B"]
        dictionary = {
            "source": src,
            "target": trgt
        }
        table_b_col_b.append(dictionary)
    
    # Building a mapping of columns to tables for lookup
    column_to_table_a = {d['target']: d['source'] for d in table_a_col_a}
    column_to_table_b = {d['target']: d['source'] for d in table_b_col_b}

    # Merge logic
    result_edge = []

    # For each colA to colB mapping
    for col_a_b in col_a_col_b:
        source_table = column_to_table_a.get(col_a_b['source'])
        target_table = column_to_table_b.get(col_a_b['target'])

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
    ##### Logic Close Edges #######

    ##### Logic Open Combos #######
    combos = [
                { "id": "data_asset_combo", "label": "Data_Asset","collapsed": False, "padding": [50,50,50, 50]},
                { "id": "sap_combo", "label": "SAP" ,"collapsed": False, "padding": [50,50,50, 50]},
                { "id": "flat_file_combo", "label": "Flat_File","collapsed": False, "padding": [50,50,50, 50]}
            ]

    ##### Logic Close Combos #######

    #### Remove columns from nodes ####
    # [CHANGE]: Should we really be doing this?
    dct_lst = [dct for dct in dct_lst if dct['type'] == 'table']

    #### Logic Add Highlights ####
    for item in dct_lst[1:]:
        item['highlighted'] = item['id'] in highlighted_ids
        # if item['comboId'] == 'data_asset_combo': 
        #     item['highlighted'] = True

    #### Logic Unite as one dictionary #####
    final_dct = {}
    final_dct["nodes"] = dct_lst
    final_dct["edges"] = result_edge
    final_dct["combos"] = combos   
    
    return final_dct



















#     connection = mysql.connector.connect(
#         host="20.212.32.214",
#         user="UserDataDb",
#         password="sa_54321"
#         )

#     cursor = connection.cursor()
#     query1 = f"SELECT * FROM relationship_data.new_final_score_60"
#     cursor.execute(query1)

#     rows = cursor.fetchall()

#     # Convert fetched data into a pandas DataFrame
#     df = pd.DataFrame(rows, columns=[column[0] for column in cursor.description])

#     cursor.close()
#     connection.close()
    
    
# #     import random

#     seed_value = 42
#     np.random.seed(seed_value)  # Set the random seed for NumPy

#     # Get a random sample of one row from the DataFrame df with the specified seed
#     random_row = df.sample(n=1, random_state=seed_value)

#     # Select specific columns from the randomly selected row
#     selected_columns = random_row[['DB_A', 'Table_A']]
#     selected_columns = selected_columns.reset_index(drop=True)
#     a = selected_columns.at[0, 'DB_A']
#     b = selected_columns.at[0, 'Table_A']
# #     db_tb_nam = a + "." + b                 ############################ Input Value here
#     # db_tb_nam
#     db_tb_nam = val
#     left_part, right_part = db_tb_nam.split(".", 1)

#     df_tmp_A = df[(df["DB_A"] ==  left_part) & (df["Table_A"] ==  right_part)]
#     df_tmp_A.reset_index(drop=True,inplace = True)
#     df_tmp_B = df[(df["DB_B"] ==  left_part) & (df["Table_B"] ==  right_part)]
#     df_tmp_B.reset_index(drop=True,inplace = True)

#     dct_a = {"DB_A": "DB_A_CH", "Table_A": "Table_A_CH","Table_A_Column" : "Table_A_Column_CH","Flag_prim_table_A" : "Flag_prim_table_A_CH"}
#     df_tmp_B.rename(columns=dct_a, inplace=True)

#     dct_b =  {"DB_B": "DB_A", "Table_B": "Table_A","Table_B_Column" : "Table_A_Column","Flag_prim_table_B" : "Flag_prim_table_A"}
#     df_tmp_B.rename(columns=dct_b, inplace=True)

#     dct_a_ch = {"DB_A_CH": "DB_B", "Table_A_CH": "Table_B","Table_A_Column_CH" : "Table_B_Column","Flag_prim_table_A_CH" : "Flag_prim_table_B"}
#     df_tmp_B.rename(columns=dct_a_ch, inplace=True)

#     df_required = pd.concat([df_tmp_A, df_tmp_B], ignore_index=True)
#     df_required = df_required.sort_values(by='Final_Score',ascending = False).reset_index(drop=True)
#     df_required = df_required[df_required["Final_Score"] >= 80]
    
#     path = "60_metadata.csv" ######
    
#     df_othr_info = metadata_input(path = path)
#     dftemp2 = pd.read_csv('metadat_latest_5sept.csv') #####
#     dftemp2 = dftemp2[['table_name','source']].copy()
#     df_other = pd.merge(df_othr_info, dftemp2, on='table_name',how = 'left')
#     df_other["source"].fillna("Flat_File", inplace=True)
#     df_other["source"].replace("SAP", "sap_combo", inplace=True)
#     df_other["source"].replace("Flat_File", "flat_file_combo", inplace=True)
#     df_other["source"].replace("data_asset_combo", "data_asset_combo", inplace=True)
#     df_intm = df_other[["table_name","source"]].copy()
#     df_intm = df_intm.drop_duplicates()

#     combo_info = {row["table_name"]: row["source"] for index, row in df_intm.iterrows()}
    
#     dct = {"id": '',
#     "label": '',
#     "type": '',
#     "comboId": ''}

#     dct_col = {"id": '',
#     "label": '',
#     "data": { "type": '',"description": ''},
#     "type": '',
#     "comboId": ''}
    
    
#     dct_lst = []
#     jss = []
#     dtst = df_required.loc[0,'Table_A']
#     dct["id"] = dtst
#     dct["label"] = dtst.upper()
#     dct["type"] = 'table'
#     dct["comboId"] = 'data_asset_combo'  ### Make Change Here When the required info comes
#     tmp = dct.copy()
#     dct_lst.append(tmp)


#     remn = df_required['Table_B'].unique()
#     for i in remn.tolist():

#         dct["id"] = i
#         dct["label"] = i.upper()
#         dct["type"] = 'table'
#         dct["comboId"] = combo_info[i]
#         #Json
#         tmp = dct.copy()
#         dct_lst.append(tmp)   
#         #Js
#         js_object_literal = f'''{{id:"{i}",label:"{i.upper()}",type:"table",comboID:"{combo_info[i]}"}}'''
#         jss.append(js_object_literal)

# # dtst_col = df_required['Table_A_Column'].unique()
# # for i in dtst_col.tolist():
# #     dct_col["id"] = i
# #     dct_col["label"] = i.upper()
    
# #     dt_trb = df_other["data_tribe"][(df_other["table_name"] == dtst) & (df_other["original_column_name"] == i)].values[0]
# #     dt_dscr = df_other["column_description"][(df_other["table_name"] == dtst) & (df_other["original_column_name"] == i)].values[0]
    
# #     dct_col["data"]["type"] = dt_trb
# #     dct_col["data"]["description"] = dt_dscr
    
# #     dct_col["type"] = 'column'
# #     dct_col["comboId"] = 'Data_Asset'  ### Make Change Here When the required info comes
# #     tmp = dct_col.copy()
    
# #     dct_lst.append(tmp)
    
# #     js_nested_literal = '{' + ','.join([f'{key}:"{value}"' for key, value in tmp["data"].items()]) + '}'
    
# ####    js_object_literal = f'''{{id:"{i}",label:"{i.upper()}",data:{js_nested_literal},type:"column",comboID:"Data_Asset"}}'''
# #     jss.append(js_object_literal)

#     df_unique = df_required.drop_duplicates(subset="Table_A_Column")
#     df_unique90= df_unique[df_unique["Final_Score"] >= 90]
#     df_unique80= df_unique[(df_unique["Final_Score"] >= 80) & (df_unique["Final_Score"] < 90)]

#     dtst_col_A = df_unique90['Table_A_Column'].unique()
#     for i in dtst_col_A.tolist():
#         dct_col["id"] = i
#         dct_col["label"] = i.upper()

#         dt_trb = df_other["data_tribe"][(df_other["table_name"] == dtst) & (df_other["original_column_name"] == i)].values[0]
#         dt_dscr = df_other["column_description"][(df_other["table_name"] == dtst) & (df_other["original_column_name"] == i)].values[0]

#         dct_col["data"]["type"] = dt_trb
#         dct_col["data"]["description"] = dt_dscr
#     #     print(dct_col["data"]["description"])
#         dct_col["type"] = 'column'
#         dct_col["comboId"] = 'data_asset_combo'  ### Make Change Here When the required info comes
#         temp = dct_col.copy()
#         temp["data"] = dct_col["data"].copy()
#     #     temp["data"]["description"] = dt_dscr["data"]["type"] 
#         dct_lst.append(temp)

#         js_nested_literal = '{' + ','.join([f'{key}:"{value}"' for key, value in temp["data"].items()]) + '}'


#         js_object_literal = f'''{{id:"{i}",label:"{i.upper()}",data:{js_nested_literal},type:"column",comboID:"data_asset_combo"}}'''
#         jss.append(js_object_literal)



#     dtst_col_B = df_unique80['Table_A_Column'].unique()
#     dtst_comb_info = df_unique80['Table_B'].unique()
#     for i,j in zip(dtst_col_B.tolist() , dtst_comb_info.tolist()):
#         dct_col["id"] = i
#         dct_col["label"] = i.upper()

#         dt_trb = df_other["data_tribe"][(df_other["table_name"] == dtst) & (df_other["original_column_name"] == i)].values[0]
#         dt_dscr = df_other["column_description"][(df_other["table_name"] == dtst) & (df_other["original_column_name"] == i)].values[0]

#         dct_col["data"]["type"] = dt_trb
#         dct_col["data"]["description"] = dt_dscr

#         dct_col["type"] = 'column'
#         dct_col["comboId"] = combo_info[j]  ### Make Change Here When the required info comes

#         temp = dct_col.copy()
#         temp["data"] = dct_col["data"].copy()    
#     #     temp["data"]["type"] = dt_trb
#     #     temp["data"]["description"] = dt_dscr
#         dct_lst.append(temp)


#         js_nested_literal = '{' + ','.join([f'{key}:"{value}"' for key, value in temp["data"].items()]) + '}'


#         js_object_literal = f'''{{id:"{i}",label:"{i.upper()}",data:{js_nested_literal},type:"column",comboID:"data_asset_combo"}}'''
#         jss.append(js_object_literal)
        
#     final_dct = {}
#     final_dct["nodes"] = dct_lst
    
#     edge_a = df_required[["Table_A","Table_A_Column"]].drop_duplicates()
#     edge_b = df_required[["Table_B","Table_A_Column"]].drop_duplicates()
#     result_edge = []
#     jss_edge = []
#     for index, row in edge_a.iterrows():
#         dictionary = {
#             "source": row["Table_A"],
#             "target": row["Table_A_Column"]
#         }


#         result_edge.append(dictionary)

#         js_object_literal = f'''{{source:"{row["Table_A"]}",target:"{row["Table_A_Column"]}"}}'''
#         jss_edge.append(js_object_literal)
#     for index, row in edge_b.iterrows():
#         dictionary = {
#             "source": row["Table_B"],
#             "target": row["Table_A_Column"]
#         }
#         result_edge.append(dictionary)
#         js_object_literal = f'''{{source:"{row["Table_B"]}",target:"{row["Table_A_Column"]}"}}'''
#         jss_edge.append(js_object_literal)

#     final_dct["edges"] =    result_edge
    
#     jss_combos = []
#     combos = [
#             { "id": "data_asset_combo", "label": "Data_Asset","collapsed": False, "padding": [50,50,50, 50]},
#             { "id": "sap_combo", "label": "SAP" ,"collapsed": False, "padding": [50,50,50, 50]},
#             { "id": "flat_file_combo", "label": "Flat_File","collapsed": False, "padding": [50,50,50, 50]}
#         ]
#     for i in combos:
#         js_id = i["id"]
#         js_label = i["label"]
#         js_collapsed = i["collapsed"]
#         js_padding = i["padding"]

#         # Create a JavaScript object literal for the current dictionary
#         js_object_literal = f'''{{id:"{js_id}",label:"{js_label}",collapsed:{js_collapsed},padding:{js_padding}}}'''
#         jss_combos.append(js_object_literal)
        
        
#     final_dct["combos"] =    combos
    
#     jss_jn = '[' + ','.join(jss)+ ']'
#     jss_jn_edge = '[' + ','.join(jss_edge) + ']'
#     jss_jn_combos = '[' + ','.join(jss_combos) + ']'
#     js_all = f"""{{nodes:{jss_jn},edges:{jss_jn_edge},combos:{jss_jn_combos}}} """

#     js_an = f"""{{Data:"{js_all}"}} """
    
#     return final_dct


# # In[ ]:






if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

