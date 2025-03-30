#!/usr/bin/env python3
# config.py

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class PathsConfig:
    dicom_dir: str
    bids_dir: str
    log_dir: str

@dataclass
class CSVFilesConfig:
    skeleton_csv: str
    json_map_csv: str
    final_csv: str

@dataclass
class ProcessingConfig:
    run_json_check: bool
    check_sensitive_data: bool
    create_derivatives: bool
    compress_nifti: bool

@dataclass
class SessionConfig:
    enabled: bool
    format: str
    start_number: int
    padding: int
    auto_increment: bool
    session_map: Dict[str, int]

@dataclass
class LoggingConfig:
    level: str
    file: str
    session: SessionConfig

@dataclass
class Config:
    paths: PathsConfig
    csv_files: CSVFilesConfig
    processing: ProcessingConfig
    logging: LoggingConfig

class ConfigManager:
    """Manages loading and validation of configuration from YAML file."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config: Optional[Config] = None
    
    def load_config(self) -> Config:
        """Load and validate configuration from YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Validate and convert to dataclass objects
        paths = PathsConfig(**config_dict['paths'])
        csv_files = CSVFilesConfig(**config_dict['csv_files'])
        processing = ProcessingConfig(**config_dict['processing'])
        session = SessionConfig(**config_dict['logging']['session'])
        logging = LoggingConfig(
            level=config_dict['logging']['level'],
            file=config_dict['logging']['file'],
            session=session
        )
        
        self.config = Config(
            paths=paths,
            csv_files=csv_files,
            processing=processing,
            logging=logging
        )
        
        return self.config
    
    def get_config(self) -> Config:
        """Get the current configuration, loading it if necessary."""
        if self.config is None:
            self.load_config()
        return self.config
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        if self.config is None:
            self.load_config()
        
        # Recursively update nested dictionaries
        def update_dict(d: Dict[str, Any], u: Dict[str, Any]) -> Dict[str, Any]:
            for k, v in u.items():
                if isinstance(v, dict):
                    d[k] = update_dict(d.get(k, {}), v)
                else:
                    d[k] = v
            return d
        
        # Convert config to dict, update, and convert back
        config_dict = self.config.__dict__
        updated_dict = update_dict(config_dict, updates)
        self.config = Config(**updated_dict)
    
    def save_config(self) -> None:
        """Save current configuration back to YAML file."""
        if self.config is None:
            raise ValueError("No configuration loaded")
        
        def dataclass_to_dict(dc) -> Dict[str, Any]:
            result = {}
            for field in dc.__dataclass_fields__:
                value = getattr(dc, field)
                if hasattr(value, '__dataclass_fields__'):
                    result[field] = dataclass_to_dict(value)
                else:
                    result[field] = value
            return result
        
        config_dict = dataclass_to_dict(self.config)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)

# Create a global config instance
config = ConfigManager() 