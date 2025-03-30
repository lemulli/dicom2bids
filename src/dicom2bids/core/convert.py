#!/usr/bin/env python3
# convert.py

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from ..utils.logging import setup_logging

def check_dcm2niix():
    """Check if dcm2niix is installed and accessible."""
    try:
        subprocess.run(['dcm2niix', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def convert_dicoms(config: Dict[str, Any]):
    """
    Convert DICOM files to NIfTI format using dcm2niix.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    """
    # Set up logging
    logger = setup_logging(config)
    
    # Get paths from config
    dicom_dir = Path(config['paths']['dicom_dir'])
    bids_dir = Path(config['paths']['bids_dir'])
    log_dir = Path(config['paths']['log_dir'])
    
    # Create BIDS directory if it doesn't exist
    bids_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up log files
    conversion_log = str(log_dir / "dcm2niix.log")
    errors_log = str(log_dir / "dcm2niix.err")
    
    # Run dcm2niix on each DICOM directory
    for dicom_subdir in dicom_dir.iterdir():
        if dicom_subdir.is_dir():
            try:
                # Create corresponding output subdirectory
                output_subdir = bids_dir / dicom_subdir.name
                output_subdir.mkdir(parents=True, exist_ok=True)
                
                # Run dcm2niix
                cmd = [
                    'dcm2niix',
                    '-z', 'y' if config['processing']['compress_nifti'] else 'n',
                    '-f', '%f_%p_%t_%s',
                    '-o', str(output_subdir),
                    str(dicom_subdir)
                ]
                
                with open(conversion_log, 'a') as log, open(errors_log, 'a') as err:
                    subprocess.run(cmd, stdout=log, stderr=err, check=True)
                
                logger.info(f"Successfully converted {dicom_subdir.name}")
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Error converting {dicom_subdir.name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error processing {dicom_subdir.name}: {e}")
    
    logger.info("DICOM conversion completed") 