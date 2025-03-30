#!/usr/bin/env python3
# metadata_enrichment.py

import os
import sys
import shutil   # for file copying (instead of os.system('cp ...'))
import logging
import pandas as pd
import json
from datetime import date  # if you want to store a processing date
from pathlib import Path
from .config import Config
from .utils import get_output_path, setup_logging, setup_excluded_scans_logger

# Set up logging
logger = logging.getLogger(__name__)

def expand_for_scan_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand each row for multiple scan types: T2 axial, coronal, sagittal, DWI, fMRI, etc.
    This logic comes from the first notebook (01_constants_to_csv).
    """
    logger.info("Expanding CSV rows for multiple scan types...")
    expanded_rows = []

    for _, row in df.iterrows():
        # Create a copy of the entire row as a dictionary
        row_dict = row.to_dict()

        # T2 Axial
        row_ax = row_dict.copy()
        row_ax["scan_type"] = "MR structural (T2)"
        row_ax["image_description"] = "T2_axial"
        expanded_rows.append(row_ax)

        # T2 Coronal
        row_cor = row_dict.copy()
        row_cor["scan_type"] = "MR structural (T2)"
        row_cor["image_description"] = "T2_coronal"
        expanded_rows.append(row_cor)

        # T2 Sagittal
        row_sag = row_dict.copy()
        row_sag["scan_type"] = "MR structural (T2)"
        row_sag["image_description"] = "T2_sagittal"
        expanded_rows.append(row_sag)

        # DWI
        row_dwi = row_dict.copy()
        row_dwi["scan_type"] = "MR diffusion"
        row_dwi["image_description"] = "dwi b500_1000"
        expanded_rows.append(row_dwi)

        # fMRI
        row_fmri = row_dict.copy()
        row_fmri["scan_type"] = "fMRI"
        row_fmri["image_description"] = "bold, resting"
        expanded_rows.append(row_fmri)

    df_expanded = pd.DataFrame(expanded_rows)
    logger.info(f"Expanded from {len(df)} rows to {len(df_expanded)} rows.")
    return df_expanded


def convert_subject_id_to_dir(subject_id: str) -> str:
    """
    Convert subject ID from format 'MOMMAR-01-M' to directory format 'MOMMAR_01_M'
    """
    # Replace hyphens with underscores
    return subject_id.replace('-', '_')


def copy_nii_and_sidecars(row, old_bids_dir: str, new_bids_dir: str) -> tuple[str, str]:
    """
    Given a row with subject ID and scan type, find the largest matching .nii.gz
    in the OLD BIDS directory and copy it (plus .json, .bvec, .bval)
    to a mirrored path under NEW BIDS dir.
    Returns a tuple of (new_nii_path, reason) where reason is None if successful,
    or a string explaining why the file wasn't found/copied.
    """
    subject_id = row["src_subject_id"]
    if not subject_id:
        return None, "No subject ID found in row"

    # Convert subject ID to directory format
    subject_dir = convert_subject_id_to_dir(subject_id)
    logger.info(f"Converted subject ID {subject_id} to directory format {subject_dir}")

    scan_type = row.get("scan_type", "")
    img_description = row.get("image_description", "")

    # Construct path to subject's directory
    old_dir_path = os.path.join(old_bids_dir, subject_dir, "ses-01")
    if not os.path.exists(old_dir_path):
        return None, f"Subject directory not found: {old_dir_path}"

    # Decide subdirectory by scan type
    if scan_type == "MR structural (T2)":
        old_dir_path = os.path.join(old_dir_path, "anat", "T2")
    elif scan_type == "MR diffusion":
        old_dir_path = os.path.join(old_dir_path, "dwi")
    elif scan_type == "fMRI":
        old_dir_path = os.path.join(old_dir_path, "fmri")

    if not os.path.exists(old_dir_path):
        return None, f"Scan type directory not found: {old_dir_path}"

    # Build new_dir by taking the relative path from old_bids_dir
    rel_path = os.path.relpath(old_dir_path, start=old_bids_dir)
    new_dir_path = os.path.join(new_bids_dir, rel_path)
    os.makedirs(new_dir_path, exist_ok=True)

    # Gather .nii.gz files
    files = os.listdir(old_dir_path)
    nii_candidates = []
    desc_lower = img_description.lower()

    # Example logic for T2 subtypes
    if 'axial' in desc_lower:
        nii_candidates = [
            f for f in files
            if f.endswith('.nii.gz') and 'FETUS' in f and 'AX' in f and 'Eq' not in f
        ]
    elif 'coronal' in desc_lower:
        nii_candidates = [
            f for f in files
            if f.endswith('.nii.gz') and 'FETUS' in f and 'COR' in f and 'Eq' not in f
        ]
    elif 'sagittal' in desc_lower:
        nii_candidates = [
            f for f in files
            if f.endswith('.nii.gz') and 'FETUS' in f and 'SAG' in f and 'Eq' not in f
        ]
    elif 'bold' in desc_lower:
        nii_candidates = [f for f in files if f.endswith('.nii.gz') and 'bold' in f]
    elif '1000' in desc_lower:
        nii_candidates = [f for f in files if f.endswith('.nii.gz') and 'b500' in f]

    if not nii_candidates:
        return None, f"No matching .nii.gz files found for {img_description} in {old_dir_path}"

    # Pick largest file
    largest_file = max(nii_candidates, key=lambda x: os.path.getsize(os.path.join(old_dir_path, x)))
    old_largest_file_path = os.path.join(old_dir_path, largest_file)
    new_largest_file_path = os.path.join(new_dir_path, largest_file)

    # If source and destination are the same, just return the path
    if os.path.abspath(old_largest_file_path) == os.path.abspath(new_largest_file_path):
        return old_largest_file_path, None

    # Copy the NIfTI and sidecars
    try:
        shutil.copy2(old_largest_file_path, new_largest_file_path)
        
        # Copy .json
        old_json_path = old_largest_file_path.replace('.nii.gz', '.json')
        new_json_path = new_largest_file_path.replace('.nii.gz', '.json')
        if os.path.exists(old_json_path):
            shutil.copy2(old_json_path, new_json_path)

        # Copy bvec/bval
        old_bvec = old_largest_file_path.replace('.nii.gz', '.bvec')
        old_bval = old_largest_file_path.replace('.nii.gz', '.bval')
        new_bvec = new_largest_file_path.replace('.nii.gz', '.bvec')
        new_bval = new_largest_file_path.replace('.nii.gz', '.bval')
        if os.path.exists(old_bvec):
            shutil.copy2(old_bvec, new_bvec)
        if os.path.exists(old_bval):
            shutil.copy2(old_bval, new_bval)

        return new_largest_file_path, None
    except Exception as e:
        return None, f"Error copying files: {str(e)}"


def merge_json_data(json_map_dict, image_file_path, df, row_idx):
    """
    Given the newly-copied .nii.gz path and the mapping dictionary,
    read the matching .json sidecar, and copy values into the df row.
    This logic is from the second notebook (02_copy_to_new_dir_populate_csv).
    """
    if not image_file_path or pd.isna(image_file_path):
        return

    json_file_path = image_file_path.replace('.nii.gz', '.json')
    if not os.path.exists(json_file_path):
        logger.warning(f"No JSON found at {json_file_path}")
        return

    try:
        with open(json_file_path, 'r') as f:
            json_data = json.load(f)

        for json_key, csv_col in json_map_dict.items():
            if json_key in json_data:
                val = json_data[json_key]
                if isinstance(val, list):
                    val = str(val)  # convert list to string
                df.at[row_idx, csv_col] = val

    except Exception as e:
        logger.warning(f"Error parsing {json_file_path}: {e}")


def setup_summary_logger(config):
    """Set up a logger for the summary report"""
    summary_logger = logging.getLogger('summary')
    summary_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    for handler in summary_logger.handlers[:]:
        summary_logger.removeHandler(handler)
    
    # Create handlers
    summary_file = os.path.join(config.paths.log_dir, 'metadata_enrichment_summary.log')
    os.makedirs(os.path.dirname(summary_file), exist_ok=True)
    file_handler = logging.FileHandler(summary_file, mode='w')
    file_handler.setLevel(logging.INFO)
    
    # Create formatters and add it to handlers
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    summary_logger.addHandler(file_handler)
    
    return summary_logger


def main(config: Config):
    """
    Main function combining logic from both notebooks:
      1) Load skeleton CSV, expand & set constants
      2) Copy NIfTIs & sidecars, merge JSON metadata
    """
    # Set up logging
    setup_logging(config)
    excluded_scans_logger = setup_excluded_scans_logger(config)
    summary_logger = setup_summary_logger(config)
    
    # Get paths from config
    input_csv = config.csv_files.skeleton_csv
    old_bids_dir = config.paths.bids_dir
    new_bids_dir = config.paths.bids_dir
    t2_json_map = config.csv_files.json_map_csv
    output_csv = config.csv_files.final_csv

    logger.info(f"Reading input CSV: {input_csv}")
    # Skip the first row which contains 'image,3,...' and use the second row as header
    df = pd.read_csv(input_csv, skiprows=1)
    logger.info(f"Read {len(df)} rows from CSV.")
    logger.info(f"Columns in input CSV: {df.columns.tolist()}")

    # 1. (Optional) Add default constants (from 01_constants_to_csv)
    #    Adjust to your needs: sample placeholders below:
    df["scan_object"] = "Live"
    df["image_file_format"] = "NIFTI"
    df["procdate"] = date.today().strftime('%Y-%m-%d')  # today's date, or a fixed date
    # Add any others you want

    # 2. Expand for scan types (T2 axial, coronal, etc.)
    df_expanded = expand_for_scan_types(df)
    logger.info(f"Expanded to {len(df_expanded)} rows after adding scans.")
    logger.info(f"Columns in expanded CSV: {df_expanded.columns.tolist()}")
    logger.info(f"Sample row keys: {df_expanded.iloc[0].keys()}")

    # 3. Load T2 JSON mapping (which columns to pull from sidecar)
    logger.info(f"Loading T2 JSON mapping from: {t2_json_map}")
    t2_mapping = pd.read_csv(t2_json_map)
    logger.info(f"Loaded {len(t2_mapping)} entries in JSON map.")
    json_map_dict = dict(zip(t2_mapping['json_name'], t2_mapping['csv_name']))

    # 4. For each row, copy NIfTI & sidecars, then read JSON into the CSV
    rows_to_drop = []
    for idx, row in df_expanded.iterrows():
        logger.info(f"Processing row {idx+1}/{len(df_expanded)}...")
        logger.debug(f"Row data: {row.to_dict()}")
        new_nii_path, reason = copy_nii_and_sidecars(row, old_bids_dir, new_bids_dir)
        
        # Store the final file path in the CSV, so we can see where it actually lives
        if new_nii_path:
            df_expanded.at[idx, "image_file"] = new_nii_path
            merge_json_data(json_map_dict, new_nii_path, df_expanded, idx)
        else:
            df_expanded.at[idx, "image_file"] = None
            # Log excluded scan details
            excluded_scans_logger.info(f"Scan excluded from NIH DB - Subject: {row['src_subject_id']}, Scan Type: {row.get('scan_type', 'unknown')}, Description: {row.get('image_description', 'unknown')}, Reason: {reason}")
            rows_to_drop.append(idx)

    # Drop rows with missing files
    if rows_to_drop:
        logger.info(f"Dropping {len(rows_to_drop)} rows with missing files")
        df_expanded = df_expanded.drop(rows_to_drop)
        logger.info(f"Remaining rows after dropping missing files: {len(df_expanded)}")

    # 5. Write the final CSV
    logger.info(f"Writing final enriched CSV to: {output_csv}")
    df_expanded.to_csv(output_csv, index=False)
    logger.info("Metadata enrichment complete.")
    logger.info(f"Excluded scans log written to: {excluded_scans_logger.handlers[0].baseFilename}")

    # 7. Generate summary report
    summary_logger.info("=== Metadata Enrichment Summary Report ===\n")
    
    # Missing Subjects
    summary_logger.info("Missing Subjects (not found in BIDS directory):")
    missing_subjects = set(df['src_subject_id'].unique()) - set(df_expanded['src_subject_id'].unique())
    for subject in sorted(missing_subjects):
        summary_logger.info(f"  - {subject}")
    summary_logger.info(f"\nTotal missing subjects: {len(missing_subjects)}\n")
    
    # Missing Scans for Existing Subjects
    summary_logger.info("Missing Scans for Existing Subjects:")
    missing_scans = {}
    for idx, row in df_expanded.iterrows():
        if pd.isna(row['image_file']):
            subject = row['src_subject_id']
            if subject not in missing_scans:
                missing_scans[subject] = []
            missing_scans[subject].append({
                'scan_type': row['scan_type'],
                'description': row['image_description'],
                'reason': 'Scan not found in BIDS directory'
            })
    
    # Successfully Processed Files
    summary_logger.info("\nSuccessfully Processed Files for Upload:")
    processed_files = {}
    for idx, row in df_expanded.iterrows():
        if pd.notna(row['image_file']):
            subject = row['src_subject_id']
            if subject not in processed_files:
                processed_files[subject] = []
            processed_files[subject].append({
                'scan_type': row['scan_type'],
                'description': row['image_description'],
                'file': os.path.basename(row['image_file'])
            })
    
    for subject in sorted(processed_files.keys()):
        summary_logger.info(f"\nSubject: {subject}")
        for file_info in processed_files[subject]:
            summary_logger.info(f"  - {file_info['scan_type']} ({file_info['description']})")
            summary_logger.info(f"    File: {file_info['file']}")
    
    # Summary Statistics
    total_subjects = len(df['src_subject_id'].unique())
    missing_subjects_count = len(missing_subjects)
    existing_subjects = total_subjects - missing_subjects_count
    total_processed_files = sum(len(files) for files in processed_files.values())
    
    summary_logger.info(f"\nSummary Statistics:")
    summary_logger.info(f"Total subjects in CSV: {total_subjects}")
    summary_logger.info(f"Missing subjects: {missing_subjects_count}")
    summary_logger.info(f"Existing subjects: {existing_subjects}")
    summary_logger.info(f"Subjects with missing scans: {len(missing_scans)}")
    summary_logger.info(f"Total files processed for upload: {total_processed_files}")


if __name__ == "__main__":
    from .config import ConfigManager
    config_manager = ConfigManager()
    config = config_manager.get_config()
    main(config)