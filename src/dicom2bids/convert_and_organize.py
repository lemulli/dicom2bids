#!/usr/bin/env python3
# convert_and_organize.py
import os
import sys
import shutil
import logging
from pathlib import Path
from .utils import get_output_path, setup_logging
import subprocess
from .utils.config import Config
from datetime import datetime

################################################################################
# LOGGING CONFIGURATION
################################################################################
logger = logging.getLogger(__name__)

################################################################################
# FUNCTIONS
################################################################################

def check_dcm2niix() -> bool:
    """
    Check if dcm2niix is installed and accessible.
    
    Returns:
    bool: True if dcm2niix is installed and accessible, False otherwise
    """
    try:
        # Try to run dcm2niix with --version flag
        result = subprocess.run(['dcm2niix', '--version'], 
                              capture_output=True, 
                              text=True)
        # dcm2niix returns non-zero exit code even when version is printed successfully
        if "Chris Rorden's dcm2niiX version" in result.stdout:
            logger.info("dcm2niix is installed and accessible")
            return True
        else:
            logger.error("dcm2niix is installed but returned unexpected output")
            return False
    except FileNotFoundError:
        logger.error("dcm2niix is not installed or not in PATH")
        return False
    except Exception as e:
        logger.error(f"Error checking dcm2niix: {e}")
        return False

def create_bids_dir(old_dir: Path, new_dir: Path):
    """
    Copy the entire `old_dir` structure into `new_dir`.
    """
    if not new_dir.exists():
        new_dir.mkdir(parents=True)
    logger.info(f"Copying {old_dir} -> {new_dir}")
    shutil.copytree(old_dir, new_dir, dirs_exist_ok=True)
    logger.info("Finished copying directory structure.")

def run_dcm2niix_on_unprocessed(base_path: Path, config: Config):
    """
    Find folders with .dcm files, convert them to NIfTI, remove .dcm.
    """
    unprocessed_folders = []
    for subfolder in base_path.rglob("*"):
        if subfolder.is_dir() and any(subfolder.glob("*.dcm")):
            unprocessed_folders.append(subfolder)

    total_folders = len(unprocessed_folders)
    print(f"Found {total_folders} folders with DICOM files to process")

    for idx, folder_to_convert in enumerate(unprocessed_folders, 1):
        # Extract subject information from the path
        try:
            # Get the relative path from base_path to get the correct subject ID
            rel_path = folder_to_convert.relative_to(base_path)
            subject_id = rel_path.parts[0]  # First part of relative path is subject ID
            scan_folder = folder_to_convert.name
        except Exception as e:
            logger.warning(f"Could not extract subject info from path {folder_to_convert}: {e}")
            subject_id = "Unknown"
            scan_folder = folder_to_convert.name

        print(f"\nProcessing folder {idx}/{total_folders}:")
        print(f"Subject: {subject_id}")
        print(f"Folder: {scan_folder}")
        
        # Add header to log files in outputs/log directory
        conversion_log = str(Path(config.paths.log_dir) / "dcm2niix.log")
        errors_log = str(Path(config.paths.log_dir) / "dcm2niix.err")
        
        log_header = f"""
=== Processing DICOM folder ===
Subject ID: {subject_id}
Folder Name: {scan_folder}
Full Path: {folder_to_convert}
Number of DICOM files: {len(list(folder_to_convert.glob("*.dcm")))}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        with open(conversion_log, "a") as f:
            f.write(log_header)
        with open(errors_log, "a") as f:
            f.write(log_header)
        
        # Use -v for verbose output and -y to overwrite existing files
        cmd = f'dcm2niix -v y -y y -b y -z y -f "%d_%s" "{folder_to_convert}" >> {conversion_log} 2>> {errors_log}'
        logger.info(f"Running: {cmd}")
        os.system(cmd)

        # Remove DICOM files after conversion
        dcm_files = list(folder_to_convert.glob("*.dcm"))
        for df in dcm_files:
            try:
                os.remove(df)
                logger.info(f"Removed DICOM file: {df}")
            except Exception as e:
                logger.warning(f"Could not remove {df}: {e}")

def generate_bids_structure(base_path: Path):
    """
    For each subject, create partial BIDS subfolders (anat/T1, T2, dwi, fmri, etc.).
    """
    dirs_to_make = [
        "ses-01/anat/T1",
        "ses-01/anat/T2",
        "ses-01/dwi",
        "ses-01/fmri",
        "ses-01/localized",
        "ses-01/questionable"
    ]
    for subject_dir in base_path.iterdir():
        if subject_dir.is_dir():
            for d in dirs_to_make:
                path_to_make = subject_dir / d
                path_to_make.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created BIDS subfolders for {subject_dir.name}")

def sort_files(base_path: Path):
    """
    Move newly converted .nii.gz into correct subfolders:
        T1 -> anat/T1
        T2 -> anat/T2
        DTI/_dwi_ -> dwi
        bold_ -> fmri
        _LOC_ -> localized
    """
    logger.info(f"Starting file sorting in base path: {base_path}")
    
    # First, let's see what's in the base path
    logger.info("Contents of base path:")
    for item in base_path.iterdir():
        logger.debug(f"  - {item.name} (is_dir: {item.is_dir()})")
    
    for subject_dir in base_path.iterdir():
        logger.info(f"\nProcessing subject directory: {subject_dir}")
        if subject_dir.is_dir():
            logger.info(f"Found valid subject dir: {subject_dir}")
            
            # Let's see what's in the subject directory
            logger.info("Contents of subject directory:")
            for item in subject_dir.iterdir():
                logger.debug(f"  - {item.name} (is_dir: {item.is_dir()})")
            
            subject_ses01 = subject_dir / "ses-01"
            logger.info(f"Subject session directory: {subject_ses01}")
            
            # Check if the session directory exists and what's in it
            if subject_ses01.exists():
                logger.info("Contents of session directory:")
                for item in subject_ses01.iterdir():
                    logger.debug(f"  - {item.name} (is_dir: {item.is_dir()})")
            else:
                logger.warning(f"Session directory does not exist: {subject_ses01}")

            # Look for files in the DICOM directory
            dicom_dir = subject_dir / "DICOM"
            if not dicom_dir.exists():
                logger.warning(f"DICOM directory not found: {dicom_dir}")
                continue

            logger.info(f"Looking for files in DICOM directory: {dicom_dir}")
            logger.info("Contents of DICOM directory:")
            for item in dicom_dir.iterdir():
                logger.debug(f"  - {item.name} (is_dir: {item.is_dir()})")

            # Move localizer
            logger.info("Checking for localizer files...")
            localizer_files = list(dicom_dir.glob("*_LOC_*"))
            logger.info(f"Found {len(localizer_files)} localizer files")
            for f in localizer_files:
                if f.is_file():
                    logger.info(f"Found localizer file: {f}")
                    dest = subject_ses01 / "localized" / f.name
                    try:
                        shutil.move(str(f), str(dest))
                        logger.info(f"Moved localizer {f.name} -> {dest}")
                    except Exception as e:
                        logger.warning(f"Failed to move localizer {f.name}: {e}")

            # Move T1, T2, dwi, fmri
            logger.info("Checking for other scan types...")
            all_files = list(dicom_dir.glob("*"))
            logger.info(f"Found {len(all_files)} total files/directories")
            for f in all_files:
                if not f.is_file():
                    continue
                    
                fn = f.name
                logger.debug(f"Processing file: {fn}")
                
                # Enhanced DWI pattern matching
                if any(pattern in fn.lower() for pattern in ["dti_", "_dwi_", "_dwi", "dwi_"]):
                    dest = subject_ses01 / "dwi" / fn
                    logger.debug(f"Identified as DWI scan -> {dest}")
                elif "_T1_" in fn:
                    dest = subject_ses01 / "anat" / "T1" / fn
                    logger.debug(f"Identified as T1 scan -> {dest}")
                elif "T2_" in fn:
                    dest = subject_ses01 / "anat" / "T2" / fn
                    logger.debug(f"Identified as T2 scan -> {dest}")
                elif "bold_" in fn:
                    dest = subject_ses01 / "fmri" / fn
                    logger.debug(f"Identified as fMRI scan -> {dest}")
                else:
                    logger.debug(f"Skipping file (no matching pattern): {fn}")
                    continue

                try:
                    shutil.move(str(f), str(dest))
                    logger.info(f"Moved {fn} -> {dest}")
                except Exception as e:
                    logger.warning(f"Failed to move {fn}: {e}")

    # After all files are processed, check and clean up DICOM folders
    logger.info("\n=== Checking DICOM folders for cleanup ===")
    for subject_dir in base_path.iterdir():
        if subject_dir.is_dir():
            dicom_dir = subject_dir / "DICOM"
            if dicom_dir.exists():
                remaining_items = list(dicom_dir.iterdir())
                if not remaining_items:
                    try:
                        dicom_dir.rmdir()
                        logger.info(f"Removed empty DICOM directory: {dicom_dir}")
                    except Exception as e:
                        logger.error(f"Failed to remove empty DICOM directory {dicom_dir}: {e}")
                else:
                    logger.error(f"DICOM directory not empty after processing: {dicom_dir}")
                    logger.error("Remaining items:")
                    for item in remaining_items:
                        logger.error(f"  - {item.name} (is_dir: {item.is_dir()})")

def cleanup(base_path: Path, config: Config):
    """
    1) Remove leftover dti dirs
    2) Gzip .nii if configured
    3) Move suspiciously small .nii.gz in dwi
    4) Rename _b0_ -> _b500_1000_, remove 'CANB'
    """
    # Remove leftover 'dti' directories
    for subject_dir in base_path.iterdir():
        if subject_dir.is_dir():
            dti_path = subject_dir / "ses-01" / "dti"
            if dti_path.exists():
                has_contents = any(dti_path.iterdir())
                shutil.rmtree(dti_path)
                logger.info(f"Removed leftover dti folder {dti_path} (had contents? {has_contents})")

    # Gzip any *.nii if configured
    if config.processing.compress_nifti:
        for subject_dir in base_path.iterdir():
            if subject_dir.is_dir():
                cmd = f'find "{subject_dir}" -type f -name "*.nii" -exec gzip {{}} \\;'
                os.system(cmd)

    # Set up small files log
    small_files_log = str(Path(config.paths.log_dir) / "small_files.log")
    with open(small_files_log, "w") as f:
        f.write("=== Small NIfTI Files Report ===\n\n")

    # Identify suspiciously small .nii.gz in dwi
    for subject_dir in base_path.iterdir():
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
    for subject_dir in base_path.iterdir():
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

################################################################################
# MAIN
################################################################################
def main(config: Config):
    """
    Main function to convert DICOM files to BIDS format.
    
    Parameters:
    config (Config): Configuration object containing all necessary settings
    """
    # Set up logging
    setup_logging(config)

    # Convert string paths to Path objects
    dicom_dir = Path(config.paths.dicom_dir)
    bids_dir = Path(config.paths.bids_dir)

    print("\n=== Starting DICOM to BIDS Conversion Pipeline ===")
    print(f"DICOM Directory: {dicom_dir}")
    print(f"BIDS Directory: {bids_dir}\n")

    # Create output directory if it doesn't exist
    os.makedirs(bids_dir, exist_ok=True)

    # Check if dcm2niix is installed
    print("Step 1/5: Checking dcm2niix installation...")
    if not check_dcm2niix():
        print("✗ Error: dcm2niix is not installed. Please install it first.")
        sys.exit(1)
    print("✓ dcm2niix is installed and accessible")

    # Create BIDS directory structure with copies of DICOM files
    print("\nStep 2/5: Copying DICOM files to BIDS directory...")
    create_bids_dir(dicom_dir, bids_dir)
    print("✓ DICOM files copied successfully")

    # Run dcm2niix on the copied files in bids_dir
    print("\nStep 3/5: Converting DICOM files to NIfTI format...")
    run_dcm2niix_on_unprocessed(bids_dir, config)
    print("✓ DICOM to NIfTI conversion complete")

    # Generate BIDS structure
    print("\nStep 4/5: Organizing files into BIDS structure...")
    generate_bids_structure(bids_dir)
    sort_files(bids_dir)
    print(f"✓ Files organized into BIDS structure at: {bids_dir}")

    # Clean up temporary files
    print("\nStep 5/5: Performing final cleanup...")
    cleanup(bids_dir, config)
    
    # Count small files from the log
    small_files_log = Path(config.paths.log_dir) / "small_files.log"
    if small_files_log.exists():
        with open(small_files_log, "r") as f:
            content = f.read()
            small_files_count = content.count("Subject:")
        print(f"✓ Cleanup complete. Found {small_files_count} suspiciously small files")
        print(f"  Small files report available at: {small_files_log}")
    else:
        print("✓ Cleanup complete. No small files found")

    print("\n=== DICOM to BIDS Conversion Complete! ===")
    logger.info("DICOM to BIDS conversion complete!")

if __name__ == "__main__":
    from .utils.config import ConfigManager
    config_manager = ConfigManager()
    config = config_manager.get_config()
    main(config)