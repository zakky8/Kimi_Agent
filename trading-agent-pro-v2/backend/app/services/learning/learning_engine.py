"""
Kimi Agent — Self-Improving Learning Loop (Part 6)

Components:
  • OnlineLearner       — incrementally updates XGBoost with new trade outcomes
  • MistakeTracker      — identifies and catalogues recurring trade errors
  • PerformanceTracker  — monitors win rate, Sharpe, drawdown; pauses if degraded
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────
# Trade Outcome (shared across learning components)
# ────────────────────────────────────────────────────────

class TradeResult(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"


@dataclass
class TradeOutcome:
    """Record of a completed trade for learning purposes."""
    symbol: str
    direction: str                 # LONG or SHORT
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    pnl: float                     # Realised P&L
    pnl_pct: float                 # P&L as % of capital
    result: TradeResult
    confidence_at_entry: float
    consensus_score: float
    indicators_at_entry: Dict[str, float] = field(default_factory=dict)
    timestamp_entry: float = 0.0
    timestamp_exit: float = 0.0
    duration_s: float = 0.0
    reason_exit: str = ""          # "TP", "SL", "manual", "expired"


# ════════════════════════════════════════════════════════
# Online Learner — Incremental XGBoost Updates
# ════════════════════════════════════════════════════════

class OnlineLearner:
    """
    Incrementally updates the XGBoost model after each trade outcome.
    Maintains a sliding buffer of the last N trades for periodic
    mini-batch retraining.
    
    Buffer size: 100 trades (default).
    Retrain trigger: every 20 new outcomes.
    """

    def __init__(
        self,
        buffer_size: int = 100,
        retrain_every: int = 20,
    ) -> None:
        self._buffer: deque[TradeOutcome] = deque(maxlen=buffer_size)
        self._retrain_every = retrain_every
        self._outcome_count = 0
        self._model = None  # Will be set via set_model()

    def set_model(self, model: Any) -> None:
        """Attach the XGBoost model for online updates."""
        self._model = model

    def record_outcome(self, outcome: TradeOutcome) -> Optional[Dict[str, float]]:
        """
        Record a trade outcome. Returns training metrics if a retrain was triggered.
        """
        self._buffer.append(outcome)
        self._outcome_count += 1

        logger.info(
            f"[OnlineLearner] Recorded {outcome.result.value} trade on {outcome.symbol} "
            f"(P&L: {outcome.pnl:+.2f}, buffer={len(self._buffer)})"
        )

        if self._outcome_count % self._retrain_every == 0:
            return self._retrain()

        return None

    def _retrain(self) -> Dict[str, float]:
        """Mini-batch retrain on the buffer contents."""
        if len(self._buffer) < 10:
            return {"status": "insufficient_data", "buffer_size": len(self._buffer)}

        # Build training data from buffer
        X_list = []
        y_list = []
        for outcome in self._buffer:
            if outcome.indicators_at_entry:
                sorted_keys = sorted(outcome.indicators_at_entry.keys())
                features = [outcome.indicators_at_entry.get(k, 0.0) for k in sorted_keys]
                X_list.append(features)

                # Label: 0=LONG win, 1=SHORT win, 2=neutral/loss
                if outcome.result == TradeResult.WIN:
                    y_list.append(0 if outcome.direction == "LONG" else 1)
                else:
                    y_list.append(2)

        if len(X_list) < 10:
            return {"status": "insufficient_features", "samples": len(X_list)}

        X = np.array(X_list, dtype=np.float32)
        y = np.array(y_list, dtype=np.int64)

        if self._model and hasattr(self._model, "update"):
            metrics = self._model.update(X, y)
            logger.info(f"[OnlineLearner] Online retrain complete: {metrics}")
            return metrics
        elif self._model and hasattr(self._model, "train"):
            metrics = self._model.train(X, y)
            return metrics

        return {"status": "no_model_attached"}


# ════════════════════════════════════════════════════════
# Mistake Tracker — Learns from Errors
# ════════════════════════════════════════════════════════

class MistakeType(str, Enum):
    COUNTER_TREND = "counter_trend"
    OVERSIZE = "oversize"
    STALE_DATA = "stale_data"
    LOW_CONFIDENCE = "low_confidence"
    HIGH_VOLATILITY = "high_volatility"
    AGAINST_SENTIMENT = "against_sentiment"
    REPEAT_LOSS = "repeat_loss"
    OTHER = "other"


@dataclass
class Mistake:
    """A detected trading mistake."""
    mistake_type: MistakeType
    severity: float           # 0.0 to 1.0
    description: str
    outcome: TradeOutcome
    timestamp: float = 0.0
    corrective_action: str = ""


class MistakeTracker:
    """
    Analyses losing trades to identify recurring patterns of mistakes.
    Emits corrective actions and adjusts confidence thresholds.
    """

    def __init__(self, max_history: int = 200) -> None:
        self._history: deque[Mistake] = deque(maxlen=max_history)
        self._pattern_counts: Dict[MistakeType, int] = {t: 0 for t in MistakeType}
        self._on_mistake: List[Callable[[Mistake], Any]] = []

    def on_mistake(self, callback: Callable[[Mistake], Any]) -> None:
        """Register callback for detected mistakes."""
        self._on_mistake.append(callback)

    def analyse(self, outcome: TradeOutcome) -> List[Mistake]:
        """Analyse a losing trade for mistake patterns."""
        if outcome.result == TradeResult.WIN:
            return []

        mistakes: List[Mistake] = []
        ind = outcome.indicators_at_entry

        # 1. Counter-trend trading
        ema_align = ind.get("ema_alignment", 0.0)
        if (outcome.direction == "LONG" and ema_align < -0.5) or \
           (outcome.direction == "SHORT" and ema_align > 0.5):
            m = Mistake(
                mistake_type=MistakeType.COUNTER_TREND,
                severity=0.8,
                description=f"Traded {outcome.direction} against strong EMA alignment ({ema_align:+.1f})",
                outcome=outcome,
                timestamp=time.time(),
                corrective_action="Increase EMA alignment weight in confluence scoring",
            )
            mistakes.append(m)

        # 2. Low confidence entry
        if outcome.confidence_at_entry < 0.55:
            m = Mistake(
                mistake_type=MistakeType.LOW_CONFIDENCE,
                severity=0.6,
                description=f"Entry confidence was only {outcome.confidence_at_entry:.2f}",
                outcome=outcome,
                timestamp=time.time(),
                corrective_action="Raise minimum confidence threshold to 0.60",
            )
            mistakes.append(m)

        # 3. High volatility (ATR > 3% of price)
        atr_pct = ind.get("atr_pct", 0.0)
        if atr_pct > 3.0:
            m = Mistake(
                mistake_type=MistakeType.HIGH_VOLATILITY,
                severity=0.7,
                description=f"ATR was {atr_pct:.1f}% — excessive volatility",
                outcome=outcome,
                timestamp=time.time(),
                corrective_action="Reduce position size in high-volatility environments",
            )
            mistakes.append(m)

        # 4. Repeat losses on same symbol
        recent_losses = [
            h for h in self._history
            if h.outcome.symbol == outcome.symbol
            and h.outcome.result == TradeResult.LOSS
        ]
        if len(recent_losses) >= 3:
            m = Mistake(
                mistake_type=MistakeType.REPEAT_LOSS,
                severity=0.9,
                description=f"{len(recent_losses)+1} consecutive losses on {outcome.symbol}",
                outcome=outcome,
                timestamp=time.time(),
                corrective_action=f"Temporarily exclude {outcome.symbol} from trading",
            )
            mistakes.append(m)

        # Record and notify
        for m in mistakes:
            self._history.append(m)
            self._pattern_counts[m.mistake_type] += 1
            for cb in self._on_mistake:
                try:
                    cb(m)
                except Exception as exc:
                    logger.warning(f"[MistakeTracker] Callback error: {exc}")

        if mistakes:
            logger.warning(
                f"[MistakeTracker] {len(mistakes)} mistakes detected for "
                f"{outcome.symbol} ({outcome.result.value})"
            )

        return mistakes

    def get_summary(self) -> Dict[str, Any]:
        """Return summary of detected mistake patterns."""
        return {
            "total_mistakes": len(self._history),
            "pattern_counts": dict(self._pattern_counts),
            "top_patterns": sorted(
                self._pattern_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3],
        }


# ════════════════════════════════════════════════════════
# Performance Tracker — Kill Switch
# ════════════════════════════════════════════════════════

@dataclass
class PerformanceSnapshot:
    """Point-in-time performance metrics."""
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    max_drawdown_pct: float
    sharpe_ratio: float
    avg_rr: float
    timestamp: float = 0.0


class PerformanceTracker:
    """
    Monitors key trading metrics and can halt trading if performance
    degrades below thresholds.

    Kill-switch triggers:
      • Win rate < 40% over last 50 trades
      • Max drawdown > 10%
      • Sharpe ratio < 0.5 over last 30 days
    """

    def __init__(
        self,
        min_win_rate: float = 0.40,
        max_drawdown_pct: float = 10.0,
        min_sharpe: float = 0.5,
        lookback_trades: int = 50,
    ) -> None:
        self._min_wr = min_win_rate
        self._max_dd = max_drawdown_pct
        self._min_sharpe = min_sharpe
        self._lookback = lookback_trades
        self._trades: deque[TradeOutcome] = deque(maxlen=500)
        self._is_paused = False
        self._pause_reason = ""
        self._peak_balance = 0.0
        self._current_balance = 0.0

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    @property
    def pause_reason(self) -> str:
        return self._pause_reason

    def set_balance(self, balance: float) -> None:
        self._current_balance = balance
        if balance > self._peak_balance:
            self._peak_balance = balance

    def record_trade(self, outcome: TradeOutcome) -> PerformanceSnapshot:
        """Record a trade and check performance thresholds."""
        self._trades.append(outcome)
        self._current_balance += outcome.pnl
        if self._current_balance > self._peak_balance:
            self._peak_balance = self._current_balance

        snapshot = self._compute_snapshot()

        # Check kill-switch conditions
        if snapshot.win_rate < self._min_wr and snapshot.total_trades >= self._lookback:
            self._is_paused = True
            self._pause_reason = f"Win rate {snapshot.win_rate:.1%} < {self._min_wr:.0%} threshold"
            logger.critical(f"[Performance] PAUSED: {self._pause_reason}")

        if snapshot.max_drawdown_pct > self._max_dd:
            self._is_paused = True
            self._pause_reason = f"Drawdown {snapshot.max_drawdown_pct:.1f}% > {self._max_dd}% limit"
            logger.critical(f"[Performance] PAUSED: {self._pause_reason}")

        if snapshot.sharpe_ratio < self._min_sharpe and snapshot.total_trades >= 30:
            self._is_paused = True
            self._pause_reason = f"Sharpe {snapshot.sharpe_ratio:.2f} < {self._min_sharpe} minimum"
            logger.critical(f"[Performance] PAUSED: {self._pause_reason}")

        return snapshot

    def resume(self) -> None:
        """Manually resume trading after review."""
        self._is_paused = False
        self._pause_reason = ""
        logger.info("[Performance] Trading RESUMED")

    def _compute_snapshot(self) -> PerformanceSnapshot:
        """Compute current performance metrics."""
        recent = list(self._trades)[-self._lookback:]
        if not recent:
            return PerformanceSnapshot(
                win_rate=0.0, total_trades=0, winning_trades=0, losing_trades=0,
                total_pnl=0.0, max_drawdown_pct=0.0, sharpe_ratio=0.0, avg_rr=0.0,
                timestamp=time.time(),
            )

        wins = sum(1 for t in recent if t.result == TradeResult.WIN)
        losses = sum(1 for t in recent if t.result == TradeResult.LOSS)
        total = len(recent)
        pnls = [t.pnl_pct for t in recent]

        # Sharpe ratio (annualised, assuming ~1 trade/day)
        if len(pnls) > 1:
            mean_ret = np.mean(pnls)
            std_ret = np.std(pnls) or 1e-10
            sharpe = (mean_ret / std_ret) * np.sqrt(252)
        else:
            sharpe = 0.0

        # Max drawdown
        dd = 0.0
        if self._peak_balance > 0:
            dd = ((self._peak_balance - self._current_balance) / self._peak_balance) * 100

        # Average RR
        win_pnls = [t.pnl for t in recent if t.result == TradeResult.WIN]
        loss_pnls = [abs(t.pnl) for t in recent if t.result == TradeResult.LOSS]
        avg_win = np.mean(win_pnls) if win_pnls else 0.0
        avg_loss = np.mean(loss_pnls) if loss_pnls else 1.0
        avg_rr = avg_win / avg_loss if avg_loss > 0 else 0.0

        return PerformanceSnapshot(
            win_rate=wins / total if total > 0 else 0.0,
            total_trades=total,
            winning_trades=wins,
            losing_trades=losses,
            total_pnl=sum(t.pnl for t in recent),
            max_drawdown_pct=round(dd, 2),
            sharpe_ratio=round(float(sharpe), 3),
            avg_rr=round(float(avg_rr), 2),
            timestamp=time.time(),
        )

    def get_snapshot(self) -> PerformanceSnapshot:
        """Public access to current performance metrics."""
        return self._compute_snapshot()
