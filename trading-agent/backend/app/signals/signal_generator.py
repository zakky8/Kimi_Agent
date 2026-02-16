"""
Signal Generator Module
Generates trading signals from multiple sources
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import logging

from ..analysis.technical_indicators import TechnicalIndicators, SignalType
from ..analysis.pattern_recognition import PatternRecognition, PatternType
from ..analysis.market_regime import MarketRegimeDetector, MarketRegime

logger = logging.getLogger(__name__)


class SignalDirection(Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class SignalStrength(Enum):
    STRONG = "strong"      # 80-100%
    MODERATE = "moderate"  # 60-80%
    WEAK = "weak"          # 40-60%
    NONE = "none"          # <40%


@dataclass
class TradingSignal:
    """Complete trading signal"""
    symbol: str
    direction: SignalDirection
    strength: SignalStrength
    confidence: float  # 0.0 to 1.0
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    risk_reward: Optional[float]
    timeframe: str
    strategy: str
    sources: List[str]
    reasons: List[str]
    timestamp: datetime
    expiry: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SignalGenerator:
    """
    Generates institutional-grade trading signals
    Combines technical, fundamental, and sentiment analysis
    """
    
    def __init__(self):
        self.signals: List[TradingSignal] = []
        self.signal_history: List[TradingSignal] = []
        
    async def generate_signal(
        self,
        symbol: str,
        df: pd.DataFrame,
        sentiment_data: Optional[Dict] = None,
        market_data: Optional[Dict] = None
    ) -> Optional[TradingSignal]:
        """
        Generate comprehensive trading signal
        
        Args:
            symbol: Trading pair symbol
            df: OHLCV dataframe
            sentiment_data: Social sentiment data
            market_data: Market context data
        """
        if len(df) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return None
        
        # Technical Analysis
        tech_indicators = TechnicalIndicators(df)
        tech_indicators.add_all_indicators()
        tech_signals = tech_indicators.generate_signals()
        
        # Pattern Recognition
        patterns = PatternRecognition(df)
        patterns.detect_all_patterns()
        pattern_data = patterns.get_pattern_summary()
        
        # Market Regime
        regime_detector = MarketRegimeDetector(df)
        regime = regime_detector.detect_regime()
        
        # Combine signals
        direction, confidence, reasons = self._combine_signals(
            tech_signals, pattern_data, regime, sentiment_data
        )
        
        if confidence < 0.6:
            return None
        
        # Calculate entry, stop, and target
        latest = df.iloc[-1]
        entry = latest["close"]
        
        # ATR-based stops
        atr = latest.get("atr_14", entry * 0.01)
        
        if direction == SignalDirection.LONG:
            stop = entry - 2 * atr
            target = entry + 4 * atr  # 1:2 RR
        elif direction == SignalDirection.SHORT:
            stop = entry + 2 * atr
            target = entry - 4 * atr
        else:
            stop = None
            target = None
        
        # Calculate risk-reward
        if stop and target and entry:
            if direction == SignalDirection.LONG:
                rr = (target - entry) / (entry - stop)
            else:
                rr = (entry - target) / (stop - entry)
        else:
            rr = None
        
        # Determine strength
        strength = self._calculate_strength(confidence)
        
        # Build sources list
        sources = ["technical"]
        if sentiment_data:
            sources.append("sentiment")
        if pattern_data.get("patterns"):
            sources.append("pattern")
        
        signal = TradingSignal(
            symbol=symbol,
            direction=direction,
            strength=strength,
            confidence=round(confidence, 3),
            entry_price=round(entry, 5) if entry else None,
            stop_loss=round(stop, 5) if stop else None,
            take_profit=round(target, 5) if target else None,
            risk_reward=round(rr, 2) if rr else None,
            timeframe="1h",
            strategy=self._determine_strategy(regime),
            sources=sources,
            reasons=reasons,
            timestamp=datetime.now(),
            expiry=datetime.now() + pd.Timedelta(hours=24),
            metadata={
                "regime": regime.regime.value,
                "regime_confidence": regime.confidence,
                "patterns": pattern_data,
                "indicators": tech_indicators.get_summary()
            }
        )
        
        self.signals.append(signal)
        self.signal_history.append(signal)
        
        return signal
    
    def _combine_signals(
        self,
        tech_signals: List,
        pattern_data: Dict,
        regime: Any,
        sentiment_data: Optional[Dict]
    ) -> Tuple[SignalDirection, float, List[str]]:
        """Combine multiple signal sources"""
        
        buy_score = 0
        sell_score = 0
        reasons = []
        
        # Technical signals
        for signal in tech_signals:
            if signal.signal == SignalType.BUY:
                buy_score += signal.strength
                reasons.append(f"{signal.indicator}: {signal.description}")
            elif signal.signal == SignalType.SELL:
                sell_score += signal.strength
                reasons.append(f"{signal.indicator}: {signal.description}")
        
        # Pattern signals
        for pattern in pattern_data.get("patterns", []):
            if pattern["type"] == "bullish":
                buy_score += pattern["confidence"]
                reasons.append(f"Pattern: {pattern['name']}")
            elif pattern["type"] == "bearish":
                sell_score += pattern["confidence"]
                reasons.append(f"Pattern: {pattern['name']}")
        
        # Regime filter
        if regime.regime == MarketRegime.TRENDING_UP:
            buy_score *= 1.2
        elif regime.regime == MarketRegime.TRENDING_DOWN:
            sell_score *= 1.2
        elif regime.regime == MarketRegime.RANGE_BOUND:
            # Mean reversion - reduce trend signals
            buy_score *= 0.8
            sell_score *= 0.8
        
        # Sentiment
        if sentiment_data:
            sentiment_score = sentiment_data.get("sentiment_score", 0)
            if sentiment_score > 0.3:
                buy_score += sentiment_score * 0.5
                reasons.append(f"Social sentiment: {sentiment_data.get('sentiment_label', 'neutral')}")
            elif sentiment_score < -0.3:
                sell_score += abs(sentiment_score) * 0.5
                reasons.append(f"Social sentiment: {sentiment_data.get('sentiment_label', 'neutral')}")
        
        # Determine direction
        total_score = buy_score + sell_score
        if total_score == 0:
            return SignalDirection.NEUTRAL, 0, []
        
        if buy_score > sell_score * 1.5:
            confidence = buy_score / total_score
            return SignalDirection.LONG, confidence, reasons
        elif sell_score > buy_score * 1.5:
            confidence = sell_score / total_score
            return SignalDirection.SHORT, confidence, reasons
        else:
            return SignalDirection.NEUTRAL, 0, []
    
    def _calculate_strength(self, confidence: float) -> SignalStrength:
        """Convert confidence to signal strength"""
        if confidence >= 0.8:
            return SignalStrength.STRONG
        elif confidence >= 0.6:
            return SignalStrength.MODERATE
        elif confidence >= 0.4:
            return SignalStrength.WEAK
        else:
            return SignalStrength.NONE
    
    def _determine_strategy(self, regime: Any) -> str:
        """Determine trading strategy based on regime"""
        strategy_map = {
            MarketRegime.TRENDING_UP: "Trend Following (Long)",
            MarketRegime.TRENDING_DOWN: "Trend Following (Short)",
            MarketRegime.RANGE_BOUND: "Mean Reversion",
            MarketRegime.HIGH_VOLATILITY: "Volatility Breakout",
            MarketRegime.LOW_VOLATILITY: "Range Compression"
        }
        return strategy_map.get(regime.regime, "Multi-Strategy")
    
    def get_active_signals(self) -> List[TradingSignal]:
        """Get non-expired signals"""
        now = datetime.now()
        return [s for s in self.signals if s.expiry and s.expiry > now]
    
    def get_signal_summary(self) -> Dict[str, Any]:
        """Get summary of all signals"""
        active = self.get_active_signals()
        
        long_signals = [s for s in active if s.direction == SignalDirection.LONG]
        short_signals = [s for s in active if s.direction == SignalDirection.SHORT]
        
        return {
            "total_active": len(active),
            "long_signals": len(long_signals),
            "short_signals": len(short_signals),
            "avg_confidence": np.mean([s.confidence for s in active]) if active else 0,
            "strong_signals": len([s for s in active if s.strength == SignalStrength.STRONG]),
            "signals": [
                {
                    "symbol": s.symbol,
                    "direction": s.direction.value,
                    "strength": s.strength.value,
                    "confidence": s.confidence,
                    "entry": s.entry_price,
                    "stop": s.stop_loss,
                    "target": s.take_profit,
                    "rr": s.risk_reward,
                    "strategy": s.strategy
                }
                for s in sorted(active, key=lambda x: x.confidence, reverse=True)
            ]
        }


# Singleton instance
_signal_generator: Optional[SignalGenerator] = None


def get_signal_generator() -> SignalGenerator:
    """Get or create signal generator singleton"""
    global _signal_generator
    if _signal_generator is None:
        _signal_generator = SignalGenerator()
    return _signal_generator
