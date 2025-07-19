# © NATO Airborne Early Warning and Control Force - Licensed under NFCL v1.0
"""
Version and configuration management utilities
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

class VersionConfig:
    """Version and configuration management"""
    
    def __init__(self, config_path: str = "config/version.json"):
        self.config_path = config_path
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from JSON file"""
        # Try to find config file in multiple locations
        possible_paths = [
            self.config_path,
            os.path.join(os.path.dirname(__file__), "..", "..", self.config_path),
            os.path.join("/app", self.config_path),
            os.path.join("/app", "config", "version.json")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        self._config = json.load(f)
                    return
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error loading config from {path}: {e}")
                    continue
        
        # Fallback to default config
        print("Warning: Could not load version config, using defaults")
        self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "version": {
                "major": 1,
                "minor": 0,
                "revision": 0,
                "patch": 0,
                "string": "1.0.0.0"
            },
            "classification": {
                "level": "NOT CLASSIFIED",
                "display": True,
                "color": "#00FF00"
            },
            "build": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "environment": "development"
            }
        }
    
    def get_version_string(self) -> str:
        """Get formatted version string"""
        return self._config["version"]["string"]
    
    def get_version_parts(self) -> Dict[str, int]:
        """Get version parts as dictionary"""
        return {
            "major": self._config["version"]["major"],
            "minor": self._config["version"]["minor"],
            "revision": self._config["version"]["revision"],
            "patch": self._config["version"]["patch"]
        }
    
    def get_classification_level(self) -> str:
        """Get classification level"""
        return self._config["classification"]["level"]
    
    def get_classification_color(self) -> str:
        """Get classification color"""
        return self._config["classification"]["color"]
    
    def should_display_classification(self) -> bool:
        """Check if classification should be displayed"""
        return self._config["classification"]["display"]
    
    def get_build_info(self) -> Dict[str, Any]:
        """Get build information"""
        return self._config["build"]
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get complete configuration"""
        return self._config.copy()
    
    def update_build_timestamp(self):
        """Update build timestamp to current time"""
        self._config["build"]["timestamp"] = datetime.utcnow().isoformat() + "Z"
    
    def increment_version(self, level: str = "patch"):
        """Increment version number"""
        version = self._config["version"]
        
        if level == "major":
            version["major"] += 1
            version["minor"] = 0
            version["revision"] = 0
            version["patch"] = 0
        elif level == "minor":
            version["minor"] += 1
            version["revision"] = 0
            version["patch"] = 0
        elif level == "revision":
            version["revision"] += 1
            version["patch"] = 0
        elif level == "patch":
            version["patch"] += 1
        
        # Update version string
        version["string"] = f"{version['major']}.{version['minor']}.{version['revision']}.{version['patch']}"
        
        # Update build timestamp
        self.update_build_timestamp()
    
    def save_config(self):
        """Save configuration back to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")

# Global instance
version_config = VersionConfig()
