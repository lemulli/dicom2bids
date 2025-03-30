#!/usr/bin/env python3
# utils.py

import os
from pathlib import Path

def get_output_dir(input_file: str, output_type: str = 'csv') -> Path:
    """
    Get the standardized output directory based on the input file location.
    Creates an 'outputs' directory with subdirectories for different types of outputs.
    
    Parameters:
    input_file (str): Path to the input file
    output_type (str): Type of output ('csv', 'log', etc.)
    
    Returns:
    Path: Path to the output directory
    """
    input_path = Path(input_file)
    output_dir = input_path.parent / 'outputs' / output_type
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def get_output_path(input_file: str, suffix: str, output_type: str = 'csv') -> Path:
    """
    Generate a standardized output path based on the input file name and suffix.
    
    Parameters:
    input_file (str): Path to the input file
    suffix (str): Suffix to append to the filename (e.g., '_enriched', '_with_nifti')
    output_type (str): Type of output ('csv', 'log', etc.)
    
    Returns:
    Path: Path to the output file
    """
    input_path = Path(input_file)
    output_dir = get_output_dir(input_file, output_type)
    output_name = input_path.stem + suffix + input_path.suffix
    return output_dir / output_name 