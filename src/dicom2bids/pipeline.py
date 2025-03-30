#!/usr/bin/env python3
# pipeline.py

from .core.convert import convert_dicoms
from .core.organize import organize_files
from .core.cleanup import cleanup_files
from .processing.metadata import enrich_metadata
from .processing.nifti import calculate_nifti_stats
from .processing.sensitive import check_sensitive_data
from .finalize.pipeline import finalize_pipeline
from .finalize.upload import prepare_for_upload
from typing import Dict, Any

def convert_and_organize(config: Dict[str, Any]):
    """
    Main conversion pipeline step that converts DICOMs to NIfTI and organizes them.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    """
    convert_dicoms(config)
    organize_files(config)
    cleanup_files(config)

def metadata_enrichment(config: Dict[str, Any]):
    """
    Main metadata enrichment step that processes and enriches metadata.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    """
    enrich_metadata(config)
    calculate_nifti_stats(config)
    check_sensitive_data(config)

def finalize(config: Dict[str, Any]):
    """
    Main finalization step that prepares the BIDS directory for upload.
    
    Parameters:
    config: Configuration dictionary containing all necessary settings
    """
    finalize_pipeline(config)
    prepare_for_upload(config) 