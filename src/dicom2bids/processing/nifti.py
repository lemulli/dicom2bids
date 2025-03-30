#!/usr/bin/env python3
# nifti.py

import os
import nibabel as nib
from pathlib import Path
from ..utils.logging import setup_logging
import json
from typing import Dict, Any

def calculate_nifti_stats(config: Dict[str, Any]):
    """
    Calculate statistics for NIfTI files.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    """
    # Set up logging
    logger = setup_logging(config)
    
    # Convert string paths to Path objects
    bids_dir = Path(config.paths.bids_dir)
    
    logger.info("Starting NIfTI statistics calculation")
    logger.info(f"Using BIDS directory: {bids_dir}")
    
    # Find all NIfTI files
    nifti_files = list(bids_dir.rglob("*.nii.gz"))
    logger.info(f"Found {len(nifti_files)} NIfTI files")
    
    # Process each file
    for nifti_file in nifti_files:
        try:
            # Load NIfTI file
            img = nib.load(str(nifti_file))
            data = img.get_fdata()
            
            # Calculate basic statistics
            stats = {
                "min": float(data.min()),
                "max": float(data.max()),
                "mean": float(data.mean()),
                "std": float(data.std())
            }
            
            # Save statistics to JSON file
            stats_file = nifti_file.with_suffix(".json")
            with open(stats_file, "w") as f:
                json.dump(stats, f, indent=4)
            
            logger.info(f"Calculated statistics for {nifti_file.name}")
            
        except Exception as e:
            logger.error(f"Error processing {nifti_file.name}: {e}")
            continue
    
    logger.info("NIfTI statistics calculation completed") 