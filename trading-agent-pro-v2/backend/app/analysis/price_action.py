"""
Price Action Analysis Module
Identifies candlestick patterns, market structure, and price action signals
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CandlePattern(Enum):
    DOJI = "doji"
    HAMMER = "hammer"
    SHOOTING_STAR = "shooting_star"
    ENGULFING_BULLISH = "engulfing_bullish"
    ENGULFING_BEARISH = "engulfing_bearish"
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"
    HARAMI_BULLISH = "harami_bullish"
    HARAMI_BEARISH = "harami_bearish"
    PIERCING_LINE = "piercing_line"
    DARK_CLOUD_COVER = "dark_cloud_cover"
    THREE_WHITE_SOLDIERS = "three_white_soldiers"
    THREE_BLACK_CROWS = "three_black_crows"


class MarketStructure(Enum):
    UPTREND = "uptrend"
    DOWNTREND = "downtrend"
    RANGING = "ranging"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"


@dataclass
class CandlestickPattern:
    """Detected candlestick pattern"""
    pattern: CandlePattern
    timestamp: datetime
    confidence: float
    direction: str  # "bullish" or "bearish"
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]


@dataclass
class SwingPoint:
    """Swing high or low"""
    point_type: str  # "high" or "low"
    price: float
    timestamp: datetime
    index: int


class PriceActionAnalyzer:
    """
    Advanced Price Action Analysis
    - Candlestick pattern recognition
    - Market structure identification
    - Swing point detection
    - Trend analysis
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.patterns: List[CandlestickPattern] = []
        self.swing_highs: List[SwingPoint] = []
        self.swing_lows: List[SwingPoint] = []
        self.market_structure: MarketStructure = MarketStructure.RANGING
        
    def analyze_all(self) -> Dict[str, Any]:
        """Run complete price action analysis"""
        self.detect_candlestick_patterns()
        self.find_swing_points()
        self.identify_market_structure()
        
        return {
            "patterns": [self._pattern_to_dict(p) for p in self.patterns[-10:]],
            "swing_highs": len(self.swing_highs),
            "swing_lows": len(self.swing_lows),
            "market_structure": self.market_structure.value,
            "trend_strength": self._calculate_trend_strength(),
            "key_levels": self._get_key_levels()
        }
    
    def detect_candlestick_patterns(self) -> List[CandlestickPattern]:
        """Detect all candlestick patterns"""
        if len(self.df) < 5:
            return []
        
        opens = self.df['open'].values
        highs = self.df['high'].values
        lows = self.df['low'].values
        closes = self.df['close'].values
        volumes = self.df.get('volume', pd.Series([0] * len(self.df))).values
        
        for i in range(2, len(self.df) - 2):
            try:
                # Single candle patterns
                self._check_doji(i, opens, highs, lows, closes)
                self._check_hammer(i, opens, highs, lows, closes)
                self._check_shooting_star(i, opens, highs, lows, closes)
                
                # Two candle patterns
                self._check_engulfing(i, opens, highs, lows, closes)
                self._check_harami(i, opens, highs, lows, closes)
                self._check_piercing_dark_cloud(i, opens, highs, lows, closes)
                
                # Three candle patterns
                self._check_morning_star(i, opens, highs, lows, closes)
                self._check_evening_star(i, opens, highs, lows, closes)
                self._check_three_soldiers_crows(i, opens, highs, lows, closes)
                
            except Exception as e:
                continue
        
        return self.patterns
    
    def _check_doji(self, i: int, opens, highs, lows, closes):
        """Check for Doji pattern"""
        body = abs(closes[i] - opens[i])
        range_total = highs[i] - lows[i]
        
        if range_total > 0 and body / range_total < 0.1:
            pattern = CandlestickPattern(
                pattern=CandlePattern.DOJI,
                timestamp=self.df.index[i],
                confidence=0.6,
                direction="neutral",
                entry_price=None,
                stop_loss=None,
                take_profit=None
            )
            self.patterns.append(pattern)
    
    def _check_hammer(self, i: int, opens, highs, lows, closes):
        """Check for Hammer pattern"""
        body = abs(closes[i] - opens[i])
        upper_shadow = highs[i] - max(opens[i], closes[i])
        lower_shadow = min(opens[i], closes[i]) - lows[i]
        
        # Hammer: small body, long lower shadow, little/no upper shadow
        if body > 0 and lower_shadow > 2 * body and upper_shadow < body * 0.5:
            if closes[i] > opens[i]:  # Bullish hammer
                pattern = CandlestickPattern(
                    pattern=CandlePattern.HAMMER,
                    timestamp=self.df.index[i],
                    confidence=0.75,
                    direction="bullish",
                    entry_price=closes[i],
                    stop_loss=lows[i] - (body * 0.5),
                    take_profit=closes[i] + (body * 3)
                )
                self.patterns.append(pattern)
    
    def _check_shooting_star(self, i: int, opens, highs, lows, closes):
        """Check for Shooting Star pattern"""
        body = abs(closes[i] - opens[i])
        upper_shadow = highs[i] - max(opens[i], closes[i])
        lower_shadow = min(opens[i], closes[i]) - lows[i]
        
        # Shooting star: small body, long upper shadow, little/no lower shadow
        if body > 0 and upper_shadow > 2 * body and lower_shadow < body * 0.5:
            if closes[i] < opens[i]:  # Bearish shooting star
                pattern = CandlestickPattern(
                    pattern=CandlePattern.SHOOTING_STAR,
                    timestamp=self.df.index[i],
                    confidence=0.75,
                    direction="bearish",
                    entry_price=closes[i],
                    stop_loss=highs[i] + (body * 0.5),
                    take_profit=closes[i] - (body * 3)
                )
                self.patterns.append(pattern)
    
    def _check_engulfing(self, i: int, opens, highs, lows, closes):
        """Check for Engulfing patterns"""
        prev_body = abs(closes[i-1] - opens[i-1])
        curr_body = abs(closes[i] - opens[i])
        
        # Bullish engulfing
        if (closes[i-1] < opens[i-1] and  # Previous bearish
            closes[i] > opens[i] and       # Current bullish
            opens[i] < closes[i-1] and     # Open below previous close
            closes[i] > opens[i-1] and     # Close above previous open
            curr_body > prev_body * 1.2):  # Current body larger
            
            pattern = CandlestickPattern(
                pattern=CandlePattern.ENGULFING_BULLISH,
                timestamp=self.df.index[i],
                confidence=0.8,
                direction="bullish",
                entry_price=closes[i],
                stop_loss=lows[i],
                take_profit=closes[i] + (curr_body * 2)
            )
            self.patterns.append(pattern)
        
        # Bearish engulfing
        elif (closes[i-1] > opens[i-1] and  # Previous bullish
              closes[i] < opens[i] and       # Current bearish
              opens[i] > closes[i-1] and     # Open above previous close
              closes[i] < opens[i-1] and     # Close below previous open
              curr_body > prev_body * 1.2):
            
            pattern = CandlestickPattern(
                pattern=CandlePattern.ENGULFING_BEARISH,
                timestamp=self.df.index[i],
                confidence=0.8,
                direction="bearish",
                entry_price=closes[i],
                stop_loss=highs[i],
                take_profit=closes[i] - (curr_body * 2)
            )
            self.patterns.append(pattern)
    
    def _check_harami(self, i: int, opens, highs, lows, closes):
        """Check for Harami patterns"""
        prev_body = abs(closes[i-1] - opens[i-1])
        curr_body = abs(closes[i] - opens[i])
        
        # Bullish harami
        if (closes[i-1] < opens[i-1] and  # Previous bearish (large)
            closes[i] > opens[i] and       # Current bullish (small)
            opens[i] > closes[i-1] and     # Current open inside previous body
            closes[i] < opens[i-1] and
            curr_body < prev_body * 0.5):
            
            pattern = CandlestickPattern(
                pattern=CandlePattern.HARAMI_BULLISH,
                timestamp=self.df.index[i],
                confidence=0.7,
                direction="bullish",
                entry_price=closes[i],
                stop_loss=lows[i],
                take_profit=closes[i] + (prev_body * 1.5)
            )
            self.patterns.append(pattern)
        
        # Bearish harami
        elif (closes[i-1] > opens[i-1] and  # Previous bullish (large)
              closes[i] < opens[i] and       # Current bearish (small)
              opens[i] < closes[i-1] and     # Current open inside previous body
              closes[i] > opens[i-1] and
              curr_body < prev_body * 0.5):
            
            pattern = CandlestickPattern(
                pattern=CandlePattern.HARAMI_BEARISH,
                timestamp=self.df.index[i],
                confidence=0.7,
                direction="bearish",
                entry_price=closes[i],
                stop_loss=highs[i],
                take_profit=closes[i] - (prev_body * 1.5)
            )
            self.patterns.append(pattern)
    
    def _check_piercing_dark_cloud(self, i: int, opens, highs, lows, closes):
        """Check for Piercing Line and Dark Cloud Cover"""
        prev_body = abs(closes[i-1] - opens[i-1])
        
        # Piercing line (bullish)
        if (closes[i-1] < opens[i-1] and  # Previous bearish
            closes[i] > opens[i] and       # Current bullish
            opens[i] < lows[i-1] and       # Gap down
            closes[i] > (opens[i-1] + closes[i-1]) / 2 and  # Close above midpoint
            closes[i] < opens[i-1]):
            
            pattern = CandlestickPattern(
                pattern=CandlePattern.PIERCING_LINE,
                timestamp=self.df.index[i],
                confidence=0.75,
                direction="bullish",
                entry_price=closes[i],
                stop_loss=lows[i],
                take_profit=closes[i] + (prev_body * 2)
            )
            self.patterns.append(pattern)
        
        # Dark cloud cover (bearish)
        elif (closes[i-1] > opens[i-1] and  # Previous bullish
              closes[i] < opens[i] and       # Current bearish
              opens[i] > highs[i-1] and      # Gap up
              closes[i] < (opens[i-1] + closes[i-1]) / 2 and  # Close below midpoint
              closes[i] > opens[i-1]):
            
            pattern = CandlestickPattern(
                pattern=CandlePattern.DARK_CLOUD_COVER,
                timestamp=self.df.index[i],
                confidence=0.75,
                direction="bearish",
                entry_price=closes[i],
                stop_loss=highs[i],
                take_profit=closes[i] - (prev_body * 2)
            )
            self.patterns.append(pattern)
    
    def _check_morning_star(self, i: int, opens, highs, lows, closes):
        """Check for Morning Star pattern"""
        if i < 2:
            return
        
        prev2_body = abs(closes[i-2] - opens[i-2])
        prev_body = abs(closes[i-1] - opens[i-1])
        curr_body = abs(closes[i] - opens[i])
        
        # Morning star: bearish, small body (doji), bullish
        if (closes[i-2] < opens[i-2] and  # First bearish
            abs(closes[i-1] - opens[i-1]) < prev2_body * 0.3 and  # Small middle
            closes[i] > opens[i] and       # Last bullish
            closes[i] > (opens[i-2] + closes[i-2]) / 2):  # Close above midpoint of first
            
            pattern = CandlestickPattern(
                pattern=CandlePattern.MORNING_STAR,
                timestamp=self.df.index[i],
                confidence=0.85,
                direction="bullish",
                entry_price=closes[i],
                stop_loss=lows[i-1],
                take_profit=closes[i] + (prev2_body * 3)
            )
            self.patterns.append(pattern)
    
    def _check_evening_star(self, i: int, opens, highs, lows, closes):
        """Check for Evening Star pattern"""
        if i < 2:
            return
        
        prev2_body = abs(closes[i-2] - opens[i-2])
        
        # Evening star: bullish, small body (doji), bearish
        if (closes[i-2] > opens[i-2] and  # First bullish
            abs(closes[i-1] - opens[i-1]) < prev2_body * 0.3 and  # Small middle
            closes[i] < opens[i] and       # Last bearish
            closes[i] < (opens[i-2] + closes[i-2]) / 2):  # Close below midpoint of first
            
            pattern = CandlestickPattern(
                pattern=CandlePattern.EVENING_STAR,
                timestamp=self.df.index[i],
                confidence=0.85,
                direction="bearish",
                entry_price=closes[i],
                stop_loss=highs[i-1],
                take_profit=closes[i] - (prev2_body * 3)
            )
            self.patterns.append(pattern)
    
    def _check_three_soldiers_crows(self, i: int, opens, highs, lows, closes):
        """Check for Three White Soldiers and Three Black Crows"""
        if i < 2:
            return
        
        # Three white soldiers (bullish)
        if (closes[i-2] > opens[i-2] and
            closes[i-1] > opens[i-1] and
            closes[i] > opens[i] and
            closes[i-2] < closes[i-1] < closes[i] and  # Progressive higher closes
            opens[i-1] > opens[i-2] and opens[i-1] < closes[i-2] and  # Inside previous
            opens[i] > opens[i-1] and opens[i] < closes[i-1]):
            
            pattern = CandlestickPattern(
                pattern=CandlePattern.THREE_WHITE_SOLDIERS,
                timestamp=self.df.index[i],
                confidence=0.85,
                direction="bullish",
                entry_price=closes[i],
                stop_loss=lows[i-2],
                take_profit=closes[i] + ((closes[i] - opens[i-2]) * 2)
            )
            self.patterns.append(pattern)
        
        # Three black crows (bearish)
        elif (closes[i-2] < opens[i-2] and
              closes[i-1] < opens[i-1] and
              closes[i] < opens[i] and
              closes[i-2] > closes[i-1] > closes[i] and  # Progressive lower closes
              opens[i-1] < opens[i-2] and opens[i-1] > closes[i-2] and
              opens[i] < opens[i-1] and opens[i] > closes[i-1]):
            
            pattern = CandlestickPattern(
                pattern=CandlePattern.THREE_BLACK_CROWS,
                timestamp=self.df.index[i],
                confidence=0.85,
                direction="bearish",
                entry_price=closes[i],
                stop_loss=highs[i-2],
                take_profit=closes[i] - ((opens[i-2] - closes[i]) * 2)
            )
            self.patterns.append(pattern)
    
    def find_swing_points(self, lookback: int = 50, order: int = 3) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """
        Find swing highs and lows
        
        Args:
            lookback: Number of candles to analyze
            order: Number of candles on each side for confirmation
        """
        if len(self.df) < lookback + order * 2:
            return [], []
        
        recent = self.df.tail(lookback + order * 2)
        highs = recent['high'].values
        lows = recent['low'].values
        
        self.swing_highs = []
        self.swing_lows = []
        
        for i in range(order, len(recent) - order):
            idx = len(self.df) - len(recent) + i
            
            # Check for swing high
            is_swing_high = all(highs[i] > highs[i-j] for j in range(1, order+1)) and \
                           all(highs[i] > highs[i+j] for j in range(1, order+1))
            
            if is_swing_high:
                self.swing_highs.append(SwingPoint(
                    point_type="high",
                    price=highs[i],
                    timestamp=recent.index[i],
                    index=idx
                ))
            
            # Check for swing low
            is_swing_low = all(lows[i] < lows[i-j] for j in range(1, order+1)) and \
                          all(lows[i] < lows[i+j] for j in range(1, order+1))
            
            if is_swing_low:
                self.swing_lows.append(SwingPoint(
                    point_type="low",
                    price=lows[i],
                    timestamp=recent.index[i],
                    index=idx
                ))
        
        return self.swing_highs, self.swing_lows
    
    def identify_market_structure(self) -> MarketStructure:
        """Identify current market structure"""
        if len(self.df) < 20:
            self.market_structure = MarketStructure.RANGING
            return self.market_structure
        
        # Calculate trend using swing points
        highs = [sp.price for sp in self.swing_highs[-5:]]
        lows = [sp.price for sp in self.swing_lows[-5:]]
        
        if len(highs) >= 3 and len(lows) >= 3:
            # Check for higher highs and higher lows (uptrend)
            higher_highs = all(highs[i] > highs[i-1] for i in range(1, len(highs)))
            higher_lows = all(lows[i] > lows[i-1] for i in range(1, len(lows)))
            
            if higher_highs and higher_lows:
                self.market_structure = MarketStructure.UPTREND
                return self.market_structure
            
            # Check for lower highs and lower lows (downtrend)
            lower_highs = all(highs[i] < highs[i-1] for i in range(1, len(highs)))
            lower_lows = all(lows[i] < lows[i-1] for i in range(1, len(lows)))
            
            if lower_highs and lower_lows:
                self.market_structure = MarketStructure.DOWNTREND
                return self.market_structure
        
        # Check for ranging market using ATR
        atr = self._calculate_atr(14)
        recent_range = (self.df['high'].tail(20).max() - self.df['low'].tail(20).min()) / self.df['close'].iloc[-1]
        
        if recent_range < atr * 3 / self.df['close'].iloc[-1]:
            self.market_structure = MarketStructure.RANGING
        else:
            self.market_structure = MarketStructure.BREAKOUT
        
        return self.market_structure
    
    def _calculate_atr(self, period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(self.df) < period:
            return 0.0
        
        highs = self.df['high']
        lows = self.df['low']
        closes = self.df['close']
        
        tr1 = highs - lows
        tr2 = abs(highs - closes.shift(1))
        tr3 = abs(lows - closes.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]
        
        return atr
    
    def _calculate_trend_strength(self) -> float:
        """Calculate trend strength (0-1)"""
        if len(self.df) < 20:
            return 0.5
        
        # Use ADX-like calculation
        plus_dm = self.df['high'].diff()
        minus_dm = -self.df['low'].diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        atr = self._calculate_atr(14)
        
        if atr == 0:
            return 0.5
        
        plus_di = 100 * plus_dm.rolling(14).mean() / atr
        minus_di = 100 * minus_dm.rolling(14).mean() / atr
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(14).mean().iloc[-1] if len(dx) >= 14 else 25
        
        # Normalize to 0-1
        return min(adx / 50, 1.0)
    
    def _get_key_levels(self) -> Dict[str, List[float]]:
        """Get key support and resistance levels"""
        return {
            "swing_highs": [sp.price for sp in self.swing_highs[-5:]],
            "swing_lows": [sp.price for sp in self.swing_lows[-5:]]
        }
    
    def _pattern_to_dict(self, pattern: CandlestickPattern) -> Dict[str, Any]:
        """Convert pattern to dictionary"""
        return {
            "pattern": pattern.pattern.value,
            "timestamp": pattern.timestamp.isoformat() if hasattr(pattern.timestamp, 'isoformat') else str(pattern.timestamp),
            "confidence": pattern.confidence,
            "direction": pattern.direction,
            "entry_price": pattern.entry_price,
            "stop_loss": pattern.stop_loss,
            "take_profit": pattern.take_profit
        }
    
    def get_recent_patterns(self, n: int = 5) -> List[CandlestickPattern]:
        """Get N most recent patterns"""
        return self.patterns[-n:] if self.patterns else []
    
    def get_bullish_patterns(self) -> List[CandlestickPattern]:
        """Get all bullish patterns"""
        return [p for p in self.patterns if p.direction == "bullish"]
    
    def get_bearish_patterns(self) -> List[CandlestickPattern]:
        """Get all bearish patterns"""
        return [p for p in self.patterns if p.direction == "bearish"]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get complete price action summary"""
        return {
            "total_patterns": len(self.patterns),
            "bullish_patterns": len(self.get_bullish_patterns()),
            "bearish_patterns": len(self.get_bearish_patterns()),
            "recent_patterns": [self._pattern_to_dict(p) for p in self.get_recent_patterns(5)],
            "market_structure": self.market_structure.value,
            "trend_strength": self._calculate_trend_strength(),
            "swing_highs_count": len(self.swing_highs),
            "swing_lows_count": len(self.swing_lows),
            "key_levels": self._get_key_levels()
        }
