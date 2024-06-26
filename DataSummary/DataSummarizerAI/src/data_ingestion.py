# src/data_ingestion.py
import pandas as pd

def read_data(file_path):
    """Reads data from a CSV file."""
    data = pd.read_csv(file_path)
    return data
