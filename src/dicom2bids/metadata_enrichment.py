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
from .main import Config, load_config
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


def copy_nii_and_sidecars(row, old_bids_dir: str, new_bids_dir: str) -> str:
    """
    Given a row with subject ID and scan type, find the largest matching .nii.gz
    in the OLD BIDS directory and copy it (plus .json, .bvec, .bval)
    to a mirrored path under NEW BIDS dir.
    Returns the new path to the .nii.gz, or None if not found.
    """
    subject_id = row["src_subject_id"]
    if not subject_id:
        logger.warning("No subject ID found in row.")
        return None

    # Convert subject ID to directory format
    subject_dir = convert_subject_id_to_dir(subject_id)
    logger.info(f"Converted subject ID {subject_id} to directory format {subject_dir}")

    scan_type = row.get("scan_type", "")
    img_description = row.get("image_description", "")

    # Construct path to subject's directory
    old_dir_path = os.path.join(old_bids_dir, subject_dir, "ses-01")
    logger.info(f"Looking for subject directory: {old_dir_path}")
    if not os.path.exists(old_dir_path):
        logger.warning(f"Subject directory not found: {old_dir_path}")
        return None

    # Decide subdirectory by scan type
    if scan_type == "MR structural (T2)":
        old_dir_path = os.path.join(old_dir_path, "anat", "T2")
    elif scan_type == "MR diffusion":
        old_dir_path = os.path.join(old_dir_path, "dwi")
    elif scan_type == "fMRI":
        old_dir_path = os.path.join(old_dir_path, "fmri")

    logger.info(f"Looking for scan type directory: {old_dir_path}")
    if not os.path.exists(old_dir_path):
        logger.warning(f"Scan type directory not found: {old_dir_path}")
        return None

    # Build new_dir by taking the relative path from old_bids_dir
    rel_path = os.path.relpath(old_dir_path, start=old_bids_dir)
    new_dir_path = os.path.join(new_bids_dir, rel_path)
    logger.info(f"Creating new directory: {new_dir_path}")
    os.makedirs(new_dir_path, exist_ok=True)

    # Gather .nii.gz files
    files = os.listdir(old_dir_path)
    logger.info(f"Found files in {old_dir_path}: {files}")
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

    logger.info(f"Found matching .nii.gz candidates: {nii_candidates}")
    if not nii_candidates:
        logger.warning(f"No matching .nii.gz for {img_description} in {old_dir_path}")
        return None

    # Pick largest file
    largest_file = max(nii_candidates, key=lambda x: os.path.getsize(os.path.join(old_dir_path, x)))
    old_largest_file_path = os.path.join(old_dir_path, largest_file)
    new_largest_file_path = os.path.join(new_dir_path, largest_file)

    logger.info(f"Copying from {old_largest_file_path} to {new_largest_file_path}")
    # Copy the NIfTI using shutil (or os.system('cp'))
    shutil.copy2(old_largest_file_path, new_largest_file_path)
    logger.info(f"Copied {old_largest_file_path} -> {new_largest_file_path}")

    # Copy .json
    old_json_path = old_largest_file_path.replace('.nii.gz', '.json')
    new_json_path = new_largest_file_path.replace('.nii.gz', '.json')
    if os.path.exists(old_json_path):
        shutil.copy2(old_json_path, new_json_path)
        logger.info(f"Copied {old_json_path} -> {new_json_path}")

    # Copy bvec/bval
    old_bvec = old_largest_file_path.replace('.nii.gz', '.bvec')
    old_bval = old_largest_file_path.replace('.nii.gz', '.bval')
    new_bvec = new_largest_file_path.replace('.nii.gz', '.bvec')
    new_bval = new_largest_file_path.replace('.nii.gz', '.bval')
    if os.path.exists(old_bvec):
        shutil.copy2(old_bvec, new_bvec)
        logger.info(f"Copied {old_bvec} -> {new_bvec}")
    if os.path.exists(old_bval):
        shutil.copy2(old_bval, new_bval)
        logger.info(f"Copied {old_bval} -> {new_bval}")

    return new_largest_file_path


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


def main():
    """Main function to run the metadata enrichment pipeline."""
    config = load_config('config.yaml')
    metadata_enrichment(config)


if __name__ == "__main__":
    main()