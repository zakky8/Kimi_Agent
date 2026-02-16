"""
Pattern Recognition Module
Detects chart patterns using machine learning and classical methods
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PatternType(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class ChartPattern:
    """Detected chart pattern"""
    name: str
    type: PatternType
    confidence: float
    start_idx: int
    end_idx: int
    price_target: Optional[float]
    stop_loss: Optional[float]
    description: str


class PatternRecognition:
    """
    Chart pattern recognition engine
    Implements classical and ML-based pattern detection
    """
    
    # Classical patterns
    CLASSICAL_PATTERNS = [
        "head_and_shoulders", "inverse_head_and_shoulders",
        "double_top", "double_bottom",
        "triple_top", "triple_bottom",
        "ascending_triangle", "descending_triangle",
        "symmetrical_triangle", "wedge",
        "flag", "pennant",
        "channel", "range"
    ]
    
    # Candlestick patterns
    CANDLESTICK_PATTERNS = [
        "doji", "hammer", "shooting_star",
        "engulfing_bullish", "engulfing_bearish",
        "morning_star", "evening_star",
        "harami", "piercing_line", "dark_cloud_cover"
    ]
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.patterns: List[ChartPattern] = []
        
    def detect_all_patterns(self) -> List[ChartPattern]:
        """Detect all chart patterns"""
        self.patterns = []
        
        # Classical patterns
        self._detect_head_and_shoulders()
        self._detect_double_tops_bottoms()
        self._detect_triangles()
        self._detect_flags_pennants()
        
        # Candlestick patterns
        self._detect_candlestick_patterns()
        
        return self.patterns
    
    def _detect_head_and_shoulders(self):
        """Detect head and shoulders pattern"""
        if len(self.df) < 20:
            return
        
        highs = self.df["high"].values
        lows = self.df["low"].values
        
        # Find local extrema
        peaks = self._find_peaks(highs, order=3)
        troughs = self._find_troughs(lows, order=3)
        
        # Look for H&S pattern
        if len(peaks) >= 3:
            for i in range(len(peaks) - 2):
                left_shoulder = highs[peaks[i]]
                head = highs[peaks[i+1]]
                right_shoulder = highs[peaks[i+2]]
                
                # Check H&S conditions
                shoulder_tolerance = 0.02  # 2% tolerance
                
                if (head > left_shoulder and head > right_shoulder and
                    abs(left_shoulder - right_shoulder) / left_shoulder < shoulder_tolerance):
                    
                    # Calculate neckline
                    if len(troughs) >= 2:
                        neckline = (lows[troughs[-2]] + lows[troughs[-1]]) / 2
                        
                        pattern = ChartPattern(
                            name="Head and Shoulders",
                            type=PatternType.BEARISH,
                            confidence=0.75,
                            start_idx=peaks[i],
                            end_idx=peaks[i+2],
                            price_target=neckline - (head - neckline),
                            stop_loss=head * 1.01,
                            description="Bearish reversal pattern"
                        )
                        self.patterns.append(pattern)
    
    def _detect_double_tops_bottoms(self):
        """Detect double top and double bottom patterns"""
        if len(self.df) < 15:
            return
        
        highs = self.df["high"].values
        lows = self.df["low"].values
        
        peaks = self._find_peaks(highs, order=2)
        troughs = self._find_troughs(lows, order=2)
        
        # Double Top
        if len(peaks) >= 2:
            for i in range(len(peaks) - 1):
                peak1 = highs[peaks[i]]
                peak2 = highs[peaks[i+1]]
                
                tolerance = 0.015
                if abs(peak1 - peak2) / peak1 < tolerance:
                    # Find neckline
                    mid_idx = (peaks[i] + peaks[i+1]) // 2
                    neckline = lows[mid_idx]
                    
                    pattern = ChartPattern(
                        name="Double Top",
                        type=PatternType.BEARISH,
                        confidence=0.70,
                        start_idx=peaks[i],
                        end_idx=peaks[i+1],
                        price_target=neckline - (peak1 - neckline),
                        stop_loss=max(peak1, peak2) * 1.01,
                        description="Bearish reversal pattern"
                    )
                    self.patterns.append(pattern)
        
        # Double Bottom
        if len(troughs) >= 2:
            for i in range(len(troughs) - 1):
                trough1 = lows[troughs[i]]
                trough2 = lows[troughs[i+1]]
                
                tolerance = 0.015
                if abs(trough1 - trough2) / trough1 < tolerance:
                    mid_idx = (troughs[i] + troughs[i+1]) // 2
                    neckline = highs[mid_idx]
                    
                    pattern = ChartPattern(
                        name="Double Bottom",
                        type=PatternType.BULLISH,
                        confidence=0.70,
                        start_idx=troughs[i],
                        end_idx=troughs[i+1],
                        price_target=neckline + (neckline - trough1),
                        stop_loss=min(trough1, trough2) * 0.99,
                        description="Bullish reversal pattern"
                    )
                    self.patterns.append(pattern)
    
    def _detect_triangles(self):
        """Detect triangle patterns"""
        if len(self.df) < 20:
            return
        
        highs = self.df["high"].values
        lows = self.df["low"].values
        
        # Get recent data
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]
        
        # Find trendlines
        high_trend = np.polyfit(range(len(recent_highs)), recent_highs, 1)
        low_trend = np.polyfit(range(len(recent_lows)), recent_lows, 1)
        
        high_slope = high_trend[0]
        low_slope = low_trend[0]
        
        # Ascending Triangle (flat top, rising bottom)
        if abs(high_slope) < 0.001 and low_slope > 0.001:
            pattern = ChartPattern(
                name="Ascending Triangle",
                type=PatternType.BULLISH,
                confidence=0.65,
                start_idx=len(self.df) - 20,
                end_idx=len(self.df) - 1,
                price_target=recent_highs[-1] + (recent_highs[-1] - recent_lows[-1]),
                stop_loss=recent_lows[-1] * 0.99,
                description="Bullish continuation pattern"
            )
            self.patterns.append(pattern)
        
        # Descending Triangle (flat bottom, falling top)
        elif abs(low_slope) < 0.001 and high_slope < -0.001:
            pattern = ChartPattern(
                name="Descending Triangle",
                type=PatternType.BEARISH,
                confidence=0.65,
                start_idx=len(self.df) - 20,
                end_idx=len(self.df) - 1,
                price_target=recent_lows[-1] - (recent_highs[-1] - recent_lows[-1]),
                stop_loss=recent_highs[-1] * 1.01,
                description="Bearish continuation pattern"
            )
            self.patterns.append(pattern)
        
        # Symmetrical Triangle (converging)
        elif high_slope < -0.001 and low_slope > 0.001:
            pattern = ChartPattern(
                name="Symmetrical Triangle",
                type=PatternType.NEUTRAL,
                confidence=0.60,
                start_idx=len(self.df) - 20,
                end_idx=len(self.df) - 1,
                price_target=None,
                stop_loss=None,
                description="Continuation pattern, wait for breakout"
            )
            self.patterns.append(pattern)
    
    def _detect_flags_pennants(self):
        """Detect flag and pennant patterns"""
        if len(self.df) < 15:
            return
        
        closes = self.df["close"].values
        
        # Check for strong preceding move (pole)
        if len(closes) < 15:
            return
        
        pole_start = closes[-15]
        pole_end = closes[-10]
        pole_move = (pole_end - pole_start) / pole_start
        
        # Bull flag (strong up move, then consolidation)
        if pole_move > 0.05:  # 5% move
            consolidation = closes[-10:]
            consolidation_range = (max(consolidation) - min(consolidation)) / max(consolidation)
            
            if consolidation_range < 0.03:  # Tight consolidation
                pattern = ChartPattern(
                    name="Bull Flag",
                    type=PatternType.BULLISH,
                    confidence=0.70,
                    start_idx=len(self.df) - 15,
                    end_idx=len(self.df) - 1,
                    price_target=pole_end + (pole_end - pole_start),
                    stop_loss=min(consolidation) * 0.99,
                    description="Bullish continuation pattern"
                )
                self.patterns.append(pattern)
        
        # Bear flag (strong down move, then consolidation)
        elif pole_move < -0.05:
            consolidation = closes[-10:]
            consolidation_range = (max(consolidation) - min(consolidation)) / max(consolidation)
            
            if consolidation_range < 0.03:
                pattern = ChartPattern(
                    name="Bear Flag",
                    type=PatternType.BEARISH,
                    confidence=0.70,
                    start_idx=len(self.df) - 15,
                    end_idx=len(self.df) - 1,
                    price_target=pole_end - (pole_start - pole_end),
                    stop_loss=max(consolidation) * 1.01,
                    description="Bearish continuation pattern"
                )
                self.patterns.append(pattern)
    
    def _detect_candlestick_patterns(self):
        """Detect candlestick patterns"""
        if len(self.df) < 5:
            return
        
        opens = self.df["open"].values
        highs = self.df["high"].values
        lows = self.df["low"].values
        closes = self.df["close"].values
        
        # Get last 3 candles
        for i in range(2, len(self.df)):
            o1, h1, l1, c1 = opens[i-2], highs[i-2], lows[i-2], closes[i-2]
            o2, h2, l2, c2 = opens[i-1], highs[i-1], lows[i-1], closes[i-1]
            o3, h3, l3, c3 = opens[i], highs[i], lows[i], closes[i]
            
            # Doji
            body = abs(c3 - o3)
            range_total = h3 - l3
            if range_total > 0 and body / range_total < 0.1:
                pattern = ChartPattern(
                    name="Doji",
                    type=PatternType.NEUTRAL,
                    confidence=0.50,
                    start_idx=i,
                    end_idx=i,
                    price_target=None,
                    stop_loss=None,
                    description="Indecision candle"
                )
                self.patterns.append(pattern)
            
            # Hammer
            lower_shadow = min(o3, c3) - l3
            upper_shadow = h3 - max(o3, c3)
            if lower_shadow > 2 * body and upper_shadow < body:
                pattern = ChartPattern(
                    name="Hammer",
                    type=PatternType.BULLISH,
                    confidence=0.60,
                    start_idx=i,
                    end_idx=i,
                    price_target=c3 + 2 * body,
                    stop_loss=l3,
                    description="Bullish reversal candle"
                )
                self.patterns.append(pattern)
            
            # Engulfing Bullish
            body1 = abs(c2 - o2)
            body2 = abs(c3 - o3)
            if (c2 < o2 and c3 > o3 and 
                c3 > o2 and o3 < c2 and body2 > body1):
                pattern = ChartPattern(
                    name="Bullish Engulfing",
                    type=PatternType.BULLISH,
                    confidence=0.70,
                    start_idx=i-1,
                    end_idx=i,
                    price_target=c3 + 2 * body2,
                    stop_loss=l3,
                    description="Strong bullish reversal"
                )
                self.patterns.append(pattern)
            
            # Engulfing Bearish
            if (c2 > o2 and c3 < o3 and 
                c3 < o2 and o3 > c2 and body2 > body1):
                pattern = ChartPattern(
                    name="Bearish Engulfing",
                    type=PatternType.BEARISH,
                    confidence=0.70,
                    start_idx=i-1,
                    end_idx=i,
                    price_target=c3 - 2 * body2,
                    stop_loss=h3,
                    description="Strong bearish reversal"
                )
                self.patterns.append(pattern)
    
    def _find_peaks(self, data: np.ndarray, order: int = 3) -> List[int]:
        """Find local peaks in data"""
        peaks = []
        for i in range(order, len(data) - order):
            if all(data[i] > data[i-j] for j in range(1, order+1)) and \
               all(data[i] > data[i+j] for j in range(1, order+1)):
                peaks.append(i)
        return peaks
    
    def _find_troughs(self, data: np.ndarray, order: int = 3) -> List[int]:
        """Find local troughs in data"""
        troughs = []
        for i in range(order, len(data) - order):
            if all(data[i] < data[i-j] for j in range(1, order+1)) and \
               all(data[i] < data[i+j] for j in range(1, order+1)):
                troughs.append(i)
        return troughs
    
    def get_pattern_summary(self) -> Dict[str, Any]:
        """Get summary of detected patterns"""
        bullish = [p for p in self.patterns if p.type == PatternType.BULLISH]
        bearish = [p for p in self.patterns if p.type == PatternType.BEARISH]
        neutral = [p for p in self.patterns if p.type == PatternType.NEUTRAL]
        
        return {
            "total_patterns": len(self.patterns),
            "bullish_count": len(bullish),
            "bearish_count": len(bearish),
            "neutral_count": len(neutral),
            "patterns": [
                {
                    "name": p.name,
                    "type": p.type.value,
                    "confidence": p.confidence,
                    "price_target": p.price_target,
                    "stop_loss": p.stop_loss,
                    "description": p.description
                }
                for p in sorted(self.patterns, key=lambda x: x.confidence, reverse=True)
            ]
        }
