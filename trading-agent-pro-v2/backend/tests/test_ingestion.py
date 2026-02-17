"""
Unit Tests for MarketDataService (Part 1)

Tests candle normalisation, rolling window, health monitor, and Binance
message parsing — all without any live API calls.
"""
import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── We import from the app package ──
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.shared.schemas.candle import NormalisedCandle, Timeframe
from app.shared.schemas.signal import TradingSignal, SignalDirection
from app.services.market_data.ingestion import (
    BinanceConnector,
    DataRouter,
    HealthMonitor,
    MarketDataService,
    RollingWindow,
    ROLLING_WINDOW_SIZE,
)


# ════════════════════════════════════════════════════════
# NormalisedCandle schema tests
# ════════════════════════════════════════════════════════

class TestNormalisedCandle:
    """Test the Pydantic candle schema."""

    def test_valid_candle(self) -> None:
        candle = NormalisedCandle(
            symbol="btc/usdt",
            timeframe="h1",
            timestamp=1700000000,
            open=42000.0,
            high=42500.0,
            low=41800.0,
            close=42300.0,
            volume=1250.0,
            source="binance",
        )
        # Symbol uppercased by validator
        assert candle.symbol == "BTC/USDT"
        assert candle.timeframe == "H1"
        assert candle.close == 42300.0

    def test_invalid_timeframe_rejected(self) -> None:
        with pytest.raises(ValueError, match="Timeframe must be one of"):
            NormalisedCandle(
                symbol="ETH/USDT",
                timeframe="W1",
                timestamp=1700000000,
                open=1.0,
                high=1.0,
                low=1.0,
                close=1.0,
                source="test",
            )

    def test_empty_symbol_rejected(self) -> None:
        with pytest.raises(ValueError, match="non-empty"):
            NormalisedCandle(
                symbol="  ",
                timeframe="H1",
                timestamp=1700000000,
                open=1.0,
                high=1.0,
                low=1.0,
                close=1.0,
                source="test",
            )

    def test_negative_timestamp_rejected(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            NormalisedCandle(
                symbol="EUR/USD",
                timeframe="H1",
                timestamp=-1,
                open=1.0,
                high=1.0,
                low=1.0,
                close=1.0,
                source="test",
            )

    def test_redis_key_format(self) -> None:
        candle = NormalisedCandle(
            symbol="EUR/USD",
            timeframe="M15",
            timestamp=1700000000,
            open=1.08,
            high=1.09,
            low=1.07,
            close=1.085,
            source="oanda",
        )
        assert candle.to_redis_key() == "market:EUR/USD:M15:latest"

    def test_kafka_topic_format(self) -> None:
        candle = NormalisedCandle(
            symbol="BTC/USDT",
            timeframe="H1",
            timestamp=1700000000,
            open=42000.0,
            high=42500.0,
            low=41800.0,
            close=42300.0,
            source="binance",
        )
        assert candle.to_kafka_topic() == "market.data.BTC_USDT"

    def test_db_row_has_all_fields(self) -> None:
        candle = NormalisedCandle(
            symbol="EUR/USD",
            timeframe="D1",
            timestamp=1700000000,
            open=1.08,
            high=1.09,
            low=1.07,
            close=1.085,
            volume=5000.0,
            source="oanda",
        )
        row = candle.to_db_row()
        assert "time" in row
        assert row["symbol"] == "EUR/USD"
        assert row["close"] == 1.085


# ════════════════════════════════════════════════════════
# TradingSignal schema tests
# ════════════════════════════════════════════════════════

class TestTradingSignal:
    """Basic tests for the signal schema."""

    def test_create_signal(self) -> None:
        sig = TradingSignal(
            symbol="EUR/USD",
            timeframe="H4",
            direction=SignalDirection.LONG,
            entry_price=1.08300,
            stop_loss=1.08000,
            take_profit_1=1.08750,
            take_profit_2=1.09050,
            take_profit_3=1.09500,
            overall_confidence=0.72,
        )
        assert sig.direction == SignalDirection.LONG
        assert sig.signal_id  # auto-generated UUID

    def test_risk_reward_ratio(self) -> None:
        sig = TradingSignal(
            symbol="BTC/USDT",
            timeframe="H1",
            direction=SignalDirection.LONG,
            entry_price=42000.0,
            stop_loss=41700.0,
            take_profit_1=42450.0,
            take_profit_2=42750.0,
            take_profit_3=43200.0,
            overall_confidence=0.65,
        )
        # Risk = 300, Reward to TP1 = 450 → R:R = 1.5
        assert sig.risk_reward_ratio() == 1.5


# ════════════════════════════════════════════════════════
# RollingWindow tests
# ════════════════════════════════════════════════════════

class TestRollingWindow:
    """Test the in-memory rolling candle window."""

    def _make_candle(self, ts: int) -> NormalisedCandle:
        return NormalisedCandle(
            symbol="BTC/USDT",
            timeframe="H1",
            timestamp=ts,
            open=42000.0,
            high=42500.0,
            low=41800.0,
            close=42300.0,
            volume=100.0,
            source="test",
        )

    def test_append_and_get(self) -> None:
        rw = RollingWindow(max_size=5)
        for i in range(3):
            rw.append(self._make_candle(1700000000 + i * 3600))
        df = rw.get("BTC/USDT", "H1")
        assert df is not None
        assert len(df) == 3

    def test_eviction_at_capacity(self) -> None:
        rw = RollingWindow(max_size=5)
        for i in range(10):
            rw.append(self._make_candle(1700000000 + i * 3600))
        df = rw.get("BTC/USDT", "H1")
        assert df is not None
        assert len(df) == 5  # only last 5 remain

    def test_separate_symbols(self) -> None:
        rw = RollingWindow(max_size=100)
        rw.append(NormalisedCandle(
            symbol="BTC/USDT", timeframe="H1", timestamp=1700000000,
            open=42000, high=42500, low=41800, close=42300, source="test",
        ))
        rw.append(NormalisedCandle(
            symbol="ETH/USDT", timeframe="H1", timestamp=1700000000,
            open=2200, high=2250, low=2180, close=2230, source="test",
        ))
        assert rw.size("BTC/USDT", "H1") == 1
        assert rw.size("ETH/USDT", "H1") == 1
        assert rw.get("XRP/USDT", "H1") is None

    def test_size_of_empty(self) -> None:
        rw = RollingWindow()
        assert rw.size("NONEXIST", "M1") == 0


# ════════════════════════════════════════════════════════
# HealthMonitor tests
# ════════════════════════════════════════════════════════

class TestHealthMonitor:
    """Test the health monitoring logic."""

    def test_record_and_retrieve(self) -> None:
        hm = HealthMonitor()
        hm.record_tick("BTC/USDT")
        metrics = hm.get_metrics()
        assert "BTC/USDT" in metrics
        assert metrics["BTC/USDT"] < 1.0  # should be nearly 0

    def test_stale_symbol_detection(self) -> None:
        hm = HealthMonitor()
        # Fake a tick that happened 200 seconds ago
        hm._last_tick["OLD/PAIR"] = time.time() - 200
        metrics = hm.get_metrics()
        assert metrics["OLD/PAIR"] > 120  # stale threshold


# ════════════════════════════════════════════════════════
# BinanceConnector message parsing
# ════════════════════════════════════════════════════════

class TestBinanceMessageParsing:
    """Test the Binance kline message handling."""

    @pytest.mark.asyncio
    async def test_closed_kline_emits_candle(self) -> None:
        received = []

        async def on_candle(c: NormalisedCandle) -> None:
            received.append(c)

        conn = BinanceConnector(["BTC/USDT"], ["H1"], on_candle)

        # Simulate a closed kline message
        msg = {
            "k": {
                "t": 1700000000000,  # ms
                "s": "BTCUSDT",
                "i": "1h",
                "o": "42000.0",
                "h": "42500.0",
                "l": "41800.0",
                "c": "42300.0",
                "v": "125.5",
                "x": True,  # candle is closed
            }
        }
        await conn._handle_message(msg)
        assert len(received) == 1
        assert received[0].symbol == "BTC/USDT"
        assert received[0].timeframe == "H1"
        assert received[0].close == 42300.0

    @pytest.mark.asyncio
    async def test_open_kline_ignored(self) -> None:
        received = []

        async def on_candle(c: NormalisedCandle) -> None:
            received.append(c)

        conn = BinanceConnector(["BTC/USDT"], ["H1"], on_candle)

        msg = {
            "k": {
                "t": 1700000000000,
                "s": "BTCUSDT",
                "i": "1h",
                "o": "42000.0", "h": "42500.0",
                "l": "41800.0", "c": "42300.0",
                "v": "125.5",
                "x": False,  # NOT closed
            }
        }
        await conn._handle_message(msg)
        assert len(received) == 0

    def test_symbol_unpacking(self) -> None:
        assert BinanceConnector._unpack_symbol("BTCUSDT") == "BTC/USDT"
        assert BinanceConnector._unpack_symbol("ETHUSDT") == "ETH/USDT"
        assert BinanceConnector._unpack_symbol("SOLUSDT") == "SOL/USDT"
        assert BinanceConnector._unpack_symbol("ETHBTC") == "ETH/BTC"


# ════════════════════════════════════════════════════════
# MarketDataService (integration — mocked externals)
# ════════════════════════════════════════════════════════

class TestMarketDataServiceIntegration:
    """Integration test with mocked connectors."""

    @pytest.mark.asyncio
    async def test_candle_reaches_rolling_window(self) -> None:
        svc = MarketDataService(
            crypto_symbols=["BTC/USDT"],
            forex_symbols=[],
            timeframes=["H1"],
            enable_rest_fallback=False,
        )

        candle = NormalisedCandle(
            symbol="BTC/USDT",
            timeframe="H1",
            timestamp=1700000000,
            open=42000.0,
            high=42500.0,
            low=41800.0,
            close=42300.0,
            volume=100.0,
            source="test",
        )
        await svc._on_candle(candle)

        df = svc.get_candles("BTC/USDT", "H1")
        assert df is not None
        assert len(df) == 1
        assert df.iloc[0]["close"] == 42300.0

    @pytest.mark.asyncio
    async def test_external_callback_fires(self) -> None:
        svc = MarketDataService(
            crypto_symbols=["ETH/USDT"],
            forex_symbols=[],
            timeframes=["M15"],
            enable_rest_fallback=False,
        )

        results = []
        svc.on_candle(lambda c: results.append(c))

        candle = NormalisedCandle(
            symbol="ETH/USDT",
            timeframe="M15",
            timestamp=1700000000,
            open=2200.0,
            high=2250.0,
            low=2180.0,
            close=2230.0,
            source="test",
        )
        await svc._on_candle(candle)
        assert len(results) == 1
        assert results[0].symbol == "ETH/USDT"
