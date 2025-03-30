#!/usr/bin/env python3
# help.py

def show_help():
    """
    Display comprehensive help information about the dicom2bids pipeline.
    """
    help_text = """
DICOM to BIDS Pipeline
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

Step-by-Step Guide
-----------------

1. Convert DICOM to BIDS (dicom2bids)
   ---------------------------------
   Converts DICOM files to NIfTI format and organizes them into a BIDS-compliant directory structure.
   
   Usage: dicom2bids <dicom_dir> <bids_dir>
   
   Input:
   - dicom_dir: Directory containing DICOM files
   - bids_dir: Output directory for BIDS structure
   
   Output:
   - Organized BIDS directory structure
   - NIfTI files (.nii.gz)
   - JSON sidecar files
   - Logs in outputs/log/dicom_to_bids.log

2. Enrich Metadata (metadata-enrichment)
   -----------------------------------
   Adds additional metadata to the CSV file and copies NIfTI files to the new BIDS directory.
   
   Usage: metadata-enrichment <input_csv> <output_csv> <old_bids_dir> <new_bids_dir> <json_map>
   
   Input:
   - input_csv: Original CSV file
   - output_csv: Path for enriched CSV output
   - old_bids_dir: Original BIDS directory
   - new_bids_dir: New BIDS directory
   - json_map: JSON mapping file
   
   Output:
   - Enriched CSV file
   - Copied NIfTI files
   - Logs in outputs/log/metadata_enrichment.log

3. Calculate NIfTI Statistics (nifti-calculations)
   ---------------------------------------------
   Calculates statistics for NIfTI files and adds them to the CSV.
   
   Usage: nifti-calculations <input_csv>
   
   Input:
   - input_csv: CSV file from metadata enrichment
   
   Output:
   - Updated CSV with NIfTI statistics
   - Logs in outputs/log/nifti_calculations.log

4. Check for Sensitive Data (check-sensitive-data)
   ---------------------------------------------
   Scans JSON files for potentially sensitive information.
   
   Usage: check-sensitive-data <bids_dir> <output_file> [--terms TERM1 TERM2 ...]
   
   Input:
   - bids_dir: BIDS directory to check
   - output_file: Path for findings output
   - --terms: Optional list of sensitive terms to check for
   
   Output:
   - Report of sensitive information findings
   - Logs in outputs/log/sensitive_data_check.log

5. Finalize for Upload (finalize-upload)
   -----------------------------------
   Prepares the BIDS directory for NIH upload by removing JSON files and zipping DWI files.
   
   Usage: finalize-upload <bids_dir> <csv_file>
   
   Input:
   - bids_dir: BIDS directory to finalize
   - csv_file: CSV file to update
   
   Output:
   - Cleaned BIDS directory (no JSON files)
   - Zipped DWI files
   - Updated CSV with zip file references
   - Logs in outputs/log/finalize_upload.log

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
- DWI files are automatically zipped for NIH upload

For more information about a specific step, use:
  <command> --help
"""
    print(help_text)

if __name__ == "__main__":
    show_help() 