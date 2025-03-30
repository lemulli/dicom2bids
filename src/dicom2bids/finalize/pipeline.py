#!/usr/bin/env python3
# pipeline.py

import os
import json
from pathlib import Path
from ..utils.logging import setup_logging
from typing import Dict, Any

def finalize_pipeline(config: Dict[str, Any]):
    """Finalize the BIDS pipeline by performing final checks and cleanup."""
    # Set up logging
    logger = setup_logging(config)
    
    # Convert string paths to Path objects
    bids_dir = Path(config.paths.bids_dir)
    
    logger.info("Starting pipeline finalization")
    logger.info(f"Using BIDS directory: {bids_dir}")
    
    # Check for required BIDS files
    required_files = [
        "dataset_description.json",
        "participants.tsv",
        "README",
        "CHANGES"
    ]
    
    missing_files = []
    for file in required_files:
        if not (bids_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing required BIDS files: {', '.join(missing_files)}")
        return
    
    # Check for empty directories
    empty_dirs = []
    for dirpath, dirnames, filenames in os.walk(bids_dir):
        if not dirnames and not filenames and dirpath != str(bids_dir):
            empty_dirs.append(dirpath)
    
    if empty_dirs:
        logger.warning(f"Found empty directories: {', '.join(empty_dirs)}")
    
    # Validate JSON files
    json_files = list(bids_dir.rglob("*.json"))
    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                json.load(f)
            logger.info(f"Validated JSON file: {json_file.name}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_file.name}: {e}")
    
    logger.info("Pipeline finalization completed") 