"""
Normalised OHLCV Candle Schema

Every incoming candle from any source (Binance WebSocket, yfinance polling,
ccxt REST fallback, browser scraper) is normalised into this structure before
being routed to Redis, TimescaleDB, and Kafka.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Timeframe(str, Enum):
    """Supported trading timeframes."""
    M1 = "M1"
    M5 = "M5"
    M15 = "M15"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


class DataQuality(str, Enum):
    """Quality tier of the data source."""
    REALTIME = "realtime"    # Binance WebSocket — sub-second
    DELAYED = "delayed"      # yfinance — ~15min delayed
    REST = "rest"            # ccxt REST polling — seconds
    SCRAPED = "scraped"      # Browser automation — minutes


class DataSource(str, Enum):
    """Origin of market data."""
    BINANCE = "binance"
    YFINANCE = "yfinance"
    CCXT_REST = "ccxt_rest"
    BROWSER = "browser"


class NormalisedCandle(BaseModel):
    """
    Universal OHLCV candle structure used across the entire system.

    Every market data source normalises its output into this model
    before publishing to the data pipeline.
    """
    symbol: str = Field(..., description="Trading pair, e.g. 'EUR/USD' or 'BTC/USDT'")
    timeframe: str = Field(..., description="Candle timeframe, e.g. 'H1', 'M15'")
    timestamp: int = Field(..., description="Unix timestamp in UTC seconds")
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="Highest price in period")
    low: float = Field(..., description="Lowest price in period")
    close: float = Field(..., description="Closing price")
    volume: float = Field(default=0.0, description="Trading volume")
    source: str = Field(..., description="Data source identifier")
    quality: str = Field(
        default=DataQuality.REALTIME.value,
        description="Data quality tier: realtime / delayed / rest / scraped",
    )
    latency_ms: int = Field(
        default=0,
        description="Ingestion latency in milliseconds (time from source to system)",
    )

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """Ensure symbol is non-empty and uppercased."""
        if not v or not v.strip():
            raise ValueError("Symbol must be a non-empty string")
        return v.strip().upper()

    @field_validator("timeframe")
    @classmethod
    def validate_timeframe(cls, v: str) -> str:
        """Validate timeframe is one of the supported values."""
        valid = {tf.value for tf in Timeframe}
        v_upper = v.strip().upper()
        if v_upper not in valid:
            raise ValueError(f"Timeframe must be one of {valid}, got '{v}'")
        return v_upper

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        """Ensure timestamp is a positive Unix timestamp."""
        if v <= 0:
            raise ValueError("Timestamp must be a positive Unix timestamp")
        return v

    @field_validator("open", "high", "low", "close")
    @classmethod
    def validate_positive_price(cls, v: float) -> float:
        """Prices must be positive."""
        if v < 0:
            raise ValueError("Price values must be non-negative")
        return v

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, v: str) -> str:
        """Validate quality tier."""
        valid = {q.value for q in DataQuality}
        v_lower = v.strip().lower()
        if v_lower not in valid:
            raise ValueError(f"Quality must be one of {valid}, got '{v}'")
        return v_lower

    def to_redis_key(self) -> str:
        """Generate the Redis key for hot-cache storage."""
        return f"market:{self.symbol}:{self.timeframe}:latest"

    def to_kafka_topic(self) -> str:
        """Generate the Kafka topic for event publishing."""
        safe_symbol = self.symbol.replace("/", "_")
        return f"market.data.{safe_symbol}"

    def to_db_row(self) -> dict:
        """Convert to a dict suitable for TimescaleDB insertion."""
        from datetime import datetime, timezone
        return {
            "time": datetime.fromtimestamp(self.timestamp, tz=timezone.utc),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "source": self.source,
        }

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "timeframe": "H1",
                "timestamp": 1700000000,
                "open": 37250.50,
                "high": 37400.00,
                "low": 37100.00,
                "close": 37350.00,
                "volume": 1250.5,
                "source": "binance",
                "quality": "realtime",
                "latency_ms": 12,
            }
        }
