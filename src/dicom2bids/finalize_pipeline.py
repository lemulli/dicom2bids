#!/usr/bin/env python3
# finalize_pipeline.py

import os
import sys
import logging
import gzip
import shutil
import pandas as pd
from pathlib import Path
from typing import List, Dict
from .utils.config import Config
from .utils.logging import setup_logging

# Set up logging
logger = logging.getLogger(__name__)

def compress_dwi_files(bids_dir: str) -> Dict[str, List[str]]:
    """
    Compress uncompressed DWI files (.nii) to gzipped format (.nii.gz).
    Already compressed files (.nii.gz) are left untouched.
    
    Parameters:
    bids_dir (str): Path to BIDS directory
    
    Returns:
    Dict[str, List[str]]: Dictionary with lists of processed and skipped files
    """
    results = {
        'compressed': [],
        'already_compressed': [],
        'errors': []
    }
    
    for root, _, files in os.walk(bids_dir):
        # Find all DWI files
        dwi_files = [f for f in files if ('dwi' in f.lower() or 'dti' in f.lower())]
        for dwi_file in dwi_files:
            file_path = os.path.join(root, dwi_file)
            if file_path.endswith('.nii.gz'):
                logger.info(f"Skipping already compressed file: {file_path}")
                results['already_compressed'].append(file_path)
            elif file_path.endswith('.nii'):
                gz_path = file_path + '.gz'
                try:
                    # Compress the file using gzip
                    with open(file_path, 'rb') as f_in:
                        with gzip.open(gz_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    # Remove original uncompressed file after successful compression
                    os.remove(file_path)
                    logger.info(f"Compressed: {file_path} -> {gz_path}")
                    results['compressed'].append(file_path)
                except Exception as e:
                    error_msg = f"Error compressing {file_path}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
    return results

def update_csv_file(csv_file: str) -> Dict[str, int]:
    """
    Update CSV file with final metadata.
    
    Parameters:
    csv_file (str): Path to CSV file
    
    Returns:
    Dict[str, int]: Statistics about the updates
    """
    stats = {
        'total_rows': 0,
        'dwi_rows': 0,
        'updated_rows': 0
    }
    
    try:
        df = pd.read_csv(csv_file)
        stats['total_rows'] = len(df)
        
        # Count DWI rows
        dwi_mask = df['image_file'].str.contains('dwi|dti', case=False, na=False)
        stats['dwi_rows'] = dwi_mask.sum()
        
        # Add any final metadata updates here if needed
        # For example, update file paths, add upload status, etc.
        
        df.to_csv(csv_file, index=False)
        logger.info(f"Updated CSV file: {csv_file}")
        
    except Exception as e:
        logger.error(f"Error updating CSV file: {e}")
        stats['error'] = str(e)
    
    return stats

def main(config: Config):
    """
    Main function to finalize BIDS directory for upload by:
    1. Compressing uncompressed DWI files (.nii -> .nii.gz)
    2. Updating CSV file with final metadata
    
    Parameters:
    config (Config): Configuration object containing all necessary settings
    """
    # Set up logging
    setup_logging(config)
    
    print("\n=== Starting Pipeline Finalization ===")
    print(f"BIDS Directory: {config.paths.bids_dir}")
    print(f"CSV File: {config.csv_files.final_csv}\n")

    # Step 1: Check and compress DWI files if needed
    print("Step 1/2: Processing DWI files...")
    dwi_results = compress_dwi_files(config.paths.bids_dir)
    
    if dwi_results['compressed']:
        print("\nCompressed files:")
        for f in dwi_results['compressed']:
            print(f"  ✓ {os.path.basename(f)}")
    
    if dwi_results['already_compressed']:
        print("\nAlready compressed files:")
        for f in dwi_results['already_compressed']:
            print(f"  • {os.path.basename(f)}")
    
    if dwi_results['errors']:
        print("\nErrors during compression:")
        for error in dwi_results['errors']:
            print(f"  ✗ {error}")
    
    print(f"\n✓ Found {len(dwi_results['already_compressed'])} compressed DWI files")
    print(f"✓ Compressed {len(dwi_results['compressed'])} DWI files")
    if dwi_results['errors']:
        print(f"✗ Encountered {len(dwi_results['errors'])} errors\n")
    else:
        print("✓ No errors encountered\n")

    # Step 2: Update CSV file
    print("Step 2/2: Updating CSV file...")
    csv_stats = update_csv_file(config.csv_files.final_csv)
    
    if 'error' in csv_stats:
        print(f"✗ Error updating CSV: {csv_stats['error']}")
    else:
        print(f"✓ Updated CSV file with {csv_stats['total_rows']} total rows")
        print(f"  • {csv_stats['dwi_rows']} DWI/DTI entries")
        print(f"  • Located in: {config.csv_files.final_csv}\n")

    print("=== Pipeline Finalization Complete! ===")
    print(f"✓ Processed {len(dwi_results['compressed']) + len(dwi_results['already_compressed'])} DWI files total")
    print(f"✓ Updated CSV file: {config.csv_files.final_csv}")
    if dwi_results['errors']:
        print(f"✗ {len(dwi_results['errors'])} errors occurred - check logs for details\n")
    else:
        print("✓ No errors occurred\n")

if __name__ == "__main__":
    from .utils.config import ConfigManager
    config_manager = ConfigManager()
    config = config_manager.get_config()
    main(config) 