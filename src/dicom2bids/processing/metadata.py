#!/usr/bin/env python3
# metadata.py

import json
import pandas as pd
from pathlib import Path
from ..utils.logging import setup_logging
import os
import shutil
from datetime import datetime
from typing import Dict, Any

def process_metadata(config: Dict[str, Any]):
    """Process metadata and create necessary files."""
    # Set up logging
    logger = setup_logging(config)
    
    # Convert string paths to Path objects
    bids_dir = Path(config.paths.bids_dir)
    
    logger.info("Starting metadata processing")
    logger.info(f"Using BIDS directory: {bids_dir}")
    
    # Create participants.tsv
    participants_data = []
    for subject_dir in bids_dir.iterdir():
        if subject_dir.is_dir() and subject_dir.name.startswith("sub-"):
            subject_id = subject_dir.name.replace("sub-", "")
            participants_data.append({
                "participant_id": subject_id,
                "age": "",  # To be filled manually
                "sex": "",  # To be filled manually
                "group": ""  # To be filled manually
            })
    
    participants_df = pd.DataFrame(participants_data)
    participants_tsv = bids_dir / "participants.tsv"
    participants_df.to_csv(participants_tsv, sep="\t", index=False)
    logger.info(f"Created participants.tsv with {len(participants_data)} entries")
    
    # Create dataset_description.json
    dataset_description = {
        "Name": config.dataset.name,
        "BIDSVersion": "1.4.0",
        "DatasetType": "raw",
        "License": config.dataset.license,
        "Authors": config.dataset.authors,
        "Acknowledgements": config.dataset.acknowledgements,
        "HowToAcknowledge": config.dataset.how_to_acknowledge,
        "Funding": config.dataset.funding,
        "ReferencesAndLinks": config.dataset.references_and_links,
        "DatasetDOI": config.dataset.dataset_doi
    }
    
    dataset_description_json = bids_dir / "dataset_description.json"
    with open(dataset_description_json, "w") as f:
        json.dump(dataset_description, f, indent=4)
    logger.info("Created dataset_description.json")
    
    # Create README
    readme_content = f"""# {config.dataset.name}

## Description
{config.dataset.description}

## License
{config.dataset.license}

## Authors
{', '.join(config.dataset.authors)}

## Acknowledgements
{config.dataset.acknowledgements}

## How to Acknowledge
{config.dataset.how_to_acknowledge}

## Funding
{config.dataset.funding}

## References and Links
{config.dataset.references_and_links}

## Dataset DOI
{config.dataset.dataset_doi}
"""
    
    readme_path = bids_dir / "README"
    with open(readme_path, "w") as f:
        f.write(readme_content)
    logger.info("Created README")
    
    # Create CHANGES
    changes_content = """# Changelog

## [Unreleased]
- Initial release
"""
    
    changes_path = bids_dir / "CHANGES"
    with open(changes_path, "w") as f:
        f.write(changes_content)
    logger.info("Created CHANGES")

def enrich_metadata(config: Dict[str, Any]):
    """Enrich metadata by processing CSV files and updating BIDS structure."""
    # Set up logging
    logger = setup_logging(config)
    
    # Convert string paths to Path objects
    bids_dir = Path(config.paths.bids_dir)
    csv_path = Path(config.csv_files.skeleton_csv)
    
    logger.info("Starting metadata enrichment")
    logger.info(f"Using BIDS directory: {bids_dir}")
    logger.info(f"Using CSV file: {csv_path}")
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
        logger.info(f"Successfully read CSV file with {len(df)} rows")
        
        # Process each row in the CSV
        for idx, row in df.iterrows():
            try:
                # Extract subject information
                subject_id = row['subject_id']
                logger.info(f"Processing subject: {subject_id}")
                
                # Create subject directory if it doesn't exist
                subject_dir = bids_dir / f"sub-{subject_id}"
                subject_dir.mkdir(parents=True, exist_ok=True)
                
                # Update metadata files
                metadata_file = subject_dir / "metadata.json"
                if metadata_file.exists():
                    # Update existing metadata
                    logger.info(f"Updating metadata for subject {subject_id}")
                else:
                    # Create new metadata file
                    logger.info(f"Creating new metadata for subject {subject_id}")
                
            except Exception as e:
                logger.error(f"Error processing subject {subject_id}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return
    
    logger.info("Metadata enrichment completed") 