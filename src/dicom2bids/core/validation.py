#!/usr/bin/env python3
# validation.py

import subprocess
from pathlib import Path
from typing import Dict, Any
from ..utils.logging import setup_logging

logger = setup_logging()

def validate_bids(config: Dict[str, Any]):
    """
    Validate the BIDS dataset using bids-validator.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    """
    bids_dir = Path(config.paths.bids_dir)
    
    # Check if bids-validator is installed
    try:
        subprocess.run(["bids-validator", "--version"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        logger.error("bids-validator is not installed. Please install it using: npm install -g bids-validator")
        return False
    except FileNotFoundError:
        logger.error("bids-validator is not found in PATH. Please install it using: npm install -g bids-validator")
        return False
    
    # Run bids-validator
    try:
        result = subprocess.run(
            ["bids-validator", str(bids_dir)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Check if there are any errors or warnings
        if "ERROR" in result.stdout or "WARNING" in result.stdout:
            logger.warning("BIDS validation found issues:")
            logger.warning(result.stdout)
            return False
        else:
            logger.info("BIDS validation passed successfully")
            return True
            
    except subprocess.CalledProcessError as e:
        logger.error(f"BIDS validation failed with error: {e.stderr}")
        return False

def check_required_files(config: Dict[str, Any]):
    """
    Check if all required BIDS files are present.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    
    Returns:
    bool: True if all required files are present, False otherwise
    """
    bids_dir = Path(config.paths.bids_dir)
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
        return False
    
    logger.info("All required BIDS files are present")
    return True

def check_directory_structure(config: Dict[str, Any]):
    """
    Check if the BIDS directory structure is correct.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    
    Returns:
    bool: True if directory structure is correct, False otherwise
    """
    bids_dir = Path(config.paths.bids_dir)
    
    # Check if there are any subject directories
    subject_dirs = [d for d in bids_dir.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    if not subject_dirs:
        logger.error("No subject directories found in BIDS directory")
        return False
    
    # Check each subject directory
    for subject_dir in subject_dirs:
        # Check if session directory exists
        session_dir = subject_dir / "ses-01"
        if not session_dir.exists():
            logger.error(f"Missing session directory in {subject_dir.name}")
            return False
        
        # Check if required modality directories exist
        required_dirs = ["anat", "dwi", "fmri"]
        for modality in required_dirs:
            modality_dir = session_dir / modality
            if not modality_dir.exists():
                logger.error(f"Missing {modality} directory in {session_dir}")
                return False
    
    logger.info("BIDS directory structure is correct")
    return True 