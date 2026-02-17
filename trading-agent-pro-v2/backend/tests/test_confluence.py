"""
Kimi Agent — Unit Tests for Confluence Engine
"""
import numpy as np
import pandas as pd
import pytest

from app.services.analysis.confluence import ConfluenceEngine


@pytest.fixture
def sample_ohlcv():
    np.random.seed(42)
    n = 200
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n)) * 0.5
    low = close - np.abs(np.random.randn(n)) * 0.5
    open_ = close + np.random.randn(n) * 0.2
    volume = np.random.randint(100, 10000, size=n).astype(float)
    return pd.DataFrame({
        "open": open_, "high": high, "low": low,
        "close": close, "volume": volume,
    })


@pytest.fixture
def engine():
    return ConfluenceEngine()


class TestConfluenceEngine:
    def test_score_in_range(self, engine, sample_ohlcv):
        candles = {"H1": sample_ohlcv}
        result = engine.score(candles)
        assert -1.0 <= result["confluence_score"] <= 1.0

    def test_returns_dict(self, engine, sample_ohlcv):
        candles = {"H1": sample_ohlcv}
        result = engine.score(candles)
        assert isinstance(result, dict)
        assert "confluence_score" in result
        assert "signal" in result

    def test_multi_timeframe(self, engine, sample_ohlcv):
        candles = {
            "D1": sample_ohlcv,
            "H4": sample_ohlcv,
            "H1": sample_ohlcv,
        }
        result = engine.score(candles)
        assert "confluence_score" in result

    def test_empty_candles_returns_neutral(self, engine):
        result = engine.score({})
        assert result["confluence_score"] == 0.0

    def test_signal_labels(self, engine, sample_ohlcv):
        candles = {"H1": sample_ohlcv}
        result = engine.score(candles)
        assert result["signal"] in ["STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"]
