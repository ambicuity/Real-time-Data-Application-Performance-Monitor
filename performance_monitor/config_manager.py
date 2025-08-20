"""
Configuration Management Module

Handles loading and managing configuration settings for the performance monitor.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages configuration settings."""
    
    DEFAULT_CONFIG = {
        "monitoring": {
            "interval": 1.0,  # seconds between metric collection
            "analysis_interval": 60,  # seconds between performance analysis
            "buffer_size": 10000  # maximum metrics to keep in memory
        },
        "metrics": {
            "buffer_size": 10000,
            "latency_buffer_size": 1000
        },
        "thresholds": {
            "cpu_usage": 80.0,  # percentage
            "memory_usage": 85.0,  # percentage
            "latency_p95": 1000.0,  # milliseconds
            "min_throughput": 100.0  # events per second
        },
        "simulation": {
            "default_scenario": "normal_load",
            "default_duration": 300
        },
        "reporting": {
            "default_format": "html",
            "default_hours": 1,
            "chart_width": 800,
            "chart_height": 400
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self._config = None
        self._load_config()
        
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        if self._config is None:
            self._load_config()
        return self._config
        
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a specific configuration section."""
        return self.get_config().get(section, {})
        
    def get_value(self, section: str, key: str, default: Any = None) -> Any:
        """Get a specific configuration value."""
        return self.get_section(section).get(key, default)
        
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration values."""
        self._deep_update(self._config, updates)
        
    def save_config(self, path: Optional[str] = None):
        """Save configuration to file."""
        save_path = path or self.config_path
        if save_path:
            try:
                with open(save_path, 'w') as f:
                    yaml.dump(self._config, f, default_flow_style=False, indent=2)
            except Exception as e:
                print(f"Error saving configuration: {e}")
        else:
            print("No configuration path specified for saving")
            
    def _load_config(self):
        """Load configuration from file or use defaults."""
        self._config = self.DEFAULT_CONFIG.copy()
        
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self._deep_update(self._config, file_config)
            except Exception as e:
                print(f"Error loading configuration from {self.config_path}: {e}")
                print("Using default configuration")
        
        # Also check for config files in standard locations
        self._load_default_configs()
        
    def _load_default_configs(self):
        """Load configuration from standard locations."""
        possible_paths = [
            "config/config.yaml",
            "config/performance_monitor.yaml",
            os.path.expanduser("~/.rt-perf-monitor.yaml"),
            "/etc/rt-perf-monitor/config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        file_config = yaml.safe_load(f)
                        if file_config:
                            self._deep_update(self._config, file_config)
                            break
                except Exception as e:
                    print(f"Error loading configuration from {path}: {e}")
                    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Recursively update dictionary."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
                
    def create_default_config_file(self, path: str):
        """Create a default configuration file."""
        config_dir = os.path.dirname(path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
            
        try:
            with open(path, 'w') as f:
                yaml.dump(self.DEFAULT_CONFIG, f, default_flow_style=False, indent=2)
            print(f"Default configuration created at: {path}")
        except Exception as e:
            print(f"Error creating default configuration: {e}")
            
    @classmethod
    def get_default_config_path(cls) -> str:
        """Get the default configuration file path."""
        return "config/config.yaml"