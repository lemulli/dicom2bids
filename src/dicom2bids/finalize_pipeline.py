#!/usr/bin/env python3
# finalize_pipeline.py

import os
import sys
import logging
import zipfile
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from .main import Config, load_config
from .utils.logging import setup_logging

# Set up logging
logger = logging.getLogger(__name__)

def remove_json_files(bids_dir: str) -> int:
    """
    Remove all JSON files from the BIDS directory.
    
    Parameters:
    bids_dir (str): Path to BIDS directory
    
    Returns:
    int: Number of JSON files removed
    """
    json_count = 0
    for root, _, files in os.walk(bids_dir):
        json_files = [f for f in files if f.endswith('.json')]
        for json_file in json_files:
            file_path = os.path.join(root, json_file)
            try:
                os.remove(file_path)
                logger.info(f"Removed: {file_path}")
                json_count += 1
            except OSError as e:
                logger.error(f"Error removing {file_path}: {e}")
    return json_count

def zip_dwi_files(bids_dir: str) -> int:
    """
    Zip DWI files in the BIDS directory.
    
    Parameters:
    bids_dir (str): Path to BIDS directory
    
    Returns:
    int: Number of DWI files zipped
    """
    zip_count = 0
    for root, _, files in os.walk(bids_dir):
        dwi_files = [f for f in files if f.endswith('.nii.gz') and 'dwi' in f.lower()]
        for dwi_file in dwi_files:
            file_path = os.path.join(root, dwi_file)
            zip_path = file_path + '.zip'
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(file_path, os.path.basename(file_path))
                os.remove(file_path)  # Remove original file after zipping
                logger.info(f"Zipped: {file_path}")
                zip_count += 1
            except Exception as e:
                logger.error(f"Error zipping {file_path}: {e}")
    return zip_count

def update_csv_file(csv_file: str) -> None:
    """
    Update CSV file with zip file references.
    
    Parameters:
    csv_file (str): Path to CSV file
    """
    try:
        df = pd.read_csv(csv_file)
        # Update file paths to include .zip extension for DWI files
        df.loc[df['image_file'].str.contains('dwi', case=False, na=False), 'image_file'] += '.zip'
        df.to_csv(csv_file, index=False)
        logger.info(f"Updated CSV file: {csv_file}")
    except Exception as e:
        logger.error(f"Error updating CSV file: {e}")

def finalize(config: Dict[str, Any]):
    """Finalize the pipeline for upload."""
    # Set up logging
    setup_logging(config)

    logger.info(f"Starting finalization for upload...")
    logger.info(f"BIDS Directory: {config.paths.bids_dir}")
    logger.info(f"CSV File: {config.csv_files.final_csv}")

    # Step 1: Remove JSON files
    logger.info("Step 1: Removing JSON files...")
    json_count = remove_json_files(config.paths.bids_dir)
    logger.info(f"Removed {json_count} JSON files")

    # Step 2: Zip DWI files
    logger.info("Step 2: Zipping DWI files...")
    zip_count = zip_dwi_files(config.paths.bids_dir)
    logger.info(f"Zipped {zip_count} DWI files")

    # Step 3: Update CSV file
    logger.info("Step 3: Updating CSV file...")
    update_csv_file(config.csv_files.final_csv)

    logger.info("Finalization complete!")

def main():
    """Main function to run the finalize pipeline."""
    config = load_config('config.yaml')
    finalize(config)

if __name__ == "__main__":
    main() 