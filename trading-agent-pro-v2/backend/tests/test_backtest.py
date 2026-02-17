"""
Kimi Agent — Unit Tests for Backtest Engine
"""
import numpy as np
import pandas as pd
import pytest

from app.services.backtest.engine import BacktestEngine, BacktestResult


@pytest.fixture
def trending_ohlcv():
    """200-bar uptrending OHLCV data."""
    np.random.seed(42)
    n = 200
    trend = np.linspace(100, 130, n)
    noise = np.random.randn(n) * 0.5
    close = trend + noise
    high = close + np.abs(np.random.randn(n)) * 0.8
    low = close - np.abs(np.random.randn(n)) * 0.8
    open_ = close + np.random.randn(n) * 0.3
    volume = np.random.randint(500, 5000, size=n).astype(float)
    return pd.DataFrame({
        "open": open_, "high": high, "low": low,
        "close": close, "volume": volume,
    })


@pytest.fixture
def engine():
    return BacktestEngine(
        initial_balance=10000.0,
        risk_pct=1.0,
        sl_atr_mult=1.5,
        tp_rr=2.0,
        commission_pct=0.1,
        slippage_pct=0.05,
    )


class TestBacktestEngine:
    def test_run_returns_result(self, engine, trending_ohlcv):
        result = engine.run(trending_ohlcv, symbol="TEST", timeframe="H1")
        assert isinstance(result, BacktestResult)

    def test_result_fields(self, engine, trending_ohlcv):
        result = engine.run(trending_ohlcv)
        assert result.total_bars == len(trending_ohlcv)
        assert result.symbol == "BTC/USDT"
        assert result.timeframe == "H1"
        assert 0.0 <= result.win_rate <= 1.0
        assert result.duration_s >= 0

    def test_equity_curve_length(self, engine, trending_ohlcv):
        result = engine.run(trending_ohlcv)
        # Equity curve should have approximately (n - 100) entries
        assert len(result.equity_curve) > 0

    def test_short_data_returns_empty_result(self, engine):
        short = pd.DataFrame({
            "open": [1, 2, 3], "high": [2, 3, 4], "low": [0, 1, 2],
            "close": [1.5, 2.5, 3.5], "volume": [100, 100, 100],
        })
        result = engine.run(short)
        assert result.total_trades == 0
        assert result.total_bars == 0

    def test_none_data(self, engine):
        result = engine.run(None)
        assert result.total_trades == 0

    def test_trades_have_direction(self, engine, trending_ohlcv):
        result = engine.run(trending_ohlcv)
        for trade in result.trades:
            assert trade.direction in ["LONG", "SHORT"]
            assert trade.exit_reason in ["SL", "TP"]

    def test_commissions_calculated(self, engine, trending_ohlcv):
        result = engine.run(trending_ohlcv)
        if result.total_trades > 0:
            assert result.total_commissions > 0
