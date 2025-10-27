"""Configuration management for Zimbra migration."""

from typing import Dict, Any
from pathlib import Path
from configobj import ConfigObj


class ConfigManager:
    """Manages configuration for Zimbra migration."""
    
    def __init__(self, config_path: str = "config.ini"):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = ConfigObj(config_path)
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate required configuration keys."""
        required_sections = ['zimbra_source', 'zimbra_destination', 'global']
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required config section: {section}")
    
    @property
    def source(self) -> Dict[str, Any]:
        """Get source Zimbra configuration."""
        return dict(self.config['zimbra_source'])
    
    @property
    def destination(self) -> Dict[str, Any]:
        """Get destination Zimbra configuration."""
        return dict(self.config['zimbra_destination'])
    
    @property
    def root_folder(self) -> Path:
        """Get root folder path."""
        return Path(self.config['global']['root_folder'])
    
    @property
    def session_file(self) -> Path:
        """Get session file path."""
        return self.root_folder / self.config['global']['session_file']
    
    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.config['global'].get('log_level', 'INFO')