#!/usr/bin/env python3
# cleanup.py

import os
import shutil
from pathlib import Path
from ..utils.logging import setup_logging
from typing import Dict, Any

def cleanup_files(config: Dict[str, Any]):
    """
    Clean up temporary files and directories.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    """
    # Set up logging
    logger = setup_logging(config)
    
    # Get paths from config
    bids_dir = Path(config['paths']['bids_dir'])
    
    logger.info("Starting cleanup")
    logger.info(f"Using BIDS directory: {bids_dir}")
    
    try:
        # Remove temporary files and directories
        for item in bids_dir.glob('**/*'):
            if item.is_file():
                # Remove temporary files
                if item.suffix in ['.tmp', '.temp']:
                    item.unlink()
                    logger.info(f"Removed temporary file: {item}")
                
                # Remove empty files
                if item.stat().st_size == 0:
                    item.unlink()
                    logger.info(f"Removed empty file: {item}")
            
            elif item.is_dir():
                # Remove empty directories
                try:
                    item.rmdir()  # This will only succeed if the directory is empty
                    logger.info(f"Removed empty directory: {item}")
                except OSError:
                    pass  # Directory not empty, skip it
        
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

    # Remove leftover 'dti' directories
    try:
        for dti_dir in bids_dir.glob('**/dti'):
            if dti_dir.is_dir():
                shutil.rmtree(str(dti_dir))
                logger.info(f"Removed DTI directory: {dti_dir}")
    except Exception as e:
        logger.error(f"Error removing DTI directories: {e}")

    # Gzip NIfTI files if configured
    if config['processing']['compress_nifti']:
        try:
            for nifti_file in bids_dir.glob('**/*.nii'):
                if nifti_file.is_file():
                    try:
                        # Create gzipped version
                        with open(nifti_file, 'rb') as f_in:
                            with open(str(nifti_file) + '.gz', 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        # Remove original file
                        nifti_file.unlink()
                        logger.info(f"Compressed NIfTI file: {nifti_file}")
                    except Exception as e:
                        logger.error(f"Error compressing {nifti_file}: {e}")
        except Exception as e:
            logger.error(f"Error during NIfTI compression: {e}")

    # Set up small files log
    small_files_log = str(Path(config.paths.log_dir) / "small_files.log")
    with open(small_files_log, "w") as f:
        f.write("=== Small NIfTI Files Report ===\n\n")

    # Identify suspiciously small .nii.gz in dwi
    for subject_dir in bids_dir.iterdir():
        if subject_dir.is_dir():
            dwi_path = subject_dir / "ses-01" / "dwi"
            if dwi_path.exists():
                file_groups = {}
                for f in dwi_path.iterdir():
                    if f.is_file():
                        base_stem = f.stem
                        if base_stem.endswith(".nii"):
                            base_stem = base_stem[:-4]
                        group_key = base_stem[-5:]
                        file_groups.setdefault(group_key, []).append(f)

                questionable_dir = subject_dir / "ses-01" / "questionable"
                questionable_dir.mkdir(exist_ok=True)

                for key, files in file_groups.items():
                    small_files = []
                    for f in files:
                        if f.suffix == ".gz":
                            size = f.stat().st_size
                            if size < 1_000_000:
                                small_files.append((f, size))
                    
                    if small_files:
                        with open(small_files_log, "a") as f:
                            f.write(f"\nSubject: {subject_dir.name}\n")
                            f.write(f"Group: {key}\n")
                            f.write("Small files found:\n")
                            for file_path, size in small_files:
                                size_mb = size / (1024 * 1024)  # Convert bytes to MB
                                f.write(f"  - {file_path.name}: {size_mb:.2f} MB\n")
                            f.write("\n")
                        
                        for file_path, _ in small_files:
                            dest = questionable_dir / file_path.name
                            try:
                                shutil.move(str(file_path), str(dest))
                                logger.info(f"Moved small file {file_path.name} -> {dest}")
                            except Exception as e:
                                logger.warning(f"Could not move {file_path.name}: {e}")

    # Rename '_b0_' -> '_b500_1000_', remove 'CANB'
    for subject_dir in bids_dir.iterdir():
        if subject_dir.is_dir():
            dwi_path = subject_dir / "ses-01" / "dwi"
            if dwi_path.exists():
                for f in dwi_path.iterdir():
                    if "_b0_" in f.name:
                        new_name = f.name.replace("_b0_", "_b500_1000_")
                        new_path = dwi_path / new_name
                        f.rename(new_path)
                        logger.info(f"Renamed {f.name} -> {new_name}")

            fmri_path = subject_dir / "ses-01" / "fmri"
            if fmri_path.exists():
                for f in fmri_path.iterdir():
                    if "CANB" in f.name:
                        new_name = f.name.replace("CANB", "")
                        new_path = fmri_path / new_name
                        f.rename(new_path)
                        logger.info(f"Renamed {f.name} -> {new_name}") 