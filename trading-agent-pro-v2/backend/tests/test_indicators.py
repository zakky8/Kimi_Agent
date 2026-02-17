"""
Kimi Agent — Unit Tests for Indicator Engine
"""
import numpy as np
import pandas as pd
import pytest

from app.services.analysis.indicators import IndicatorEngine


@pytest.fixture
def sample_ohlcv():
    """Create a synthetic OHLCV DataFrame with 200 bars."""
    np.random.seed(42)
    n = 200
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n)) * 0.5
    low = close - np.abs(np.random.randn(n)) * 0.5
    open_ = close + np.random.randn(n) * 0.2
    volume = np.random.randint(100, 10000, size=n).astype(float)

    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })
    return df


@pytest.fixture
def engine():
    return IndicatorEngine()


class TestIndicatorEngine:
    def test_compute_returns_dict(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_all_values_are_floats(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        for key, value in result.items():
            assert isinstance(value, (int, float)), f"{key} is {type(value)}"

    def test_no_nan_values(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        for key, value in result.items():
            assert not np.isnan(value), f"{key} is NaN"

    def test_rsi_in_range(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        rsi = result.get("rsi_14", None)
        if rsi is not None:
            assert 0.0 <= rsi <= 100.0, f"RSI out of range: {rsi}"

    def test_ema_keys_present(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        for period in [9, 20, 50]:
            assert f"ema_{period}" in result, f"ema_{period} missing"

    def test_bollinger_keys_present(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        for key in ["bb_upper", "bb_middle", "bb_lower"]:
            assert key in result, f"{key} missing"

    def test_macd_keys_present(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        for key in ["macd_line", "macd_signal", "macd_histogram"]:
            assert key in result, f"{key} missing"

    def test_empty_dataframe_returns_empty_dict(self, engine):
        result = engine.compute(pd.DataFrame())
        assert result == {}

    def test_none_returns_empty_dict(self, engine):
        result = engine.compute(None)
        assert result == {}

    def test_short_dataframe_returns_partial(self, engine, sample_ohlcv):
        short = sample_ohlcv.head(10)
        result = engine.compute(short)
        # Should still return something, even if some indicators can't compute
        assert isinstance(result, dict)

    def test_atr_positive(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        atr = result.get("atr_14", 0)
        assert atr >= 0, f"ATR negative: {atr}"

    def test_volume_indicators(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        assert "obv" in result
        assert "volume_sma_ratio" in result

    def test_candlestick_patterns(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        pattern_keys = [k for k in result if k.startswith("pattern_")]
        assert len(pattern_keys) > 0, "No candlestick patterns detected"

    def test_support_resistance(self, engine, sample_ohlcv):
        result = engine.compute(sample_ohlcv)
        assert "pivot_point" in result
        assert "fib_0" in result
