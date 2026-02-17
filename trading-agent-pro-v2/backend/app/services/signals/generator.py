"""
Kimi Agent — Signal Generator (Part 5b)

Converts a ConsensusResult from the Orchestrator into a fully-formed
trading signal with:
  • Entry price (current market or limit)
  • Stop Loss (ATR-based or structure-based)
  • Take Profit (risk:reward ratio)
  • Position size (Kelly criterion / fixed risk %)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.services.agents.orchestrator import AgentVote, ConsensusResult

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class SignalStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass
class TradingSignal:
    """Complete trading signal ready for execution."""
    symbol: str
    direction: str             # "LONG" or "SHORT"
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: float
    take_profit_2: float = 0.0   # Optional TP2 for scaling out
    position_size: float = 0.0   # In base currency units
    risk_pct: float = 1.0        # % of capital risked
    risk_reward: float = 2.0
    confidence: float = 0.0
    status: SignalStatus = SignalStatus.PENDING
    consensus_score: float = 0.0
    agreement_count: int = 0
    timestamp: float = 0.0
    expiry_s: int = 3600         # Signal expires after 1 hour
    reasons: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def risk_amount(self) -> float:
        """Distance from entry to SL in price."""
        return abs(self.entry_price - self.stop_loss)

    @property
    def reward_amount(self) -> float:
        """Distance from entry to TP in price."""
        return abs(self.take_profit - self.entry_price)

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.expiry_s


class SignalGenerator:
    """
    Transforms ConsensusResult + current indicators into a TradingSignal.

    Stop loss: ATR-based (1.5 × ATR) or nearest structure level.
    Take profit: risk:reward ratio (default 2:1, up to 3:1 with high confidence).
    Position size: fixed percentage risk (default 1% of capital).
    """

    def __init__(
        self,
        default_risk_pct: float = 1.0,
        default_rr: float = 2.0,
        max_rr: float = 3.0,
        atr_sl_multiplier: float = 1.5,
        account_balance: float = 10000.0,
    ) -> None:
        self._risk_pct = default_risk_pct
        self._default_rr = default_rr
        self._max_rr = max_rr
        self._atr_mult = atr_sl_multiplier
        self._balance = account_balance

    def generate(
        self,
        consensus: ConsensusResult,
        indicators: Dict[str, float],
        current_price: Optional[float] = None,
    ) -> Optional[TradingSignal]:
        """
        Generate a signal if consensus is actionable.
        Returns None if no signal should be generated.
        """
        if not consensus.is_actionable:
            return None

        if consensus.direction not in (AgentVote.LONG, AgentVote.SHORT):
            return None

        direction = consensus.direction.value
        is_long = direction == "LONG"

        # Entry price
        entry = current_price or indicators.get("ema_9", 0.0)
        if entry <= 0:
            logger.warning("[SignalGen] Invalid entry price — skipping")
            return None

        # ATR for stop loss
        atr = indicators.get("atr_14", 0.0)
        if atr <= 0:
            atr = entry * 0.01  # Default 1% of price

        # Structure-based SL (nearest support/resistance)
        nearest_support = indicators.get("nearest_support", 0.0)
        nearest_resistance = indicators.get("nearest_resistance", 0.0)

        # Calculate stop loss
        atr_sl_distance = atr * self._atr_mult

        if is_long:
            atr_sl = entry - atr_sl_distance
            structure_sl = nearest_support if nearest_support > 0 else atr_sl
            # Use the tighter of the two (closer to entry but still below)
            sl = max(atr_sl, structure_sl) if structure_sl < entry else atr_sl
        else:
            atr_sl = entry + atr_sl_distance
            structure_sl = nearest_resistance if nearest_resistance > 0 else atr_sl
            sl = min(atr_sl, structure_sl) if structure_sl > entry else atr_sl

        # Risk:reward ratio — boost for high-confidence signals
        rr = self._default_rr
        if consensus.consensus_score > 0.75:
            rr = self._max_rr

        # Take profit
        risk_dist = abs(entry - sl)
        if is_long:
            tp = entry + risk_dist * rr
            tp2 = entry + risk_dist * rr * 0.5  # TP1 at 50% of full target
        else:
            tp = entry - risk_dist * rr
            tp2 = entry - risk_dist * rr * 0.5

        # Position sizing (fixed % risk)
        risk_amount = self._balance * (self._risk_pct / 100.0)
        position_size = risk_amount / risk_dist if risk_dist > 0 else 0.0

        signal = TradingSignal(
            symbol=consensus.symbol,
            direction=direction,
            signal_type=SignalType.MARKET,
            entry_price=round(entry, 6),
            stop_loss=round(sl, 6),
            take_profit=round(tp, 6),
            take_profit_2=round(tp2, 6),
            position_size=round(position_size, 4),
            risk_pct=self._risk_pct,
            risk_reward=rr,
            confidence=consensus.consensus_score,
            consensus_score=consensus.consensus_score,
            agreement_count=consensus.agreement_count,
            timestamp=time.time(),
            reasons=consensus.reasons[:5],  # Top 5 reasons
        )

        logger.info(
            f"[SignalGen] {signal.direction} {signal.symbol} @ {signal.entry_price} "
            f"SL={signal.stop_loss} TP={signal.take_profit} size={signal.position_size} "
            f"RR={signal.risk_reward}"
        )

        return signal

    def update_balance(self, balance: float) -> None:
        """Update account balance for position sizing."""
        self._balance = balance
