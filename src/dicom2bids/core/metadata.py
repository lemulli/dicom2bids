#!/usr/bin/env python3
# metadata.py

import json
import pandas as pd
from pathlib import Path
from ..utils.logging import setup_logging
from typing import Dict, Any

logger = setup_logging()

def process_metadata(config: Dict[str, Any]):
    """
    Process and enrich metadata for the BIDS dataset.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    """
    bids_dir = Path(config.paths.bids_dir)
    
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