#!/usr/bin/env python3
# upload.py

import os
import shutil
from pathlib import Path
from ..utils.logging import setup_logging
from typing import Dict, Any

def prepare_for_upload(config: Dict[str, Any]):
    """
    Prepare the BIDS directory for upload.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    """
    # Set up logging
    logger = setup_logging(config)
    
    # Convert string paths to Path objects
    bids_dir = Path(config.paths.bids_dir)
    
    logger.info("Starting upload preparation")
    logger.info(f"Using BIDS directory: {bids_dir}")
    
    # Create a temporary directory for upload files
    upload_dir = bids_dir / "upload"
    upload_dir.mkdir(exist_ok=True)
    logger.info(f"Created upload directory: {upload_dir}")
    
    try:
        # Copy all files to upload directory
        for item in bids_dir.iterdir():
            if item.name != "upload":  # Skip the upload directory itself
                if item.is_file():
                    shutil.copy2(item, upload_dir)
                    logger.info(f"Copied file: {item.name}")
                elif item.is_dir():
                    shutil.copytree(item, upload_dir / item.name)
                    logger.info(f"Copied directory: {item.name}")
        
        # Create a zip file
        zip_path = bids_dir / f"{bids_dir.name}.zip"
        shutil.make_archive(str(zip_path.with_suffix("")), "zip", upload_dir)
        logger.info(f"Created zip file: {zip_path}")
        
        # Clean up temporary directory
        shutil.rmtree(upload_dir)
        logger.info("Removed temporary upload directory")
        
    except Exception as e:
        logger.error(f"Error preparing for upload: {e}")
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
            logger.info("Cleaned up temporary upload directory after error")
        return
    
    logger.info("Upload preparation completed") 