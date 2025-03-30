#!/usr/bin/env python3
# finalize_upload.py

import os
import sys
import logging
import argparse
import zipfile
import pandas as pd
from pathlib import Path
from typing import List, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
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
    Zip DWI files (bvec, bval, nii.gz) and remove original files.
    
    Parameters:
    bids_dir (str): Path to BIDS directory
    
    Returns:
    int: Number of DWI files zipped
    """
    zip_count = 0
    for root, _, files in os.walk(bids_dir):
        bvec_files = [f for f in files if f.endswith('.bvec')]
        for bvec_file in bvec_files:
            stem = os.path.splitext(bvec_file)[0]
            matching_files = [
                os.path.join(root, f) for f in files 
                if f.startswith(stem) and f.endswith(('.bvec', '.bval', '.nii.gz'))
            ]
            
            if matching_files:
                zip_name = os.path.join(root, f"{stem}.zip")
                try:
                    with zipfile.ZipFile(zip_name, 'w') as zipf:
                        for file in matching_files:
                            zipf.write(file, os.path.basename(file))
                            logger.info(f"Added {os.path.basename(file)} to {zip_name}")
                    
                    # Remove original files
                    for file in matching_files:
                        try:
                            os.remove(file)
                            logger.info(f"Removed: {file}")
                            zip_count += 1
                        except OSError as e:
                            logger.error(f"Error removing {file}: {e}")
                except Exception as e:
                    logger.error(f"Error creating zip file {zip_name}: {e}")
    
    return zip_count

def update_csv_file(csv_path: str) -> None:
    """
    Update CSV file to replace .nii.gz with .zip for DWI files.
    
    Parameters:
    csv_path (str): Path to CSV file
    """
    try:
        df = pd.read_csv(csv_path)
        # For rows containing 'dwi', replace .nii.gz with .zip in image_file column
        mask = df['image_file'].str.contains('dwi', case=False, na=False)
        df.loc[mask, 'image_file'] = df.loc[mask, 'image_file'].str.replace('.nii.gz', '.zip')
        
        # Save the updated dataframe back to CSV
        df.to_csv(csv_path, index=False)
        logger.info(f"Updated CSV file: {csv_path}")
    except Exception as e:
        logger.error(f"Error updating CSV file {csv_path}: {e}")

def main():
    """
    Main function to finalize BIDS directory for upload by removing JSON files,
    zipping DWI files, and updating CSV file.
    """
    parser = argparse.ArgumentParser(description='Finalize BIDS directory for upload by removing JSON files, zipping DWI files, and updating CSV')
    parser.add_argument('bids_dir', help='Path to BIDS directory')
    parser.add_argument('csv_file', help='Path to CSV file to update')
    
    args = parser.parse_args()

    logger.info(f"Starting finalization for upload...")
    logger.info(f"BIDS Directory: {args.bids_dir}")
    logger.info(f"CSV File: {args.csv_file}")

    # Step 1: Remove JSON files
    logger.info("Step 1: Removing JSON files...")
    json_count = remove_json_files(args.bids_dir)
    logger.info(f"Removed {json_count} JSON files")

    # Step 2: Zip DWI files
    logger.info("Step 2: Zipping DWI files...")
    zip_count = zip_dwi_files(args.bids_dir)
    logger.info(f"Zipped {zip_count} DWI files")

    # Step 3: Update CSV file
    logger.info("Step 3: Updating CSV file...")
    update_csv_file(args.csv_file)

    logger.info("Finalization complete!")

if __name__ == "__main__":
    main() 