#!/usr/bin/env python3
# check_sensitive_data.py

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def check_sensitive_info(json_path: str, sensitive_terms: List[str]) -> List[str]:
    """
    Check a JSON file for sensitive information.
    
    Parameters:
    json_path (str): Path to the JSON file
    sensitive_terms (List[str]): List of sensitive terms to check for
    
    Returns:
    List[str]: List of findings (empty if no sensitive info found)
    """
    findings = []
    try:
        with open(json_path) as f:
            data = json.load(f)
        
        for key in data.keys():
            # Convert key to lowercase for case-insensitive comparison
            key_lower = key.lower()
            for term in sensitive_terms:
                # Check if the term is a whole word using word boundaries
                if f" {term} " in f" {key_lower} ":
                    findings.append(f"\nFound sensitive term '{term}' in {json_path}")
                    findings.append(f"Key: {key}")
                    findings.append(f"Value: {data[key]}")
    
    except Exception as e:
        logger.error(f"Error processing {json_path}: {e}")
        findings.append(f"\nError processing {json_path}: {e}")
    
    return findings

def main():
    """
    Main function to check BIDS directory for sensitive information in JSON files.
    """
    parser = argparse.ArgumentParser(description='Check BIDS directory for sensitive information in JSON files')
    parser.add_argument('bids_dir', help='Path to BIDS directory')
    parser.add_argument('output_file', help='Path to output file for findings')
    parser.add_argument('--terms', nargs='+', default=[
        'zip', 'date', 'dob', 'name', 'ssn', 'age', 'sex',
        'address', 'phone', 'email', 'birth', 'patient', 'subject'
    ], help='''List of terms to check for in JSON files that might indicate sensitive information.
    Common terms to check include:
    - Personal identifiers: name, ssn, id, subject, patient
    - Demographics: age, sex, gender, race, ethnicity
    - Contact info: address, phone, email
    - Dates: dob, birth, date
    - Medical info: diagnosis, condition, treatment
    - Location: zip, city, state, country
    Default terms: zip, date, dob, name, ssn, age, sex, address, phone, email, birth, patient, subject''')
    
    args = parser.parse_args()

    logger.info(f"Checking for sensitive information in {args.bids_dir}")
    logger.info(f"Output will be written to: {args.output_file}")
    logger.info(f"Checking for terms: {', '.join(args.terms)}")

    # Collect all findings
    all_findings = []
    
    # Recursively find all JSON files
    json_count = 0
    for root, _, files in os.walk(args.bids_dir):
        for file in files:
            if file.endswith('.json'):
                json_path = os.path.join(root, file)
                json_count += 1
                logger.debug(f"Checking {json_path}")
                findings = check_sensitive_info(json_path, args.terms)
                all_findings.extend(findings)

    # Write findings to file
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(f"=== Sensitive Information Check Results ===\n")
        f.write(f"BIDS Directory: {args.bids_dir}\n")
        f.write(f"Total JSON files checked: {json_count}\n")
        f.write(f"Total findings: {len(all_findings)}\n")
        f.write(f"Terms checked: {', '.join(args.terms)}\n\n")
        
        if all_findings:
            f.write("=== Findings ===\n")
            for finding in all_findings:
                f.write(f"{finding}\n")
        else:
            f.write("No sensitive information found.\n")

    logger.info(f"Check complete. Results written to {args.output_file}")
    if all_findings:
        logger.warning(f"Found {len(all_findings)} potential sensitive information items")
    else:
        logger.info("No sensitive information found")

if __name__ == "__main__":
    main() 