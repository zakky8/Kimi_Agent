"""
Technical Analysis Module
Indicators, patterns, and signal generation
"""

from .technical_indicators import TechnicalIndicators
from .pattern_recognition import PatternRecognition
from .market_regime import MarketRegimeDetector

__all__ = [
    "TechnicalIndicators",
    "PatternRecognition",
    "MarketRegimeDetector"
]
