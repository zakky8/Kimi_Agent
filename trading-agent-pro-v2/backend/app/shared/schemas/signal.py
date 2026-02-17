"""
Trading Signal Schema

Complete TradingSignal model used by the SignalGenerator (Part 5),
persisted to TimescaleDB, and published via Kafka + WebSocket.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SignalDirection(str, Enum):
    """Trade direction."""
    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


class SignalStatus(str, Enum):
    """Signal lifecycle status."""
    ACTIVE = "ACTIVE"
    FILLED = "FILLED"
    CLOSED_TP1 = "CLOSED_TP1"
    CLOSED_TP2 = "CLOSED_TP2"
    CLOSED_TP3 = "CLOSED_TP3"
    CLOSED_SL = "CLOSED_SL"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class SignalStrength(str, Enum):
    """Confluence-based signal strength."""
    WEAK = "WEAK"
    MEDIUM = "MEDIUM"
    STRONG = "STRONG"
    ULTRA = "ULTRA"


class TradingSignal(BaseModel):
    """
    Complete trading signal produced by the SignalGenerator.

    Contains entry/SL/TP levels, confidence scores from all models,
    the reasoning string, and metadata for tracking and learning.
    """
    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Core signal info
    symbol: str = Field(..., description="Trading pair")
    timeframe: str = Field(..., description="Primary timeframe of signal")
    direction: SignalDirection = Field(..., description="LONG or SHORT")
    strength: SignalStrength = Field(default=SignalStrength.MEDIUM)

    # Price levels
    entry_price: float = Field(..., description="Entry price")
    stop_loss: float = Field(..., description="Stop loss price")
    take_profit_1: float = Field(..., description="TP1 — R:R 1.5:1")
    take_profit_2: float = Field(..., description="TP2 — R:R 2.5:1")
    take_profit_3: float = Field(..., description="TP3 — R:R 4.0:1")

    # Position sizing
    position_size: float = Field(default=0.0, description="Computed lot size")
    risk_percent: float = Field(default=1.0, description="Risk % of equity")

    # ML model outputs
    overall_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Combined confidence score"
    )
    confluence_score: float = Field(
        default=0.0, ge=-1.0, le=1.0, description="Multi-TF confluence score"
    )
    xgb_win_prob: float = Field(
        default=0.0, ge=0.0, le=1.0, description="XGBoost win probability"
    )
    lstm_forecast_24h: Optional[float] = Field(
        default=None, description="LSTM 24h price forecast"
    )
    lstm_forecast_48h: Optional[float] = Field(
        default=None, description="LSTM 48h price forecast"
    )
    lstm_forecast_72h: Optional[float] = Field(
        default=None, description="LSTM 72h price forecast"
    )
    regime: Optional[str] = Field(
        default=None, description="Market regime from classifier"
    )

    # Reasoning
    reasoning: str = Field(
        default="", description="Human-readable reasoning string"
    )

    # Status
    status: SignalStatus = Field(default=SignalStatus.ACTIVE)

    # Feature snapshot for learning
    feature_vector: Optional[Dict[str, Any]] = Field(
        default=None, description="Feature vector at entry time (for labelling)"
    )
    indicators: Optional[Dict[str, Any]] = Field(
        default=None, description="Indicator values at entry time"
    )

    def risk_reward_ratio(self) -> float:
        """Compute the risk-reward ratio for TP1."""
        risk = abs(self.entry_price - self.stop_loss)
        if risk == 0:
            return 0.0
        reward = abs(self.take_profit_1 - self.entry_price)
        return round(reward / risk, 2)

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "EUR/USD",
                "timeframe": "H4",
                "direction": "LONG",
                "strength": "STRONG",
                "entry_price": 1.08300,
                "stop_loss": 1.08000,
                "take_profit_1": 1.08750,
                "take_profit_2": 1.09050,
                "take_profit_3": 1.09500,
                "overall_confidence": 0.72,
                "confluence_score": 0.72,
                "xgb_win_prob": 0.71,
                "reasoning": "LONG EUR/USD H4 | Confluence: 0.72 STRONG",
            }
        }
