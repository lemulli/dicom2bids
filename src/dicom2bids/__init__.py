"""
DICOM to BIDS conversion pipeline.
"""

from .config import Config, ConfigManager
from .convert_and_organize import main as convert_main
from .metadata_enrichment import main as metadata_main
from .finalize_pipeline import main as finalize_main
from .help import show_help

__version__ = "0.1.0"

__all__ = [
    'Config',
    'ConfigManager',
    'convert_main',
    'metadata_main',
    'finalize_main',
    'show_help',
]
