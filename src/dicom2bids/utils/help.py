#!/usr/bin/env python3
# help.py

import sys

def show_help():
    """Display help information about the DICOM to BIDS pipeline."""
    help_text = """
DICOM to BIDS Conversion Pipeline
================================

This tool converts DICOM files to BIDS format and prepares them for upload.

Commands:
---------
1. convert-and-organize
   Converts DICOM files to NIfTI format and creates initial BIDS structure.
   Options:
   --dicom-dir    Override DICOM directory from config
   --bids-dir     Override BIDS directory from config

2. metadata-enrichment
   Processes and enriches metadata for the BIDS dataset.
   Options:
   --input-csv    Override input CSV from config
   --old-bids-dir Override old BIDS directory from config
   --new-bids-dir Override new BIDS directory from config
   --t2-json-map  Override T2 JSON mapping file from config

3. finalize-pipeline
   Validates and prepares BIDS dataset for upload.
   Options:
   --bids-dir     Override BIDS directory from config
   --csv-path     Override CSV metadata file from config

Global Options:
--------------
--config        Path to configuration file (default: config.yaml)
--help          Show this help message

Example Usage:
-------------
# Convert DICOMs to BIDS
dicom2bids convert-and-organize --dicom-dir /path/to/dicoms

# Process metadata
dicom2bids metadata-enrichment --input-csv /path/to/mapping.csv

# Finalize and validate
dicom2bids finalize-pipeline --bids-dir /path/to/bids
"""
    print(help_text)
    sys.exit(0) 