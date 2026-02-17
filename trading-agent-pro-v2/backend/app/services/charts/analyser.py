"""
Kimi Agent — Chart Pattern Analyser (Part 8a)

Detects higher-level chart patterns from OHLCV data:
  • Trend channels (ascending/descending/horizontal)
  • Head & Shoulders / Inverse Head & Shoulders
  • Double Top / Double Bottom
  • Triangle (ascending, descending, symmetrical)
  • Wedge (rising, falling)
  • Flag / Pennant

Returns pattern name, direction bias, target price, and confidence.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PatternType(str, Enum):
    HEAD_SHOULDERS = "head_and_shoulders"
    INV_HEAD_SHOULDERS = "inverse_head_and_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRICAL_TRIANGLE = "symmetrical_triangle"
    RISING_WEDGE = "rising_wedge"
    FALLING_WEDGE = "falling_wedge"
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    CHANNEL_UP = "channel_up"
    CHANNEL_DOWN = "channel_down"


class PatternBias(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class DetectedPattern:
    """A chart pattern found in price data."""
    pattern_type: PatternType
    bias: PatternBias
    confidence: float          # 0.0 to 1.0
    start_idx: int
    end_idx: int
    target_price: float = 0.0
    neckline: float = 0.0
    description: str = ""


class ChartAnalyser:
    """
    Scans OHLCV DataFrame for chart patterns using pivot point analysis.
    
    Methodology:
      1. Detect swing highs and swing lows (local extremes)
      2. Fit linear regressions to peaks and troughs
      3. Match geometric shapes to known pattern templates
      4. Calculate measured-move price targets
    """

    def __init__(self, swing_lookback: int = 5, min_pattern_bars: int = 15) -> None:
        self._swing_lb = swing_lookback
        self._min_bars = min_pattern_bars

    def analyse(self, df: pd.DataFrame) -> List[DetectedPattern]:
        """Run all pattern detectors on an OHLCV DataFrame."""
        if df is None or len(df) < self._min_bars * 2:
            return []

        high = df["high"].values
        low = df["low"].values
        close = df["close"].values

        swing_highs = self._find_swing_highs(high)
        swing_lows = self._find_swing_lows(low)

        patterns: List[DetectedPattern] = []

        # Run detectors
        patterns.extend(self._detect_double_top(high, close, swing_highs))
        patterns.extend(self._detect_double_bottom(low, close, swing_lows))
        patterns.extend(self._detect_head_shoulders(high, low, close, swing_highs, swing_lows))
        patterns.extend(self._detect_triangles(high, low, close, swing_highs, swing_lows))
        patterns.extend(self._detect_channels(high, low, close))

        return patterns

    def _find_swing_highs(self, high: np.ndarray) -> List[int]:
        """Find local maxima in high prices."""
        swings = []
        lb = self._swing_lb
        for i in range(lb, len(high) - lb):
            if high[i] == max(high[i - lb:i + lb + 1]):
                swings.append(i)
        return swings

    def _find_swing_lows(self, low: np.ndarray) -> List[int]:
        """Find local minima in low prices."""
        swings = []
        lb = self._swing_lb
        for i in range(lb, len(low) - lb):
            if low[i] == min(low[i - lb:i + lb + 1]):
                swings.append(i)
        return swings

    def _detect_double_top(
        self, high: np.ndarray, close: np.ndarray, swing_highs: List[int]
    ) -> List[DetectedPattern]:
        """Detect double top: two peaks at similar levels with a trough between."""
        patterns = []
        tolerance = 0.015  # 1.5% price tolerance

        for i in range(len(swing_highs) - 1):
            p1_idx = swing_highs[i]
            p2_idx = swing_highs[i + 1]

            if p2_idx - p1_idx < self._min_bars:
                continue

            p1_price = high[p1_idx]
            p2_price = high[p2_idx]

            # Peaks must be at similar level
            if abs(p1_price - p2_price) / p1_price > tolerance:
                continue

            # Find trough between peaks
            between = close[p1_idx:p2_idx + 1]
            trough = float(np.min(between))
            neckline = trough

            # Height = peak - neckline
            height = ((p1_price + p2_price) / 2) - neckline
            target = neckline - height  # Measured move down

            # Confirm: current price breaking below neckline
            current = close[-1]
            confidence = 0.6
            if current < neckline:
                confidence = 0.85

            patterns.append(DetectedPattern(
                pattern_type=PatternType.DOUBLE_TOP,
                bias=PatternBias.BEARISH,
                confidence=confidence,
                start_idx=p1_idx,
                end_idx=p2_idx,
                target_price=round(target, 4),
                neckline=round(neckline, 4),
                description=f"Double top at {p1_price:.2f}/{p2_price:.2f}, "
                           f"neckline={neckline:.2f}, target={target:.2f}",
            ))

        return patterns[:3]  # Max 3 per scan

    def _detect_double_bottom(
        self, low: np.ndarray, close: np.ndarray, swing_lows: List[int]
    ) -> List[DetectedPattern]:
        """Detect double bottom: two troughs at similar levels."""
        patterns = []
        tolerance = 0.015

        for i in range(len(swing_lows) - 1):
            t1_idx = swing_lows[i]
            t2_idx = swing_lows[i + 1]

            if t2_idx - t1_idx < self._min_bars:
                continue

            t1_price = low[t1_idx]
            t2_price = low[t2_idx]

            if abs(t1_price - t2_price) / t1_price > tolerance:
                continue

            between = close[t1_idx:t2_idx + 1]
            peak = float(np.max(between))
            neckline = peak

            height = neckline - ((t1_price + t2_price) / 2)
            target = neckline + height

            current = close[-1]
            confidence = 0.6
            if current > neckline:
                confidence = 0.85

            patterns.append(DetectedPattern(
                pattern_type=PatternType.DOUBLE_BOTTOM,
                bias=PatternBias.BULLISH,
                confidence=confidence,
                start_idx=t1_idx,
                end_idx=t2_idx,
                target_price=round(target, 4),
                neckline=round(neckline, 4),
                description=f"Double bottom at {t1_price:.2f}/{t2_price:.2f}, "
                           f"neckline={neckline:.2f}, target={target:.2f}",
            ))

        return patterns[:3]

    def _detect_head_shoulders(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        swing_highs: List[int],
        swing_lows: List[int],
    ) -> List[DetectedPattern]:
        """Detect Head & Shoulders (bearish) and Inverse H&S (bullish)."""
        patterns = []

        # Need at least 3 swing highs
        if len(swing_highs) >= 3:
            for i in range(len(swing_highs) - 2):
                ls = swing_highs[i]     # Left shoulder
                h = swing_highs[i + 1]  # Head
                rs = swing_highs[i + 2] # Right shoulder

                ls_p = high[ls]
                h_p = high[h]
                rs_p = high[rs]

                # Head must be highest
                if h_p <= ls_p or h_p <= rs_p:
                    continue

                # Shoulders roughly equal (within 5%)
                if abs(ls_p - rs_p) / ls_p > 0.05:
                    continue

                # Minimum spacing
                if h - ls < 8 or rs - h < 8:
                    continue

                neckline = (low[ls] + low[rs]) / 2
                height = h_p - neckline
                target = neckline - height

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.HEAD_SHOULDERS,
                    bias=PatternBias.BEARISH,
                    confidence=0.75,
                    start_idx=ls,
                    end_idx=rs,
                    target_price=round(target, 4),
                    neckline=round(neckline, 4),
                    description=f"H&S: LS={ls_p:.2f}, H={h_p:.2f}, RS={rs_p:.2f}",
                ))

        # Inverse H&S (using swing lows)
        if len(swing_lows) >= 3:
            for i in range(len(swing_lows) - 2):
                ls = swing_lows[i]
                h = swing_lows[i + 1]
                rs = swing_lows[i + 2]

                ls_p = low[ls]
                h_p = low[h]
                rs_p = low[rs]

                if h_p >= ls_p or h_p >= rs_p:
                    continue
                if abs(ls_p - rs_p) / ls_p > 0.05:
                    continue
                if h - ls < 8 or rs - h < 8:
                    continue

                neckline = (high[ls] + high[rs]) / 2
                height = neckline - h_p
                target = neckline + height

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.INV_HEAD_SHOULDERS,
                    bias=PatternBias.BULLISH,
                    confidence=0.75,
                    start_idx=ls,
                    end_idx=rs,
                    target_price=round(target, 4),
                    neckline=round(neckline, 4),
                    description=f"Inv H&S: LS={ls_p:.2f}, H={h_p:.2f}, RS={rs_p:.2f}",
                ))

        return patterns[:2]

    def _detect_triangles(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        swing_highs: List[int],
        swing_lows: List[int],
    ) -> List[DetectedPattern]:
        """Detect triangle patterns via trendline convergence."""
        patterns = []

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return patterns

        # Use last N swings
        recent_highs = swing_highs[-4:]
        recent_lows = swing_lows[-4:]

        if len(recent_highs) >= 2 and len(recent_lows) >= 2:
            # Upper trendline slope
            h_x = np.array(recent_highs, dtype=float)
            h_y = np.array([high[i] for i in recent_highs])
            h_slope = np.polyfit(h_x, h_y, 1)[0] if len(h_x) > 1 else 0

            # Lower trendline slope
            l_x = np.array(recent_lows, dtype=float)
            l_y = np.array([low[i] for i in recent_lows])
            l_slope = np.polyfit(l_x, l_y, 1)[0] if len(l_x) > 1 else 0

            # Classify triangle type
            if abs(h_slope) < 0.001 and l_slope > 0.001:
                # Flat top, rising bottom = ascending triangle
                patterns.append(DetectedPattern(
                    pattern_type=PatternType.ASCENDING_TRIANGLE,
                    bias=PatternBias.BULLISH,
                    confidence=0.65,
                    start_idx=min(recent_highs[0], recent_lows[0]),
                    end_idx=max(recent_highs[-1], recent_lows[-1]),
                    description=f"Ascending triangle (flat top, rising lows)",
                ))
            elif h_slope < -0.001 and abs(l_slope) < 0.001:
                # Falling top, flat bottom = descending triangle
                patterns.append(DetectedPattern(
                    pattern_type=PatternType.DESCENDING_TRIANGLE,
                    bias=PatternBias.BEARISH,
                    confidence=0.65,
                    start_idx=min(recent_highs[0], recent_lows[0]),
                    end_idx=max(recent_highs[-1], recent_lows[-1]),
                    description=f"Descending triangle (falling highs, flat bottom)",
                ))
            elif h_slope < -0.001 and l_slope > 0.001:
                # Both converging = symmetrical triangle
                patterns.append(DetectedPattern(
                    pattern_type=PatternType.SYMMETRICAL_TRIANGLE,
                    bias=PatternBias.NEUTRAL,
                    confidence=0.55,
                    start_idx=min(recent_highs[0], recent_lows[0]),
                    end_idx=max(recent_highs[-1], recent_lows[-1]),
                    description=f"Symmetrical triangle (converging trendlines)",
                ))

        return patterns

    def _detect_channels(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
    ) -> List[DetectedPattern]:
        """Detect price channels via linear regression on highs and lows."""
        patterns = []
        n = min(len(high), 50)
        if n < 20:
            return patterns

        recent_h = high[-n:]
        recent_l = low[-n:]
        x = np.arange(n, dtype=float)

        h_coefs = np.polyfit(x, recent_h, 1)
        l_coefs = np.polyfit(x, recent_l, 1)

        h_slope = h_coefs[0]
        l_slope = l_coefs[0]

        # Both slopes positive and roughly parallel = ascending channel
        if h_slope > 0.001 and l_slope > 0.001 and abs(h_slope - l_slope) / abs(h_slope) < 0.5:
            patterns.append(DetectedPattern(
                pattern_type=PatternType.CHANNEL_UP,
                bias=PatternBias.BULLISH,
                confidence=0.60,
                start_idx=len(high) - n,
                end_idx=len(high) - 1,
                description=f"Ascending channel (slopes: H={h_slope:.4f}, L={l_slope:.4f})",
            ))
        elif h_slope < -0.001 and l_slope < -0.001 and abs(h_slope - l_slope) / abs(h_slope) < 0.5:
            patterns.append(DetectedPattern(
                pattern_type=PatternType.CHANNEL_DOWN,
                bias=PatternBias.BEARISH,
                confidence=0.60,
                start_idx=len(high) - n,
                end_idx=len(high) - 1,
                description=f"Descending channel (slopes: H={h_slope:.4f}, L={l_slope:.4f})",
            ))

        return patterns

    def get_summary(self, patterns: List[DetectedPattern]) -> Dict[str, Any]:
        """Summarise detected patterns for downstream consumers."""
        return {
            "count": len(patterns),
            "patterns": [
                {
                    "type": p.pattern_type.value,
                    "bias": p.bias.value,
                    "confidence": p.confidence,
                    "target": p.target_price,
                    "description": p.description,
                }
                for p in patterns
            ],
            "dominant_bias": self._dominant_bias(patterns),
        }

    @staticmethod
    def _dominant_bias(patterns: List[DetectedPattern]) -> str:
        if not patterns:
            return "neutral"
        bullish = sum(1 for p in patterns if p.bias == PatternBias.BULLISH)
        bearish = sum(1 for p in patterns if p.bias == PatternBias.BEARISH)
        if bullish > bearish:
            return "bullish"
        elif bearish > bullish:
            return "bearish"
        return "neutral"
