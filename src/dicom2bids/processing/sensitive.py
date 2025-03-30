#!/usr/bin/env python3
# sensitive.py

import os
import json
from pathlib import Path
from ..utils.logging import setup_logging
from typing import Dict, Any

def check_sensitive_data(config: Dict[str, Any]):
    """
    Check for sensitive data in the BIDS directory.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    """
    # Set up logging
    logger = setup_logging(config)
    
    # Convert string paths to Path objects
    bids_dir = Path(config.paths.bids_dir)
    
    logger.info("Starting sensitive data check")
    logger.info(f"Using BIDS directory: {bids_dir}")
    
    # Find all JSON files
    json_files = list(bids_dir.rglob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files to check")
    
    # Define sensitive fields to check
    sensitive_fields = [
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "PatientAddress",
        "PhysicianName",
        "InstitutionName",
        "InstitutionAddress"
    ]
    
    # Process each file
    for json_file in json_files:
        try:
            # Read JSON file
            with open(json_file, "r") as f:
                data = json.load(f)
            
            # Check for sensitive fields
            found_sensitive = []
            for field in sensitive_fields:
                if field in data:
                    found_sensitive.append(field)
            
            if found_sensitive:
                logger.warning(f"Found sensitive fields in {json_file.name}: {', '.join(found_sensitive)}")
            else:
                logger.info(f"No sensitive fields found in {json_file.name}")
            
        except Exception as e:
            logger.error(f"Error checking {json_file.name}: {e}")
            continue
    
    logger.info("Sensitive data check completed") 