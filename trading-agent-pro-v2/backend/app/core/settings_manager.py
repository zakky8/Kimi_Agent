import json
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class SettingsManager:
    """
    Manages persistent settings using a JSON file.
    """
    
    def __init__(self, data_dir: str = "data", filename: str = "settings.json"):
        self.data_dir = data_dir
        self.filename = filename
        self.filepath = os.path.join(data_dir, filename)
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir)
            except Exception as e:
                logger.error(f"Failed to create data directory: {e}")

    def load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file"""
        if not os.path.exists(self.filepath):
            return {}
            
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings from {self.filepath}: {e}")
            return {}

    def save_settings(self, new_settings: Dict[str, Any]) -> bool:
        """
        Save settings to JSON file.
        Updates existing settings with new values (merge).
        """
        current_settings = self.load_settings()
        updated_settings = {**current_settings, **new_settings}
        
        try:
            with open(self.filepath, 'w') as f:
                json.dump(updated_settings, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save settings to {self.filepath}: {e}")
            return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        settings = self.load_settings()
        return settings.get(key, default)

# Global instance
settings_manager = SettingsManager()
