#!/usr/bin/env python3
# logging.py

import sys
import logging
from pathlib import Path
from typing import Optional
from ..config import Config

def setup_logging(config: Config, logger_name: Optional[str] = None) -> logging.Logger:
    """
    Set up logging with console and file handlers based on configuration.
    
    Parameters:
    config (Config): Configuration object containing logging settings
    logger_name (Optional[str]): Name of the logger to set up. If None, uses the caller's name.
    
    Returns:
    logging.Logger: Configured logger instance
    """
    # Get the logger
    logger = logging.getLogger(logger_name or __name__)
    logger.setLevel(logging.DEBUG)  # gather all logs at DEBUG level internally
    
    # Remove any existing handlers to avoid duplicates
    logger.handlers = []
    
    # Console handler for WARNING and ERROR: show on stderr
    warning_handler = logging.StreamHandler(sys.stderr)
    warning_handler.setLevel(logging.WARNING)
    warning_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    warning_handler.setFormatter(warning_formatter)
    logger.addHandler(warning_handler)
    
    # Console handler for CRITICAL: show on stdout
    critical_handler = logging.StreamHandler(sys.stdout)
    critical_handler.setLevel(logging.CRITICAL)
    critical_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    critical_handler.setFormatter(critical_formatter)
    logger.addHandler(critical_handler)
    
    # File handler: record INFO+ to configured log file
    log_file = str(Path(config.paths.log_dir) / config.logging.file)
    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Warning handler: record WARNING+ to error log
    error_log = str(Path(config.paths.log_dir) / f"{Path(config.logging.file).stem}.err")
    error_handler = logging.FileHandler(error_log, mode="w")
    error_handler.setLevel(logging.WARNING)
    error_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    error_handler.setFormatter(error_formatter)
    logger.addHandler(error_handler)
    
    return logger

def setup_excluded_scans_logger(config: Config) -> logging.Logger:
    """
    Set up a special logger for excluded scans.
    
    Parameters:
    config (Config): Configuration object containing logging settings
    
    Returns:
    logging.Logger: Configured logger instance for excluded scans
    """
    excluded_scans_log = str(Path(config.paths.log_dir) / "excluded_scans.log")
    excluded_scans_logger = logging.getLogger('excluded_scans')
    excluded_scans_logger.handlers = []  # Remove any existing handlers
    
    excluded_scans_handler = logging.FileHandler(excluded_scans_log)
    excluded_scans_handler.setFormatter(logging.Formatter('%(message)s'))
    excluded_scans_logger.addHandler(excluded_scans_handler)
    excluded_scans_logger.setLevel(logging.INFO)
    
    return excluded_scans_logger 