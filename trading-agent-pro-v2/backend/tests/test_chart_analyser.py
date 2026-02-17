"""
Kimi Agent — Unit Tests for Chart Analyser
"""
import numpy as np
import pandas as pd
import pytest

from app.services.charts.analyser import (
    ChartAnalyser,
    DetectedPattern,
    PatternType,
    PatternBias,
)


@pytest.fixture
def analyser():
    return ChartAnalyser(swing_lookback=5, min_pattern_bars=10)


@pytest.fixture
def uptrend_df():
    """OHLCV data with a clear uptrend."""
    n = 100
    close = np.linspace(100, 150, n) + np.random.randn(n) * 0.5
    high = close + 1
    low = close - 1
    open_ = close - 0.2
    volume = np.ones(n) * 1000
    return pd.DataFrame({
        "open": open_, "high": high, "low": low,
        "close": close, "volume": volume,
    })


@pytest.fixture
def double_top_df():
    """Synthetic double-top pattern: up → peak → dip → peak → down."""
    np.random.seed(99)
    seg1 = np.linspace(100, 120, 30)  # Up to first peak
    seg2 = np.linspace(120, 110, 15)  # Trough
    seg3 = np.linspace(110, 120, 15)  # Second peak
    seg4 = np.linspace(120, 105, 20)  # Breakdown
    close = np.concatenate([seg1, seg2, seg3, seg4])
    high = close + 0.5
    low = close - 0.5
    open_ = close + np.random.randn(len(close)) * 0.1
    volume = np.ones(len(close)) * 1000
    return pd.DataFrame({
        "open": open_, "high": high, "low": low,
        "close": close, "volume": volume,
    })


class TestChartAnalyser:
    def test_analyse_returns_list(self, analyser, uptrend_df):
        patterns = analyser.analyse(uptrend_df)
        assert isinstance(patterns, list)

    def test_detected_pattern_structure(self, analyser, double_top_df):
        patterns = analyser.analyse(double_top_df)
        for p in patterns:
            assert isinstance(p, DetectedPattern)
            assert isinstance(p.pattern_type, PatternType)
            assert isinstance(p.bias, PatternBias)
            assert 0.0 <= p.confidence <= 1.0

    def test_short_df_returns_empty(self, analyser):
        short = pd.DataFrame({
            "open": [1, 2], "high": [2, 3], "low": [0, 1],
            "close": [1.5, 2.5], "volume": [100, 100],
        })
        patterns = analyser.analyse(short)
        assert patterns == []

    def test_none_returns_empty(self, analyser):
        assert analyser.analyse(None) == []

    def test_summary(self, analyser, uptrend_df):
        patterns = analyser.analyse(uptrend_df)
        summary = analyser.get_summary(patterns)
        assert "count" in summary
        assert "dominant_bias" in summary
        assert summary["dominant_bias"] in ["bullish", "bearish", "neutral"]

    def test_channel_detection(self, analyser, uptrend_df):
        patterns = analyser.analyse(uptrend_df)
        channel_patterns = [p for p in patterns if "channel" in p.pattern_type.value]
        # Uptrend should ideally detect ascending channel
        if channel_patterns:
            assert channel_patterns[0].bias == PatternBias.BULLISH
