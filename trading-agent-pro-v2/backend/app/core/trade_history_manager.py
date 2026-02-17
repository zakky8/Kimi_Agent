import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class TradeHistoryManager:
    """Manages persistent storage and retrieval of trade results for agent learning"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.history_file = os.path.join(data_dir, "trade_history.json")
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)

    def save_trade(self, trade_data: Dict):
        """Append a completed trade to history"""
        try:
            history = self.load_history()
            
            # Add metadata if not present
            if 'recorded_at' not in trade_data:
                trade_data['recorded_at'] = datetime.utcnow().isoformat()
            
            history.append(trade_data)
            
            # Keep history manageable (last 5000 trades)
            if len(history) > 5000:
                history = history[-5000:]
                
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=4)
                
            return True
        except Exception as e:
            logger.error(f"Error saving trade history: {e}")
            return False

    def load_history(self) -> List[Dict]:
        """Load full trade history"""
        try:
            if not os.path.exists(self.history_file):
                return []
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading trade history: {e}")
            return []

    def get_agent_trades(self, agent_id: str) -> List[Dict]:
        """Get history for a specific agent"""
        history = self.load_history()
        return [t for t in history if t.get('agent_id') == agent_id]

    def get_recent_mistakes(self, agent_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Retrieve recent losing trades for 'mistake' analysis"""
        history = self.load_history()
        trades = history
        if agent_id:
            trades = [t for t in trades if t.get('agent_id') == agent_id]
            
        # Filter for losses (profit < 0)
        mistakes = [t for t in trades if t.get('profit', 0) < 0]
        return mistakes[-limit:]

# Global singleton
trade_history_manager = TradeHistoryManager()
