from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import glob
import math
import re
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can specify allowed origins instead of "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic Authentication setup
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("ENV_USERNAME")
    correct_password = os.getenv("ENV_PASSWORD")
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

def sanitize_data(data):
    """Recursively replace NaN or Infinity with None and remove None values."""
    if isinstance(data, dict):
        # Remove None values from dictionaries
        return {k: sanitize_data(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        # Remove None values from lists
        return [sanitize_data(v) for v in data if v is not None]
    elif isinstance(data, float):
        # Replace NaN or Infinity with None
        if math.isinf(data) or math.isnan(data):
            return None
    return data

def sanitize_value(value):
    """Sanitize values to ensure they are JSON-compliant."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None  # Or you can return a default value like 0 or "N/A"
    return value

# Path to the dataset folder
dataset_path = 'dataset'

# Function to clean column names
def clean_column(name):
    name = name.lower()
    name = name.replace(' ', '_')
    name = re.sub(r'[^a-z0-9_]', '', name)
    name = re.sub(r'_+', '_', name)
    return name

# Load all CSV files into a single DataFrame
dataframes = []
for filepath in glob.glob(os.path.join(dataset_path, '**', '*.csv'), recursive=True):
    df = pd.read_csv(filepath)
    df.columns = [clean_column(col) for col in df.columns]
    dataframes.append(df)

if dataframes:
    combined_df = pd.concat(dataframes, ignore_index=True)
    # Ensure 'visual_id' column exists
    if 'visual_id' not in combined_df.columns:
        raise ValueError("No 'visual_id' column found in the dataset")
else:
    raise ValueError("No CSV files found in the dataset folder or all CSV files are empty")

# Ensure 'visual_id' column exists
if 'visual_id' not in combined_df.columns:
    raise ValueError("No 'visual_id' column found in the dataset")

# Convert DataFrame to dictionary grouped by 'visual_id'
visual_data = combined_df.groupby('visual_id').apply(
    lambda x: x.drop('visual_id', axis=1).to_dict('records')
).to_dict()

# Sanitize visual data before returning it
sanitized_visual_data = sanitize_data(visual_data)

@app.get("/visual_id", response_model=Dict[str, List[str]])
def list_visual_ids(credentials: HTTPBasicCredentials = Depends(authenticate)):
    sanitized_data = sanitize_data(sanitized_visual_data)
    unique_visual_ids = list(set(sanitized_data.keys()))
    return {"data": unique_visual_ids}

@app.get("/visual_id/{visual_id}", response_model=Dict[str, List[Dict]])
def get_visual_id(visual_id: str, credentials: HTTPBasicCredentials = Depends(authenticate)):
    if visual_id in sanitized_visual_data:
        sanitized_data = sanitize_data(sanitized_visual_data[visual_id])
        return {"data": sanitized_data}
    else:
        raise HTTPException(status_code=404, detail="visual_id not found")

@app.get("/visual_id/{visual_id}/qdf")
def get_qdf(visual_id: str, credentials: HTTPBasicCredentials = Depends(authenticate)):
    # Check if the visual_id contains a column `va_qdfnames_...`
    visual_records = visual_data.get(visual_id)
    if visual_records is None:
        raise HTTPException(status_code=404, detail="visual_id not found")
    
    # Find the column that starts with `va_qdfnames_`
    qdf_column = next((col for col in combined_df.columns if col.startswith(f'va_qdfnames_')), None)
    if not qdf_column:
        raise HTTPException(status_code=404, detail="QDF column not found")

    # Extract the QDF names and split by "~"
    qdf_names = visual_records[0].get(qdf_column, "")
    qdf_elements = qdf_names.split('~') if qdf_names else []
    
    return {"data": qdf_elements}

@app.get("/visual_id/{visual_id}/qdf/{qdf}")
def get_visual_id_qdf(visual_id: str, qdf: str, credentials: HTTPBasicCredentials = Depends(authenticate)):
    # Verifica si el visual_id existe
    if visual_id not in visual_data:
        raise HTTPException(status_code=404, detail="visual_id not found")
    
    visual_records = visual_data[visual_id]
    qdf_index = None

    # Busca el índice del QDF en la columna va_qdfnames_
    for column in visual_records[0]:
        if re.match(r'^va_qdfnames_\d+', column):  # Verifica si la columna empieza con va_qdfnames_ y luego números
            column_values = visual_records[0].get(column, "")
            for idx, column_value in enumerate(column_values.split("~")):
                if column_value.lower() == qdf.lower():
                    qdf_index = idx
                    break
            if qdf_index is not None:
                break

    if qdf_index is None:
        raise HTTPException(status_code=404, detail="QDF not found")

    # Recopila los datos correspondientes al QDF
    result_data = {}

    for column in visual_records[0]:
        # Excluye las columnas va_qdfnames_ y procesa las que no contienen ~
        if re.match(r'^va_qdfnames_\d+', column):  # Evita las columnas va_qdfnames_
            continue
        
        column_values = visual_records[0].get(column, "")
        
        # Si la columna contiene ~, extraemos el valor correspondiente al QDF
        if isinstance(column_values, str) and '~' in column_values:
            column_elements = column_values.split('~')
            # Asegura que el índice esté dentro del rango
            if 0 <= qdf_index < len(column_elements):
                result_data[column] = sanitize_value(column_elements[qdf_index])
            else:
                result_data[column] = None  # Si el índice está fuera de rango, asigna None
        else:
            # Si no contiene ~, simplemente añadimos la columna si no es None
            if column_values is not None:
                result_data[column] = sanitize_value(column_values)
    
    # Filtra los valores None del resultado
    result_data = {key: value for key, value in result_data.items() if value is not None}

    return {"data": result_data}