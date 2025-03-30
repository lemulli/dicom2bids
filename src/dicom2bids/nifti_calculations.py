#!/usr/bin/env python3
# nifti_calculations.py

import os
import sys
import logging
import pandas as pd
import nibabel as nib
import numpy as np
import tempfile
import zipfile
from pathlib import Path
from .utils import get_output_path

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def get_nifti_metadata(file_path):
    """
    Extract key metadata from a NIfTI file.
    
    Parameters:
    file_path (str): Path to the .nii or .nii.gz file
    
    Returns:
    dict: Dictionary containing metadata information
    """
    # Load the NIfTI image
    img = nib.load(file_path)
    
    # Get the header
    header = img.header
    
    # Get basic dimensions
    dimensions = len(header.get_data_shape())
    
    # Get voxel sizes (spatial units)
    voxel_sizes = header.get_zooms()
    
    # Get orientation information
    orientation = nib.aff2axcodes(img.affine)
    
    # Get the units
    spatial_units = header.get_xyzt_units()[0]
    temporal_units = header.get_xyzt_units()[1]
    
    # Get the extent (bounding box)
    extent = calculate_extent(img)
    
    # Get the photomet
    photomet = get_photomet(header.get_data_dtype().name, dimensions)
    
    # Get the fov
    fov = get_fov(header)

    # Create metadata dictionary
    metadata = {
        'photomet_interpret': photomet,
        'mri_field_of_view_pd': fov,
        'image_orientation': get_orientation_plane(orientation)
    }
    
    # Add units based on dimensions
    if dimensions > 4:
        for i in range(dimensions):
            metadata[f'image_unit{i+1}'] = get_unit_name(spatial_units)
    else:
        for i in range(3):
            metadata[f'image_unit{i+1}'] = get_unit_name(spatial_units)
        metadata[f'image_unit4'] = get_unit_name(temporal_units)
    
    # Add extent information
    for i, ext in enumerate(extent.values()):
        metadata[f'image_extent{i+1}'] = int(ext)
    
    # Get resolutions (zooms)
    zooms = header.get_zooms()
    for i, res in enumerate(zooms):
        metadata[f'image_resolution{i+1}'] = float(res)
    
    return metadata

def get_orientation_plane(orientation):
    """Determine the orientation plane from the affine matrix codes."""
    if isinstance(orientation, str):
        orientation = tuple(orientation)
    
    view_direction = orientation[2]
    
    if view_direction in ['S', 'I']:
        return 'Axial'      # looking from top/bottom
    elif view_direction in ['A', 'P']:
        return 'Coronal'    # looking from front/back
    elif view_direction in ['L', 'R']:
        return 'Sagittal'   # looking from sides
    else:
        return 'unknown'

def get_fov(header):
    """Calculate the field of view from dimensions and pixel spacing."""
    dims = header.get_data_shape()
    zooms = header.get_zooms()
    fovs = [dims[i] * zooms[i] for i in range(min(3, len(dims)))]
    return max(fovs)

def get_photomet(data_type, dimensions):
    """Determine the photometric interpretation from data type."""
    if data_type in ["uint8", "uint16", "int16", "float32", "float64"]:
        return "MONOCHROME2"
    return "UNKNOWN"

def calculate_extent(img):
    """Calculate the physical extent of the image in world coordinates."""
    dims = img.shape
    
    if len(dims) == 2:
        corners = np.array(list(np.ndindex((2, 2))))
        corners = corners * (np.array(dims[:2]) - 1)
        corners = np.column_stack((corners, np.zeros(len(corners))))
    else:
        corners = np.array(list(np.ndindex((2, 2, 2))))
        corners = corners * (np.array(dims[:3]) - 1)
    
    world_corners = nib.affines.apply_affine(img.affine, corners)

    if len(dims) == 2:
        extent = {
            'x': float(np.max(world_corners[:, 0]) - np.min(world_corners[:, 0])),
            'y': float(np.max(world_corners[:, 1]) - np.min(world_corners[:, 1]))
        }
    else:
        extent = {
            'x': float(np.max(world_corners[:, 0]) - np.min(world_corners[:, 0])),
            'y': float(np.max(world_corners[:, 1]) - np.min(world_corners[:, 1])),
            'z': float(np.max(world_corners[:, 2]) - np.min(world_corners[:, 2]))
        }
    
    if len(dims) == 4:
        extent['t'] = float(dims[3])
        
    return extent

def get_unit_name(unit_code):
    """Convert NIfTI unit codes to human-readable strings."""
    units = {
        0: 'unknown',
        'm': 'Meters',
        'mm': 'Millimeters',
        'um': 'Microns',
        'sec': 'Seconds',
        'ms': 'Milliseconds',
        'us': 'Microseconds',
        'Hz': 'Hertz',
        40: 'ppm',
        48: 'radian'
    }
    return units.get(unit_code, f'unknown code: {unit_code}')

def process_nifti_file(file_path):
    """Process a single NIfTI file, handling both regular and zipped files."""
    try:
        if file_path.endswith('.zip'):
            with tempfile.TemporaryDirectory() as temp_dir:
                logger.info(f"Processing zip file: {file_path}")
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    nifti_files = [f for f in zip_ref.namelist() if f.endswith('.nii.gz')]
                    if not nifti_files:
                        logger.warning(f"No .nii.gz files found in zip: {file_path}")
                        return None
                    
                    nifti_file = nifti_files[0]
                    zip_ref.extract(nifti_file, temp_dir)
                    file_path = os.path.join(temp_dir, nifti_file)
                    logger.info(f"Extracted to: {file_path}")

        metadata = get_nifti_metadata(file_path)
        return metadata
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return None

def main(input_csv: str = None):
    """
    Main function to process NIfTI files and extract metadata.
    
    Parameters:
    input_csv (str): Path to input CSV file containing image_file paths
    """
    if input_csv is None:
        if len(sys.argv) != 2:
            print(f"Usage: {sys.argv[0]} <input_csv>")
            sys.exit(1)
        input_csv = sys.argv[1]

    # Get output path in same directory as input
    input_path = Path(input_csv)
    output_csv = str(input_path.parent / f"{input_path.stem}_with_nifti{input_path.suffix}")

    logger.info(f"Reading input CSV: {input_csv}")
    df = pd.read_csv(input_csv)
    
    # Process each row
    for idx, row in df.iterrows():
        logger.info(f"Processing row {idx+1}/{len(df)}")
        file_path = row['image_file']
        
        metadata = process_nifti_file(file_path)
        if metadata:
            for key, value in metadata.items():
                if key not in df.columns:
                    df[key] = None
                df.at[idx, key] = value
    
    # Convert dates to datetime and format as MM/DD/YYYY
    if 'interview_date' in df.columns:
        df['interview_date'] = pd.to_datetime(df['interview_date']).dt.strftime('%m/%d/%Y')
    if 'procdate' in df.columns:
        df['procdate'] = pd.to_datetime(df['procdate']).dt.strftime('%m/%d/%Y')
    
    logger.info(f"Writing output CSV: {output_csv}")
    df.to_csv(output_csv, index=False)
    logger.info("Processing complete.")

if __name__ == "__main__":
    main() 