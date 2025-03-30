#!/usr/bin/env python3
# main.py

import argparse
import sys
import os
from pathlib import Path
from .utils.config import ConfigManager

def main():
    # Initialize config manager
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    # Create output directories
    output_dirs = [
        config.paths.bids_dir,
        config.paths.log_dir,
        os.path.dirname(config.csv_files.final_csv)
    ]
    
    for dir_path in output_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    parser = argparse.ArgumentParser(
        description="""DICOM to BIDS Pipeline
=====================

This pipeline converts DICOM files to BIDS format and prepares them for NIH upload.
The pipeline consists of several steps that must be run in sequence.

Pipeline Overview
----------------
1. Convert DICOM to NIfTI and organize into BIDS structure
2. Enrich metadata with additional information
3. Calculate NIfTI statistics
4. Check for sensitive information
5. Finalize for upload

Directory Structure
-----------------
outputs/
├── csv/           # CSV files
├── log/           # Log files
└── bids/          # BIDS directory structure

Important Notes
--------------
- Each step must be run in sequence
- All outputs are organized in the outputs/ directory
- Logs are created for each step
- The pipeline handles sensitive information removal
- DWI files are automatically zipped for NIH upload""",
        epilog="""Example usage:
  dicom2bids convert-and-organize [--config config.yaml]
  dicom2bids metadata-enrichment [--config config.yaml]
  dicom2bids finalize-pipeline [--config config.yaml]

For more information about a specific step, use:
  <command> --help""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add global config argument
    parser.add_argument('--config', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    
    subparsers = parser.add_subparsers(dest="command", help="Sub-command to run")

    # Subcommand: convert-and-organize
    parser_convert = subparsers.add_parser("convert-and-organize", 
        help="Convert DICOMs to NIfTI and create partial BIDS",
        description="""Convert DICOM to BIDS
---------------------------------
Converts DICOM files to NIfTI format and organizes them into a BIDS-compliant directory structure.

Input:
- dicom_dir: Directory containing DICOM files
- bids_dir: Output directory for BIDS structure

Output:
- Organized BIDS directory structure
- NIfTI files (.nii.gz)
- JSON sidecar files
- Logs in outputs/log/dicom_to_bids.log""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_convert.add_argument('--dicom-dir', help='Override DICOM directory from config')
    parser_convert.add_argument('--bids-dir', help='Override BIDS directory from config')
    
    # Subcommand: metadata-enrichment
    parser_meta = subparsers.add_parser("metadata-enrichment", 
        help="Expand CSV, copy NIfTIs, read headers with nibabel",
        description="""Enrich Metadata
----------------------------------
Adds additional metadata to the CSV file and copies NIfTI files to the new BIDS directory.

Input:
- input_csv: Original CSV file
- output_csv: Path for enriched CSV output
- old_bids_dir: Original BIDS directory
- new_bids_dir: New BIDS directory
- json_map: JSON mapping file

Output:
- Enriched CSV file
- Copied NIfTI files
- Logs in outputs/log/metadata_enrichment.log""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_meta.add_argument('--input-csv', help='Override input CSV from config')
    parser_meta.add_argument('--old-bids-dir', help='Override old BIDS directory from config')
    parser_meta.add_argument('--new-bids-dir', help='Override new BIDS directory from config')
    parser_meta.add_argument('--t2-json-map', help='Override T2 JSON mapping file from config')

    # Subcommand: finalize-pipeline
    parser_final = subparsers.add_parser("finalize-pipeline", 
        help="Check JSONs, remove them, zip DWI, etc.",
        description="""Finalize for Upload
----------------------------------
Prepares the BIDS directory for NIH upload by removing JSON files and zipping DWI files.

Input:
- bids_dir: BIDS directory to finalize
- csv_file: CSV file to update

Output:
- Cleaned BIDS directory (no JSON files)
- Zipped DWI files
- Updated CSV with zip file references
- Logs in outputs/log/finalize_upload.log""",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser_final.add_argument('--bids-dir', help='Override BIDS directory from config')
    parser_final.add_argument('--csv-path', help='Override CSV metadata file from config')

    # Parse CLI
    args = parser.parse_args()

    # Update config with command line arguments if provided
    if args.config != 'config.yaml':
        config_manager = ConfigManager(args.config)
        config = config_manager.get_config()

    # Handle command-specific overrides
    if args.command == "convert-and-organize":
        updates = {}
        if args.dicom_dir:
            updates['paths'] = {'dicom_dir': args.dicom_dir}
        if args.bids_dir:
            updates['paths'] = {'bids_dir': args.bids_dir}
        if updates:
            config_manager.update_config(updates)
            config = config_manager.get_config()
        
        from .convert_and_organize import main as convert_main
        convert_main(config)

    elif args.command == "metadata-enrichment":
        updates = {}
        if args.input_csv:
            updates['csv_files'] = {'skeleton_csv': args.input_csv}
        if args.old_bids_dir:
            updates['paths'] = {'bids_dir': args.old_bids_dir}
        if args.new_bids_dir:
            updates['paths'] = {'bids_dir': args.new_bids_dir}
        if args.t2_json_map:
            updates['csv_files'] = {'json_map_csv': args.t2_json_map}
        if updates:
            config_manager.update_config(updates)
            config = config_manager.get_config()
        
        from .metadata_enrichment import main as meta_main
        meta_main(config)

    elif args.command == "finalize-pipeline":
        updates = {}
        if args.bids_dir:
            updates['paths'] = {'bids_dir': args.bids_dir}
        if args.csv_path:
            updates['csv_files'] = {'final_csv': args.csv_path}
        if updates:
            config_manager.update_config(updates)
            config = config_manager.get_config()
        
        from .finalize_pipeline import main as finalize_main
        finalize_main(config)

    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()