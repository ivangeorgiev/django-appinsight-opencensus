import os
import pyodbc
import requests 
import struct

def add_pyodbc_args_for_access_token(token:str, kwargs:dict=None):
    """
    Add pyodbc.connect arguments for SQL Server connection with token.

    Based on https://docs.microsoft.com/en-us/sql/connect/odbc/using-azure-active-directory?view=sql-server-ver15

    Parameters
    ----------
    token : str
        Access token.
    kwargs: dict
        Optional kwargs. If not provided, a new dictionary will be created.

    Returns
    -------
    dict
        Dictionary of pyodbc.connect keyword arguments.
    Example:
    --------

    ```python
    import os
    import pyodbc

    # Configuration
    db_azure_server = os.environ['DB_SERVER']
    db_server = f'{db_azure_server}.database.windows.net'
    db_database = os.environ['DB_DATABASE']
    db_token = os.environ['DB_TOKEN']

    connect_kwargs = add_pyodbc_args_for_access_token(db_token)
    with pyodbc.connect(connection_string, **connect_kwargs) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT getdate()")
            row = cursor.fetchone()
            print(row[0])    
    ```
    """
    kwargs = kwargs or {}
    if (token):
        SQL_COPT_SS_ACCESS_TOKEN = 1256
        exptoken = b'';
        for i in bytes(token, "UTF-8"):
            exptoken += bytes({i});
            exptoken += bytes(1);
        tokenstruct = struct.pack("=i", len(exptoken)) + exptoken;
        kwargs['attrs_before'] = { SQL_COPT_SS_ACCESS_TOKEN:tokenstruct}
    return kwargs
    

identity_endpoint = os.environ["IDENTITY_ENDPOINT"]
identity_header = os.environ["IDENTITY_HEADER"]
resource_uri="https://database.windows.net/"
token_auth_uri = f"{identity_endpoint}?resource={resource_uri}&api-version=2019-08-01"
head_msi = {'X-IDENTITY-HEADER':identity_header}
resp = requests.get(token_auth_uri, headers=head_msi)
access_token = resp.json()['access_token']

# Configuration
db_azure_server = os.environ['DB_SERVER']
db_server = f'{db_azure_server}.database.windows.net'
db_database = os.environ['DB_DATABASE']

connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server={db_server};Database={db_database}"

connect_kwargs = add_pyodbc_args_for_access_token(access_token)
with pyodbc.connect(connection_string, **connect_kwargs) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT getdate()")
        row = cursor.fetchone()
        print(row[0])    
