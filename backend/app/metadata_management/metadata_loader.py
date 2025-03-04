# app/metadata_management/metadata_loader.py
import os
import pandas as pd
import json
from typing import Dict

path = os.path.dirname(os.path.abspath(__file__))
print(path)

METADATA_OUTPUT_FILE = f"{path}/metadata/metadata.json" # Define output file constant
INPUT_METADATA_FOLDER = f"{path}/input_metadata" # Define input folder constant


def read_and_merge_files(folder_path: str) -> Dict:
    """Reads and merges metadata files from a folder."""
    metadata = {}

    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)

        if os.path.isfile(file_path) and file_name.lower().endswith((".csv", ".xls", ".xlsx")):
            try:
                if file_name.lower().endswith(".csv"):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                metadata[file_name] = df.to_dict(orient="records")
            except Exception as e:
                print(f"Error reading {file_name}: {e}")
    return metadata


def process_metadata(input_folder: str = INPUT_METADATA_FOLDER, output_file: str = METADATA_OUTPUT_FILE) -> Dict:
    """
    Processes metadata files from the input folder, merges them, and saves to a JSON file.
    Returns the loaded metadata as a dictionary.
    """
    output_dir = os.path.dirname(output_file)
    os.makedirs(output_dir, exist_ok=True) # Ensure metadata dir exists

    metadata = read_and_merge_files(input_folder)

    with open(output_file, "w", encoding="utf-8") as out_f:
        json.dump(metadata, out_f, indent=4) # Write merged metadata to JSON

    print(f"Metadata documentation generated in '{output_file}'")
    return metadata # Return the metadata