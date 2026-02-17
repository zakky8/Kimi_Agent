"""
Kimi Agent — Real-Time Market Data Ingestion Service (Part 1)

100% FREE data sources only:
  • Binance WebSocket — real-time crypto (free, no API key needed)
  • yfinance polling   — forex / stocks / indices (free, ~15min delayed)
  • ccxt REST fallback  — multi-exchange crypto REST polling (free)
  • Browser scraper     — Playwright automation for premium data (free)

Routes every normalised candle to Redis, TimescaleDB, and Kafka.
Maintains rolling 500-candle in-memory window per symbol/timeframe.
Health metrics emitted every 30 seconds.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import pandas as pd

from app.shared.schemas.candle import DataQuality, NormalisedCandle, Timeframe

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────

BINANCE_WS_BASE = "wss://stream.binance.com:9443/ws"

TIMEFRAME_TO_BINANCE: Dict[str, str] = {
    "M1": "1m", "M5": "5m", "M15": "15m",
    "H1": "1h", "H4": "4h", "D1": "1d",
}

TIMEFRAME_TO_YFINANCE: Dict[str, str] = {
    "M1": "1m", "M5": "5m", "M15": "15m",
    "H1": "1h", "H4": "1h", "D1": "1d",
}

TIMEFRAME_TO_SECONDS: Dict[str, int] = {
    "M1": 60, "M5": 300, "M15": 900,
    "H1": 3600, "H4": 14400, "D1": 86400,
}

ROLLING_WINDOW_SIZE = 500
HEALTH_INTERVAL_S = 30
STALE_TICK_THRESHOLD_S = 120
MAX_BACKOFF_S = 60


# ────────────────────────────────────────────────────────
# Rolling In-Memory Window
# ────────────────────────────────────────────────────────

class RollingWindow:
    """
    Maintains the last *max_size* candles per (symbol, timeframe) as a
    pandas DataFrame so that indicators can be computed immediately
    without a DB hit.
    """

    def __init__(self, max_size: int = ROLLING_WINDOW_SIZE) -> None:
        self._max_size = max_size
        self._windows: Dict[str, pd.DataFrame] = {}

    def _key(self, symbol: str, timeframe: str) -> str:
        return f"{symbol}:{timeframe}"

    def append(self, candle: NormalisedCandle) -> None:
        """Append a normalised candle, evicting oldest if at capacity."""
        key = self._key(candle.symbol, candle.timeframe)
        row = {
            "timestamp": candle.timestamp,
            "open": candle.open,
            "high": candle.high,
            "low": candle.low,
            "close": candle.close,
            "volume": candle.volume,
        }
        if key not in self._windows:
            self._windows[key] = pd.DataFrame([row])
        else:
            df = self._windows[key]
            new_row = pd.DataFrame([row])
            self._windows[key] = pd.concat([df, new_row], ignore_index=True)
            if len(self._windows[key]) > self._max_size:
                self._windows[key] = self._windows[key].iloc[-self._max_size:]

    def get(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Return the DataFrame for the given symbol/timeframe, or None."""
        return self._windows.get(self._key(symbol, timeframe))

    def size(self, symbol: str, timeframe: str) -> int:
        """Current number of candles stored."""
        df = self.get(symbol, timeframe)
        return 0 if df is None else len(df)


# ────────────────────────────────────────────────────────
# Data Router (Redis · TimescaleDB · Kafka)
# ────────────────────────────────────────────────────────

class DataRouter:
    """
    Routes every normalised candle to:
      1. Redis — hot cache  (key: market:{symbol}:{timeframe}:latest)
      2. TimescaleDB — warm store (table: market_data_ohlcv)
      3. Kafka — event bus (topic: market.data.{symbol})
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        database_url: str = "",
        kafka_brokers: str = "localhost:9092",
    ) -> None:
        self._redis_url = redis_url
        self._database_url = database_url
        self._kafka_brokers = kafka_brokers
        self._redis = None
        self._kafka_producer = None
        self._db_pool = None
        self._initialised = False

    async def start(self) -> None:
        """Initialise connections to Redis, TimescaleDB, and Kafka."""
        # ── Redis ──
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("[DataRouter] Redis connected")
        except Exception as exc:
            logger.warning(f"[DataRouter] Redis unavailable — caching disabled: {exc}")
            self._redis = None

        # ── TimescaleDB (asyncpg) ──
        try:
            if self._database_url:
                import asyncpg
                dsn = self._database_url.replace("postgresql+asyncpg://", "postgresql://")
                self._db_pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
                logger.info("[DataRouter] TimescaleDB connected")
        except Exception as exc:
            logger.warning(f"[DataRouter] TimescaleDB unavailable: {exc}")
            self._db_pool = None

        # ── Kafka ──
        try:
            from aiokafka import AIOKafkaProducer
            self._kafka_producer = AIOKafkaProducer(
                bootstrap_servers=self._kafka_brokers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await self._kafka_producer.start()
            logger.info("[DataRouter] Kafka producer started")
        except Exception as exc:
            logger.warning(f"[DataRouter] Kafka unavailable: {exc}")
            self._kafka_producer = None

        self._initialised = True

    async def route(self, candle: NormalisedCandle) -> None:
        """Write candle to all three sinks.  Never raises."""
        await asyncio.gather(
            self._write_redis(candle),
            self._write_timescaledb(candle),
            self._publish_kafka(candle),
            return_exceptions=True,
        )

    async def _write_redis(self, candle: NormalisedCandle) -> None:
        if self._redis is None:
            return
        try:
            key = candle.to_redis_key()
            await self._redis.set(key, candle.model_dump_json(), ex=3600)
            logger.debug(f"[Redis] SET {key}")
        except Exception as exc:
            logger.warning(f"[Redis] Write failed: {exc}")

    async def _write_timescaledb(self, candle: NormalisedCandle) -> None:
        if self._db_pool is None:
            return
        try:
            row = candle.to_db_row()
            async with self._db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO market_data_ohlcv
                        (time, symbol, timeframe, open, high, low, close, volume, source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (time, symbol, timeframe)
                    DO UPDATE SET
                        open   = EXCLUDED.open,
                        high   = EXCLUDED.high,
                        low    = EXCLUDED.low,
                        close  = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        source = EXCLUDED.source
                    """,
                    row["time"], row["symbol"], row["timeframe"],
                    row["open"], row["high"], row["low"], row["close"],
                    row["volume"], row["source"],
                )
            logger.debug(f"[TimescaleDB] Upserted {candle.symbol} {candle.timeframe}")
        except Exception as exc:
            logger.warning(f"[TimescaleDB] Write failed: {exc}")

    async def _publish_kafka(self, candle: NormalisedCandle) -> None:
        if self._kafka_producer is None:
            return
        try:
            topic = candle.to_kafka_topic()
            await self._kafka_producer.send_and_wait(topic, candle.model_dump())
            logger.debug(f"[Kafka] Published to {topic}")
        except Exception as exc:
            logger.warning(f"[Kafka] Publish failed: {exc}")

    async def stop(self) -> None:
        """Graceful teardown."""
        if self._kafka_producer:
            await self._kafka_producer.stop()
        if self._db_pool:
            await self._db_pool.close()
        if self._redis:
            await self._redis.close()
        logger.info("[DataRouter] All connections closed")


# ────────────────────────────────────────────────────────
# Binance WebSocket Connector (FREE — no key required)
# ────────────────────────────────────────────────────────

class BinanceConnector:
    """
    Connects to Binance kline WebSocket streams for crypto pairs.
    100% FREE — no API key needed for public market data.
    """

    def __init__(
        self,
        symbols: List[str],
        timeframes: List[str],
        on_candle: Callable[[NormalisedCandle], Any],
    ) -> None:
        self._symbols = symbols
        self._timeframes = timeframes
        self._on_candle = on_candle
        self._tasks: List[asyncio.Task] = []
        self._running = False

    def _build_streams(self) -> List[str]:
        """Build Binance combined stream names."""
        streams = []
        for sym in self._symbols:
            base = sym.replace("/", "").lower()
            for tf in self._timeframes:
                interval = TIMEFRAME_TO_BINANCE.get(tf)
                if interval:
                    streams.append(f"{base}@kline_{interval}")
        return streams

    async def start(self) -> None:
        """Open WebSocket connection(s) and begin listening."""
        self._running = True
        streams = self._build_streams()
        if not streams:
            logger.warning("[Binance] No streams to subscribe")
            return

        combined = "/".join(streams)
        url = f"{BINANCE_WS_BASE}/{combined}"
        task = asyncio.create_task(self._listen(url))
        self._tasks.append(task)
        logger.info(f"[Binance] Subscribing to {len(streams)} streams")

    async def _listen(self, url: str) -> None:
        """Main listen loop with exponential backoff reconnection."""
        import websockets
        import websockets.exceptions

        backoff = 1.0
        while self._running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    logger.info("[Binance] WebSocket connected")
                    backoff = 1.0
                    async for raw_msg in ws:
                        try:
                            msg = json.loads(raw_msg)
                            await self._handle_message(msg)
                        except Exception as exc:
                            logger.warning(f"[Binance] Bad message: {exc}")
            except asyncio.CancelledError:
                break
            except Exception as exc:
                if not self._running:
                    break
                logger.warning(
                    f"[Binance] Disconnected ({exc}). Reconnecting in {backoff:.1f}s"
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_S)

    async def _handle_message(self, msg: dict) -> None:
        """Parse a Binance kline message and emit candle on close."""
        kline = msg.get("k")
        if not kline:
            return

        is_closed = kline.get("x", False)
        if not is_closed:
            return

        interval = kline.get("i", "")
        tf_map = {v: k for k, v in TIMEFRAME_TO_BINANCE.items()}
        timeframe = tf_map.get(interval)
        if not timeframe:
            return

        raw_symbol = kline.get("s", "").upper()
        symbol = self._unpack_symbol(raw_symbol)
        ingest_ts = int(time.time() * 1000)
        kline_close_ts = int(kline.get("T", ingest_ts))

        try:
            candle = NormalisedCandle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=int(kline["t"] / 1000),
                open=float(kline["o"]),
                high=float(kline["h"]),
                low=float(kline["l"]),
                close=float(kline["c"]),
                volume=float(kline["v"]),
                source="binance",
                quality=DataQuality.REALTIME.value,
                latency_ms=max(0, ingest_ts - kline_close_ts),
            )
            await self._on_candle(candle)
        except Exception as exc:
            logger.warning(f"[Binance] Candle parse error: {exc}")

    @staticmethod
    def _unpack_symbol(raw: str) -> str:
        """Convert 'BTCUSDT' → 'BTC/USDT'."""
        for quote in ("USDT", "BUSD", "USDC", "BTC", "ETH", "BNB"):
            if raw.endswith(quote) and len(raw) > len(quote):
                base = raw[: -len(quote)]
                return f"{base}/{quote}"
        return raw

    async def stop(self) -> None:
        self._running = False
        for t in self._tasks:
            t.cancel()
        logger.info("[Binance] Connector stopped")


# ────────────────────────────────────────────────────────
# yfinance Polling Connector (FREE — forex/stocks/indices)
# ────────────────────────────────────────────────────────

class YFinanceConnector:
    """
    Polls forex, stock, and index data via yfinance (Yahoo Finance).
    100% FREE — no API key needed.  Data is ~15 min delayed for forex.

    yfinance symbols use a different format:
      EUR/USD → EURUSD=X
      GBP/USD → GBPUSD=X
      SPY     → SPY
      BTC-USD → BTC-USD (yahoo crypto format)
    """

    # Poll frequency per timeframe (seconds)
    POLL_INTERVALS: Dict[str, int] = {
        "M1": 60, "M5": 120, "M15": 300,
        "H1": 600, "H4": 1800, "D1": 3600,
    }

    def __init__(
        self,
        symbols: List[str],
        timeframes: List[str],
        on_candle: Callable[[NormalisedCandle], Any],
    ) -> None:
        self._symbols = symbols
        self._timeframes = timeframes
        self._on_candle = on_candle
        self._tasks: List[asyncio.Task] = []
        self._running = False
        self._last_timestamps: Dict[str, int] = {}

    @staticmethod
    def to_yf_symbol(symbol: str) -> str:
        """Convert our symbol format to yfinance format."""
        s = symbol.strip().upper()
        # Forex pairs: EUR/USD → EURUSD=X
        if "/" in s:
            parts = s.split("/")
            if len(parts) == 2:
                base, quote = parts
                # Check if it's a forex pair (both 3-letter currency codes)
                if len(base) == 3 and len(quote) == 3 and quote != "USDT":
                    return f"{base}{quote}=X"
                # Crypto on Yahoo: BTC/USD → BTC-USD
                return f"{base}-{quote}"
        return s  # Stocks/indices: SPY, QQQ, etc.

    @staticmethod
    def from_yf_symbol(yf_sym: str) -> str:
        """Convert yfinance symbol back to our format."""
        if yf_sym.endswith("=X"):
            raw = yf_sym[:-2]
            return f"{raw[:3]}/{raw[3:]}"
        if "-" in yf_sym:
            return yf_sym.replace("-", "/")
        return yf_sym

    async def start(self) -> None:
        self._running = True
        for sym in self._symbols:
            for tf in self._timeframes:
                task = asyncio.create_task(self._poll_loop(sym, tf))
                self._tasks.append(task)
        logger.info(
            f"[yfinance] Polling {len(self._symbols)} symbols × "
            f"{len(self._timeframes)} timeframes"
        )

    async def _poll_loop(self, symbol: str, timeframe: str) -> None:
        """Poll yfinance for new candles at regular intervals."""
        poll_s = self.POLL_INTERVALS.get(timeframe, 600)
        yf_interval = TIMEFRAME_TO_YFINANCE.get(timeframe, "1h")
        key = f"{symbol}:{timeframe}"

        # yfinance period map — how far back to fetch
        period_map = {
            "1m": "1d", "5m": "5d", "15m": "5d",
            "1h": "30d", "1d": "60d",
        }
        yf_period = period_map.get(yf_interval, "30d")

        while self._running:
            try:
                candles = await asyncio.get_event_loop().run_in_executor(
                    None, self._fetch_yfinance, symbol, yf_interval, yf_period
                )
                ingest_ts = int(time.time() * 1000)

                for c in candles:
                    ts = c["timestamp"]
                    if ts <= self._last_timestamps.get(key, 0):
                        continue

                    candle = NormalisedCandle(
                        symbol=symbol.upper(),
                        timeframe=timeframe,
                        timestamp=ts,
                        open=c["open"],
                        high=c["high"],
                        low=c["low"],
                        close=c["close"],
                        volume=c["volume"],
                        source="yfinance",
                        quality=DataQuality.DELAYED.value,
                        latency_ms=max(0, ingest_ts - ts * 1000),
                    )
                    self._last_timestamps[key] = ts
                    await self._on_candle(candle)

            except Exception as exc:
                logger.warning(f"[yfinance] Poll error {symbol}/{timeframe}: {exc}")

            await asyncio.sleep(poll_s)

    def _fetch_yfinance(
        self, symbol: str, interval: str, period: str
    ) -> List[Dict[str, Any]]:
        """Synchronous yfinance fetch — run in executor."""
        import yfinance as yf

        yf_sym = self.to_yf_symbol(symbol)
        ticker = yf.Ticker(yf_sym)
        df = ticker.history(period=period, interval=interval)

        if df is None or df.empty:
            return []

        candles = []
        for idx, row in df.iterrows():
            ts = int(idx.timestamp()) if hasattr(idx, "timestamp") else 0
            candles.append({
                "timestamp": ts,
                "open": float(row.get("Open", 0)),
                "high": float(row.get("High", 0)),
                "low": float(row.get("Low", 0)),
                "close": float(row.get("Close", 0)),
                "volume": float(row.get("Volume", 0)),
            })
        return candles[-10:]  # Only return latest 10 to avoid flooding

    async def stop(self) -> None:
        self._running = False
        for t in self._tasks:
            t.cancel()
        logger.info("[yfinance] Connector stopped")


# ────────────────────────────────────────────────────────
# ccxt REST Fallback Connector (FREE — public data)
# ────────────────────────────────────────────────────────

class RestFallbackConnector:
    """
    Polls candle data via the ccxt async library when WebSockets are
    unavailable. Uses Binance by default. 100% FREE for public data.
    """

    def __init__(
        self,
        symbols: List[str],
        timeframes: List[str],
        on_candle: Callable[[NormalisedCandle], Any],
        exchange_id: str = "binance",
    ) -> None:
        self._symbols = symbols
        self._timeframes = timeframes
        self._on_candle = on_candle
        self._exchange_id = exchange_id
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._last_timestamps: Dict[str, int] = {}

    async def start(self) -> None:
        self._running = True
        for sym in self._symbols:
            for tf in self._timeframes:
                task = asyncio.create_task(self._poll_loop(sym, tf))
                self._tasks.append(task)
        logger.info(
            f"[REST Fallback] Polling {len(self._symbols)}×{len(self._timeframes)} "
            f"combinations on {self._exchange_id}"
        )

    async def _poll_loop(self, symbol: str, timeframe: str) -> None:
        """Poll for new candles at intervals matching the timeframe."""
        try:
            import ccxt.async_support as ccxt_async
        except ImportError:
            logger.error("[REST Fallback] ccxt not installed")
            return

        interval_s = TIMEFRAME_TO_SECONDS.get(timeframe, 3600)
        poll_interval = max(interval_s // 2, 30)
        ccxt_tf = TIMEFRAME_TO_BINANCE.get(timeframe, "1h")
        key = f"{symbol}:{timeframe}"

        exchange = getattr(ccxt_async, self._exchange_id)()
        try:
            while self._running:
                try:
                    ohlcv = await exchange.fetch_ohlcv(symbol, ccxt_tf, limit=5)
                    ingest_ts = int(time.time() * 1000)
                    if ohlcv:
                        for row in ohlcv:
                            ts = int(row[0] / 1000)
                            if ts <= self._last_timestamps.get(key, 0):
                                continue
                            candle = NormalisedCandle(
                                symbol=symbol,
                                timeframe=timeframe,
                                timestamp=ts,
                                open=float(row[1]),
                                high=float(row[2]),
                                low=float(row[3]),
                                close=float(row[4]),
                                volume=float(row[5]),
                                source="ccxt_rest",
                                quality=DataQuality.REST.value,
                                latency_ms=max(0, ingest_ts - int(row[0])),
                            )
                            self._last_timestamps[key] = ts
                            await self._on_candle(candle)
                except Exception as exc:
                    logger.warning(
                        f"[REST Fallback] Poll error {symbol}/{timeframe}: {exc}"
                    )
                await asyncio.sleep(poll_interval)
        finally:
            await exchange.close()

    async def stop(self) -> None:
        self._running = False
        for t in self._tasks:
            t.cancel()
        logger.info("[REST Fallback] Stopped")


# ────────────────────────────────────────────────────────
# Browser Scraper Connector (FREE — Playwright automation)
# ────────────────────────────────────────────────────────

class BrowserScraperConnector:
    """
    Last-resort data source using Playwright headless browser.
    Scrapes TradingView, CoinGlass, and Fear & Greed Index.

    This connector collects supplementary sentiment/analysis data,
    not OHLCV candles. Results are published as special candle-like
    structures for downstream consumers.
    """

    SOURCES = {
        "fear_greed": {
            "url": "https://api.alternative.me/fng/?limit=1&format=json",
            "interval_s": 3600,
            "type": "api",
        },
        "coinglass_funding": {
            "url": "https://www.coinglass.com/FundingRate",
            "interval_s": 1800,
            "type": "scrape",
        },
    }

    def __init__(
        self,
        on_data: Optional[Callable] = None,
    ) -> None:
        self._on_data = on_data
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._cache: Dict[str, Any] = {}

    async def start(self) -> None:
        self._running = True
        # Fear & Greed Index — use simple REST (it's a free JSON API)
        self._tasks.append(asyncio.create_task(self._poll_fear_greed()))
        logger.info("[BrowserScraper] Started supplementary data collection")

    async def _poll_fear_greed(self) -> None:
        """Poll the free Fear & Greed Index API."""
        while self._running:
            try:
                async with aiohttp.ClientSession() as session:
                    url = self.SOURCES["fear_greed"]["url"]
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data and "data" in data and data["data"]:
                                fg = data["data"][0]
                                self._cache["fear_greed"] = {
                                    "value": int(fg.get("value", 50)),
                                    "classification": fg.get("value_classification", "Neutral"),
                                    "timestamp": int(fg.get("timestamp", time.time())),
                                }
                                logger.info(
                                    f"[BrowserScraper] Fear & Greed: "
                                    f"{self._cache['fear_greed']['value']} "
                                    f"({self._cache['fear_greed']['classification']})"
                                )
                                if self._on_data:
                                    await self._on_data("fear_greed", self._cache["fear_greed"])
            except Exception as exc:
                logger.warning(f"[BrowserScraper] Fear & Greed error: {exc}")

            await asyncio.sleep(self.SOURCES["fear_greed"]["interval_s"])

    def get_cached(self, source: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached supplementary data."""
        return self._cache.get(source)

    async def stop(self) -> None:
        self._running = False
        for t in self._tasks:
            t.cancel()
        logger.info("[BrowserScraper] Stopped")


# ────────────────────────────────────────────────────────
# Health Monitor
# ────────────────────────────────────────────────────────

class HealthMonitor:
    """
    Emits ``last_tick_age_seconds`` per symbol every 30s.
    Raises a WARNING if any symbol hasn't received data in > 120s.
    """

    def __init__(self) -> None:
        self._last_tick: Dict[str, float] = {}
        self._task: Optional[asyncio.Task] = None
        self._running = False

    def record_tick(self, symbol: str) -> None:
        """Call this on every incoming candle."""
        self._last_tick[symbol] = time.time()

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._emit_loop())
        logger.info("[Health] Monitor started (interval=30s)")

    async def _emit_loop(self) -> None:
        while self._running:
            await asyncio.sleep(HEALTH_INTERVAL_S)
            now = time.time()
            for symbol, last in self._last_tick.items():
                age = now - last
                if age > STALE_TICK_THRESHOLD_S:
                    logger.warning(
                        f"[Health] STALE — {symbol} last tick {age:.0f}s ago "
                        f"(threshold={STALE_TICK_THRESHOLD_S}s)"
                    )
                else:
                    logger.debug(f"[Health] {symbol} tick age: {age:.1f}s")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    def get_metrics(self) -> Dict[str, float]:
        """Return last_tick_age_seconds per symbol."""
        now = time.time()
        return {sym: round(now - ts, 1) for sym, ts in self._last_tick.items()}


# ════════════════════════════════════════════════════════
# MarketDataService — top-level orchestrator (100% FREE)
# ════════════════════════════════════════════════════════

class MarketDataService:
    """
    Top-level service that:
      1. Spins up Binance WebSocket for crypto (FREE)
      2. Spins up yfinance polling for forex/stocks (FREE)
      3. Starts ccxt REST fallback as safety net (FREE)
      4. Collects supplementary data via browser scraper (FREE)
      5. Routes every normalised candle to Redis, TimescaleDB, Kafka
      6. Maintains rolling in-memory windows (500 candles)
      7. Monitors health and raises alerts for stale symbols

    Usage::

        svc = MarketDataService(
            crypto_symbols=["BTC/USDT", "ETH/USDT"],
            forex_symbols=["EUR/USD", "GBP/USD"],
            stock_symbols=["SPY", "QQQ"],
            timeframes=["M1", "M15", "H1", "H4", "D1"],
        )
        await svc.start()
    """

    def __init__(
        self,
        crypto_symbols: Optional[List[str]] = None,
        forex_symbols: Optional[List[str]] = None,
        stock_symbols: Optional[List[str]] = None,
        timeframes: Optional[List[str]] = None,
        redis_url: str = "redis://localhost:6379/0",
        database_url: str = "",
        kafka_brokers: str = "localhost:9092",
        enable_rest_fallback: bool = True,
        enable_browser_scraper: bool = True,
    ) -> None:
        self.crypto_symbols = crypto_symbols or ["BTC/USDT", "ETH/USDT"]
        self.forex_symbols = forex_symbols or ["EUR/USD", "GBP/USD", "USD/JPY"]
        self.stock_symbols = stock_symbols or []
        self.timeframes = timeframes or ["M1", "M5", "M15", "H1", "H4", "D1"]

        self.rolling_window = RollingWindow(ROLLING_WINDOW_SIZE)
        self.health = HealthMonitor()
        self.router = DataRouter(
            redis_url=redis_url,
            database_url=database_url,
            kafka_brokers=kafka_brokers,
        )

        # ── Crypto: Binance WebSocket (FREE) ──
        self._binance = BinanceConnector(
            symbols=self.crypto_symbols,
            timeframes=self.timeframes,
            on_candle=self._on_candle,
        )

        # ── Forex + Stocks: yfinance polling (FREE) ──
        yf_symbols = self.forex_symbols + self.stock_symbols
        self._yfinance: Optional[YFinanceConnector] = None
        if yf_symbols:
            self._yfinance = YFinanceConnector(
                symbols=yf_symbols,
                timeframes=self.timeframes,
                on_candle=self._on_candle,
            )

        # ── REST fallback for crypto (FREE) ──
        self._rest_fallback: Optional[RestFallbackConnector] = None
        if enable_rest_fallback:
            self._rest_fallback = RestFallbackConnector(
                symbols=self.crypto_symbols,
                timeframes=self.timeframes,
                on_candle=self._on_candle,
            )

        # ── Browser scraper for supplementary data (FREE) ──
        self._browser_scraper: Optional[BrowserScraperConnector] = None
        if enable_browser_scraper:
            self._browser_scraper = BrowserScraperConnector()

        self._candle_callbacks: List[Callable[[NormalisedCandle], Any]] = []

    def on_candle(self, callback: Callable[[NormalisedCandle], Any]) -> None:
        """Register an external callback for every new candle."""
        self._candle_callbacks.append(callback)

    async def _on_candle(self, candle: NormalisedCandle) -> None:
        """Central handler invoked by every connector."""
        logger.debug(
            f"[Candle] {candle.symbol} {candle.timeframe} "
            f"O={candle.open} H={candle.high} L={candle.low} C={candle.close} "
            f"V={candle.volume} src={candle.source} q={candle.quality}"
        )

        # 1. Rolling window
        self.rolling_window.append(candle)

        # 2. Health tracking
        self.health.record_tick(candle.symbol)

        # 3. Route to Redis / TimescaleDB / Kafka
        await self.router.route(candle)

        # 4. Notify external subscribers
        for cb in self._candle_callbacks:
            try:
                result = cb(candle)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:
                logger.warning(f"[Callback] Error in candle callback: {exc}")

    async def start(self) -> None:
        """Start all connectors and the data router."""
        logger.info(
            f"[MarketDataService] Starting (100%% FREE) — "
            f"crypto={self.crypto_symbols}, forex={self.forex_symbols}, "
            f"stocks={self.stock_symbols}, timeframes={self.timeframes}"
        )

        await self.router.start()
        await self.health.start()

        # Start WebSocket connectors
        await self._binance.start()

        # Start yfinance polling
        if self._yfinance:
            await self._yfinance.start()

        # Start REST fallback
        if self._rest_fallback:
            await self._rest_fallback.start()

        # Start browser scraper
        if self._browser_scraper:
            await self._browser_scraper.start()

        logger.info("[MarketDataService] All connectors started (100%% FREE)")

    async def stop(self) -> None:
        """Graceful shutdown of all connectors and router."""
        logger.info("[MarketDataService] Stopping...")
        await self._binance.stop()
        if self._yfinance:
            await self._yfinance.stop()
        if self._rest_fallback:
            await self._rest_fallback.stop()
        if self._browser_scraper:
            await self._browser_scraper.stop()
        await self.health.stop()
        await self.router.stop()
        logger.info("[MarketDataService] Stopped")

    def get_candles(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Return the rolling DataFrame for a symbol/timeframe.
        Returns None if no data has been collected yet.
        """
        return self.rolling_window.get(symbol, timeframe)

    def get_health(self) -> Dict[str, float]:
        """Return last_tick_age_seconds per symbol."""
        return self.health.get_metrics()

    def get_supplementary(self, source: str) -> Optional[Dict[str, Any]]:
        """Get cached supplementary data (e.g. fear_greed)."""
        if self._browser_scraper:
            return self._browser_scraper.get_cached(source)
        return None
