#!/usr/bin/env python3
# main.py

import argparse
import sys
import os
import yaml
from pathlib import Path
from .pipeline import convert_and_organize, metadata_enrichment, finalize
from .utils import show_help

def setup_parser():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(
        description="DICOM to BIDS pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Add global config argument
    parser.add_argument('--config', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    
    subparsers = parser.add_subparsers(dest="command", help="Sub-command to run")

    # Subcommand: convert-and-organize
    parser_convert = subparsers.add_parser("convert-and-organize", help="Convert DICOMs to NIfTI and create partial BIDS")
    parser_convert.add_argument('--dicom-dir', help='Override DICOM directory from config')
    parser_convert.add_argument('--bids-dir', help='Override BIDS directory from config')
    
    # Subcommand: metadata-enrichment
    parser_meta = subparsers.add_parser("metadata-enrichment", help="Expand CSV, copy NIfTIs, read headers with nibabel")
    parser_meta.add_argument('--input-csv', help='Override input CSV from config')
    parser_meta.add_argument('--old-bids-dir', help='Override old BIDS directory from config')
    parser_meta.add_argument('--new-bids-dir', help='Override new BIDS directory from config')
    parser_meta.add_argument('--t2-json-map', help='Override T2 JSON mapping file from config')

    # Subcommand: finalize-pipeline
    parser_final = subparsers.add_parser("finalize-pipeline", help="Check JSONs, remove them, zip DWI, etc.")
    parser_final.add_argument('--bids-dir', help='Override BIDS directory from config')
    parser_final.add_argument('--csv-path', help='Override CSV metadata file from config')

    return parser

def main():
    # Set up parser first
    parser = setup_parser()
    args = parser.parse_args()
    
    # Handle help cases first
    if len(sys.argv) == 1 or args.command is None or any(arg in ['--help', '-h'] for arg in sys.argv):
        show_help()
        return
    
    # Load config
    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        return
    
    with open(args.config) as f:
        config = yaml.safe_load(f)
    
    # Create output directories
    output_dirs = [
        config['paths']['bids_dir'],
        config['paths']['log_dir'],
        os.path.dirname(config['csv_files']['final_csv'])
    ]
    
    for dir_path in output_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # Handle command-specific overrides and run pipeline
    if args.command == "convert-and-organize":
        if args.dicom_dir:
            config['paths']['dicom_dir'] = args.dicom_dir
        if args.bids_dir:
            config['paths']['bids_dir'] = args.bids_dir
        convert_and_organize(config)

    elif args.command == "metadata-enrichment":
        if args.input_csv:
            config['csv_files']['skeleton_csv'] = args.input_csv
        if args.old_bids_dir:
            config['paths']['bids_dir'] = args.old_bids_dir
        if args.new_bids_dir:
            config['paths']['bids_dir'] = args.new_bids_dir
        if args.t2_json_map:
            config['csv_files']['json_map_csv'] = args.t2_json_map
        metadata_enrichment(config)

    elif args.command == "finalize-pipeline":
        if args.bids_dir:
            config['paths']['bids_dir'] = args.bids_dir
        if args.csv_path:
            config['csv_files']['final_csv'] = args.csv_path
        finalize(config)

if __name__ == "__main__":
    main()