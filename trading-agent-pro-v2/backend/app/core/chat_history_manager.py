import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ChatHistoryManager:
    """
    Manages persistent chat history using a JSON file.
    """
    
    def __init__(self, data_dir: str = "data", filename: str = "chat_history.json"):
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

    def load_history(self) -> List[Dict[str, Any]]:
        """Load chat history from JSON file"""
        if not os.path.exists(self.filepath):
            return []
            
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load chat history from {self.filepath}: {e}")
            return []

    def save_message(self, message: Dict[str, Any]) -> bool:
        """
        Append a new message to history.
        """
        history = self.load_history()
        
        # Ensure timestamp is string for JSON serialization
        if isinstance(message.get('timestamp'), datetime):
             message['timestamp'] = message['timestamp'].isoformat()
        elif 'timestamp' not in message:
             message['timestamp'] = datetime.now().isoformat()
             
        history.append(message)
        
        # Limit history size (e.g., last 100 messages) to prevent indefinite growth
        if len(history) > 100:
            history = history[-100:]
        
        try:
            with open(self.filepath, 'w') as f:
                json.dump(history, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save chat history to {self.filepath}: {e}")
            return False

    def clear_history(self) -> bool:
        """Clear all chat history"""
        try:
            with open(self.filepath, 'w') as f:
                json.dump([], f)
            return True
        except Exception as e:
            logger.error(f"Failed to clear chat history: {e}")
            return False

# Global instance
chat_history_manager = ChatHistoryManager()
