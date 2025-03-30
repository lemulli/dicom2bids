#!/usr/bin/env python3
# main.py

import argparse
import sys
import os
from pathlib import Path
from .config import ConfigManager

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
        description="DICOM to BIDS pipeline CLI",
        epilog="Example usage:\n"
               "  dicom2bids convert-and-organize [--config config.yaml]\n"
               "  dicom2bids metadata-enrichment [--config config.yaml]\n"
               "  dicom2bids finalize-pipeline [--config config.yaml]",
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