#!/usr/bin/env python3
# organize.py

import shutil
from pathlib import Path
from ..utils.logging import setup_logging
from typing import Dict, Any

def generate_bids_structure(base_path: Path, config: Dict[str, Any]):
    """Create partial BIDS subfolders for each subject."""
    # Set up logging
    logger = setup_logging(config)
    
    # Create the base directory if it doesn't exist
    base_path.mkdir(parents=True, exist_ok=True)
    
    # Define the BIDS subfolders to create
    bids_folders = [
        "anat",  # For anatomical scans (T1, T2)
        "dwi",   # For diffusion-weighted imaging
        "fmri",  # For functional MRI
        "localized",  # For localized scans
        "questionable"  # For questionable data
    ]
    
    # Create each subfolder
    for folder in bids_folders:
        folder_path = base_path / folder
        try:
            folder_path.mkdir(exist_ok=True)
            logger.info(f"Created BIDS subfolder: {folder}")
        except Exception as e:
            logger.error(f"Error creating folder {folder}: {e}")

def sort_files(base_path: Path, config: Dict[str, Any]):
    """Organize files into the correct BIDS subfolders based on their naming conventions."""
    # Set up logging
    logger = setup_logging(config)
    
    # Define file patterns and their corresponding folders
    file_patterns = {
        "localized": ["*localizer*", "*localised*"],
        "anat": ["*t1*", "*t2*", "*anat*"],
        "dwi": ["*dwi*", "*dti*"],
        "fmri": ["*fmri*", "*bold*", "*func*"]
    }
    
    # Process each pattern and move files to appropriate folders
    for folder, patterns in file_patterns.items():
        folder_path = base_path / folder
        if not folder_path.exists():
            logger.warning(f"Folder {folder} does not exist, skipping")
            continue
            
        for pattern in patterns:
            try:
                # Find all matching files
                matching_files = list(base_path.glob(pattern))
                
                # Move each matching file to the appropriate folder
                for file in matching_files:
                    try:
                        shutil.move(str(file), str(folder_path / file.name))
                        logger.info(f"Moved {file.name} to {folder}")
                    except Exception as e:
                        logger.error(f"Error moving file {file.name}: {e}")
                        
            except Exception as e:
                logger.error(f"Error processing pattern {pattern}: {e}")

def organize_files(config: Dict[str, Any]):
    """Organize the BIDS directory structure and sort files."""
    # Set up logging
    logger = setup_logging(config)
    
    # Convert string paths to Path objects
    bids_dir = Path(config['paths']['bids_dir'])
    
    logger.info("Starting BIDS organization")
    logger.info(f"Using BIDS directory: {bids_dir}")
    
    # Generate the BIDS directory structure
    generate_bids_structure(bids_dir, config)
    
    # Sort files into appropriate folders
    sort_files(bids_dir, config)
    
    logger.info("BIDS organization completed") 