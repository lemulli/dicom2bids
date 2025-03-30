"""
DICOM to BIDS conversion pipeline.
"""

from .pipeline import convert_and_organize, metadata_enrichment, finalize

__version__ = "0.1.0"

__all__ = [
    'convert_and_organize',
    'metadata_enrichment',
    'finalize',
]
