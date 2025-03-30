# DICOM to BIDS Pipeline

## Pipeline Overview
1. Convert DICOM to NIfTI and organize into BIDS structure
2. Enrich metadata with additional information
3. Calculate NIfTI statistics
4. Check for sensitive information
5. Finalize for upload

---

## Step-by-Step Guide

### 1. Convert DICOM to BIDS (`dicom2bids`)
Converts DICOM files to NIfTI format and organizes them into a BIDS-compliant directory structure.

**Usage:**

dicom2bids \<dicom\_dir\> \<bids\_dir\>

- **dicom\_dir**: Directory containing DICOM files
- **bids\_dir**: Output directory for BIDS structure

**Output:**
- Organized BIDS directory structure
- NIfTI files (`.nii.gz`)
- JSON sidecar files
- Logs in `outputs/log/dicom_to_bids.log`

---

### 2. Enrich Metadata (`metadata-enrichment`)
Adds additional metadata to the CSV file and copies NIfTI files to the new BIDS directory.

**Usage:**

metadata-enrichment \<input\_csv\> \<output\_csv\> \<old\_bids\_dir\> \<new\_bids\_dir\> \<json\_map\>

- **input\_csv**: Original CSV file
- **output\_csv**: Path for enriched CSV output
- **old\_bids\_dir**: Original BIDS directory
- **new\_bids\_dir**: New BIDS directory
- **json\_map**: JSON mapping file

**Output:**
- Enriched CSV file
- Copied NIfTI files
- Logs in `outputs/log/metadata_enrichment.log`

---

### 3. Calculate NIfTI Statistics (`nifti-calculations`)
Calculates statistics for NIfTI files and adds them to the CSV.

**Usage:**

nifti-calculations \<input\_csv\>

- **input\_csv**: CSV file from metadata enrichment

**Output:**
- Updated CSV with NIfTI statistics
- Logs in `outputs/log/nifti_calculations.log`

---

### 4. Check for Sensitive Data (`check-sensitive-data`)
Scans JSON files for potentially sensitive information.

**Usage:**

check-sensitive-data \<bids\_dir\> \<output\_file\> [–terms TERM1 TERM2 …]

- **bids\_dir**: BIDS directory to check
- **output\_file**: Path for findings output
- **--terms**: Optional list of sensitive terms to check for

**Output:**
- Report of sensitive information findings
- Logs in `outputs/log/sensitive_data_check.log`

---

### 5. Finalize for Upload (`finalize-upload`)
Prepares the BIDS directory for NIH upload by removing JSON files and zipping DWI files.

**Usage:**

finalize-upload \<bids\_dir\> \<csv\_file\>

- **bids\_dir**: BIDS directory to finalize
- **csv\_file**: CSV file to update

**Output:**
- Cleaned BIDS directory (no JSON files)
- Zipped DWI files
- Updated CSV with zip file references
- Logs in `outputs/log/finalize_upload.log`

---

## Directory Structure

outputs/
├── csv/           # CSV files
├── log/           # Log files
└── bids/          # BIDS directory structure

---

## Important Notes
- Each step must be run in sequence.
- All outputs are organized in the `outputs/` directory.
- Logs are created for each step.
- The pipeline handles sensitive information removal.
- DWI files are automatically zipped for NIH upload.

---

For more information about a specific step, you can run:

 –help

