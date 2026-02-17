"""
Kimi Agent — Multi-Timeframe Confluence Analyser (Part 3)

Computes weighted confluence scores across multiple timeframes to identify
high-probability setups.  Each timeframe gets a weight reflecting its
reliability:

  D1  → 0.35  (most reliable for trend direction)
  H4  → 0.25
  H1  → 0.20
  M15 → 0.12
  M5  → 0.08

The final confluence score ranges from -1.0 (strong bearish) to +1.0
(strong bullish).  A signal is only generated when confluence exceeds a
configurable threshold (default ±0.60).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import pandas as pd

from app.services.analysis.indicators import IndicatorEngine

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────

TIMEFRAME_WEIGHTS: Dict[str, float] = {
    "D1": 0.35,
    "H4": 0.25,
    "H1": 0.20,
    "M15": 0.12,
    "M5": 0.08,
}

DEFAULT_THRESHOLD = 0.60


class SignalDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


@dataclass
class TimeframeSignal:
    """Signal produced from a single timeframe."""
    timeframe: str
    score: float             # -1.0 to +1.0
    weight: float
    trend_score: float = 0.0
    momentum_score: float = 0.0
    volatility_score: float = 0.0
    volume_score: float = 0.0
    pattern_score: float = 0.0
    sr_score: float = 0.0
    indicators: Dict[str, float] = field(default_factory=dict)


@dataclass
class ConfluenceResult:
    """Final confluence output across all timeframes."""
    symbol: str
    direction: SignalDirection
    confluence_score: float    # Weighted average: -1.0 to +1.0
    confidence: float          # 0.0 to 1.0 (how many TFs agree)
    timeframe_signals: Dict[str, TimeframeSignal] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)

    @property
    def is_actionable(self) -> bool:
        return abs(self.confluence_score) >= DEFAULT_THRESHOLD


class ConfluenceEngine:
    """
    Accepts rolling OHLCV DataFrames per timeframe for a single symbol.
    Computes IndicatorEngine on each, scores directional bias, then
    produces a weighted confluence score.

    Usage::

        engine = ConfluenceEngine()
        result = engine.analyse(
            symbol="BTC/USDT",
            candles={
                "D1": df_d1,
                "H4": df_h4,
                "H1": df_h1,
                "M15": df_m15,
            },
        )
        if result.is_actionable:
            print(result.direction, result.confluence_score)
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self._weights = weights or TIMEFRAME_WEIGHTS
        self._threshold = threshold
        self._indicator_engine = IndicatorEngine()

    def analyse(
        self,
        symbol: str,
        candles: Dict[str, pd.DataFrame],
    ) -> ConfluenceResult:
        """
        Run full multi-timeframe confluence analysis.

        Args:
            symbol:  Trading pair / ticker
            candles: dict mapping timeframe → OHLCV DataFrame

        Returns:
            ConfluenceResult with weighted score and per-TF breakdowns.
        """
        tf_signals: Dict[str, TimeframeSignal] = {}
        reasons: List[str] = []

        for tf, df in candles.items():
            weight = self._weights.get(tf, 0.05)
            indicators = self._indicator_engine.compute(df)

            if not indicators:
                logger.warning(f"[Confluence] Skipping {tf} — no indicators")
                continue

            signal = self._score_timeframe(tf, weight, indicators)
            tf_signals[tf] = signal

        # Weighted confluence
        total_weight = sum(s.weight for s in tf_signals.values())
        if total_weight == 0:
            return ConfluenceResult(
                symbol=symbol,
                direction=SignalDirection.NEUTRAL,
                confluence_score=0.0,
                confidence=0.0,
                reasons=["No timeframe data available"],
            )

        raw_score = sum(s.score * s.weight for s in tf_signals.values()) / total_weight

        # Confidence = how many TFs agree with the majority direction
        majority = 1.0 if raw_score >= 0 else -1.0
        agreeing = sum(
            1 for s in tf_signals.values()
            if (s.score >= 0 and majority >= 0) or (s.score < 0 and majority < 0)
        )
        confidence = agreeing / len(tf_signals) if tf_signals else 0.0

        # Direction
        if raw_score >= self._threshold:
            direction = SignalDirection.LONG
            reasons.append(f"Confluence score {raw_score:.2f} above threshold +{self._threshold}")
        elif raw_score <= -self._threshold:
            direction = SignalDirection.SHORT
            reasons.append(f"Confluence score {raw_score:.2f} below threshold -{self._threshold}")
        else:
            direction = SignalDirection.NEUTRAL
            reasons.append(f"Score {raw_score:.2f} inside neutral zone (±{self._threshold})")

        # Add TF-level reasoning
        for tf, sig in tf_signals.items():
            bias = "bullish" if sig.score >= 0 else "bearish"
            reasons.append(
                f"  {tf} ({sig.weight:.0%} weight): {sig.score:+.2f} ({bias}) — "
                f"trend={sig.trend_score:+.2f}, mom={sig.momentum_score:+.2f}, "
                f"vol={sig.volatility_score:+.2f}"
            )

        return ConfluenceResult(
            symbol=symbol,
            direction=direction,
            confluence_score=round(raw_score, 4),
            confidence=round(confidence, 3),
            timeframe_signals=tf_signals,
            reasons=reasons,
        )

    def _score_timeframe(
        self, tf: str, weight: float, ind: Dict[str, float]
    ) -> TimeframeSignal:
        """
        Convert raw indicators into a directional score for one timeframe.
        Each subcategory contributes an equal share of the final TF score.
        """
        trend = self._score_trend(ind)
        momentum = self._score_momentum(ind)
        volatility = self._score_volatility(ind)
        volume = self._score_volume(ind)
        pattern = self._score_patterns(ind)
        sr = self._score_support_resistance(ind)

        # Weighted average of subcategories
        components = [
            (trend, 0.30),
            (momentum, 0.25),
            (volatility, 0.10),
            (volume, 0.10),
            (pattern, 0.10),
            (sr, 0.15),
        ]
        score = sum(s * w for s, w in components)
        score = max(-1.0, min(1.0, score))

        return TimeframeSignal(
            timeframe=tf,
            score=round(score, 4),
            weight=weight,
            trend_score=round(trend, 4),
            momentum_score=round(momentum, 4),
            volatility_score=round(volatility, 4),
            volume_score=round(volume, 4),
            pattern_score=round(pattern, 4),
            sr_score=round(sr, 4),
            indicators=ind,
        )

    # ── Sub-scoring functions (each returns -1.0 to +1.0) ──

    @staticmethod
    def _score_trend(ind: Dict[str, float]) -> float:
        """Score trend from EMA alignment, ADX, Supertrend, Ichimoku."""
        score = 0.0
        n = 0

        # EMA alignment
        alignment = ind.get("ema_alignment", 0.0)
        score += alignment
        n += 1

        # Supertrend direction
        st_dir = ind.get("supertrend_direction", 0.0)
        score += st_dir
        n += 1

        # ADX strength — amplifies direction
        adx = ind.get("adx_14", 0.0)
        di_plus = ind.get("di_plus", 0.0)
        di_minus = ind.get("di_minus", 0.0)
        if adx > 25:
            di_bias = 1.0 if di_plus > di_minus else -1.0
            strength = min(adx / 50.0, 1.0)  # Scale ADX to 0-1
            score += di_bias * strength
            n += 1

        # Ichimoku: price above cloud = bullish
        senkou_a = ind.get("ichimoku_senkou_a", 0.0)
        senkou_b = ind.get("ichimoku_senkou_b", 0.0)
        ema_9 = ind.get("ema_9", 0.0)
        if senkou_a and senkou_b and ema_9:
            cloud_top = max(senkou_a, senkou_b)
            cloud_bot = min(senkou_a, senkou_b)
            if ema_9 > cloud_top:
                score += 1.0
            elif ema_9 < cloud_bot:
                score += -1.0
            n += 1

        # PSAR direction
        psar_dir = ind.get("psar_direction", 0.0)
        score += psar_dir
        n += 1

        return max(-1.0, min(1.0, score / max(n, 1)))

    @staticmethod
    def _score_momentum(ind: Dict[str, float]) -> float:
        """Score momentum from RSI, MACD, Stochastic, CCI, Williams %R."""
        score = 0.0
        n = 0

        # RSI
        rsi = ind.get("rsi_14", 50.0)
        if rsi > 70:
            score -= 0.5  # Overbought = bearish pressure
        elif rsi > 55:
            score += (rsi - 50) / 20.0  # Mild bullish
        elif rsi < 30:
            score += 0.5  # Oversold = bullish pressure
        elif rsi < 45:
            score -= (50 - rsi) / 20.0  # Mild bearish
        n += 1

        # MACD histogram
        hist = ind.get("macd_histogram", 0.0)
        macd_signal = ind.get("macd_signal", 0.0)
        if hist > 0:
            score += min(hist / max(abs(macd_signal), 0.001), 1.0)
        else:
            score += max(hist / max(abs(macd_signal), 0.001), -1.0)
        n += 1

        # Stochastic
        stoch_k = ind.get("stoch_k", 50.0)
        stoch_d = ind.get("stoch_d", 50.0)
        if stoch_k > 80:
            score -= 0.3
        elif stoch_k < 20:
            score += 0.3
        if stoch_k > stoch_d:
            score += 0.2
        else:
            score -= 0.2
        n += 1

        # CCI
        cci = ind.get("cci_20", 0.0)
        if cci > 100:
            score += 0.5
        elif cci < -100:
            score -= 0.5
        n += 1

        # Williams %R
        wr = ind.get("williams_r", -50.0)
        if wr > -20:
            score -= 0.3  # Overbought
        elif wr < -80:
            score += 0.3  # Oversold
        n += 1

        return max(-1.0, min(1.0, score / max(n, 1)))

    @staticmethod
    def _score_volatility(ind: Dict[str, float]) -> float:
        """
        Volatility doesn't have direct direction, but narrow BB = squeeze
        (potential breakout). Return how favourable conditions are for a trade.
        """
        bb_bw = ind.get("bb_bandwidth", 0.0)
        pct_b = ind.get("bb_percent_b", 0.5)
        chop = ind.get("choppiness_14", 50.0)

        score = 0.0
        # Squeeze = potential breakout (positive)
        if bb_bw < 0.04:
            score += 0.5
        # Percent B > 1 = above upper band (bullish momentum)
        if pct_b > 1.0:
            score += 0.3
        elif pct_b < 0.0:
            score -= 0.3

        # Choppiness < 40 = trending, > 60 = choppy
        if chop < 40:
            score += 0.3  # Trending environment = good for signals
        elif chop > 60:
            score -= 0.3  # Choppy = unreliable signals

        return max(-1.0, min(1.0, score))

    @staticmethod
    def _score_volume(ind: Dict[str, float]) -> float:
        """Score volume confirmation."""
        score = 0.0

        surge = ind.get("volume_surge", 0.0)
        if surge:
            score += 0.4  # Volume confirms move

        cmf = ind.get("cmf_20", 0.0)
        if cmf > 0.05:
            score += 0.3
        elif cmf < -0.05:
            score -= 0.3

        mfi = ind.get("mfi_14", 50.0)
        if mfi > 80:
            score -= 0.2  # Overbought by money flow
        elif mfi < 20:
            score += 0.2  # Oversold

        ratio = ind.get("volume_ratio", 1.0)
        if ratio > 2.0:
            score += 0.2  # High conviction move
        elif ratio < 0.5:
            score -= 0.1  # Low participation

        return max(-1.0, min(1.0, score))

    @staticmethod
    def _score_patterns(ind: Dict[str, float]) -> float:
        """Aggregate candlestick pattern signals."""
        pattern_keys = [k for k in ind if k.startswith("pattern_")]
        if not pattern_keys:
            return 0.0

        total = sum(ind[k] for k in pattern_keys)
        # Normalise: max possible = len(pattern_keys)
        return max(-1.0, min(1.0, total / max(len(pattern_keys), 1)))

    @staticmethod
    def _score_support_resistance(ind: Dict[str, float]) -> float:
        """Score proximity to support/resistance levels."""
        score = 0.0
        near_sup = ind.get("near_support", 0.0)
        near_res = ind.get("near_resistance", 0.0)

        if near_sup:
            score += 0.5  # Near support → potential bounce → bullish
        if near_res:
            score -= 0.5  # Near resistance → potential rejection → bearish

        return max(-1.0, min(1.0, score))
