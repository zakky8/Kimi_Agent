"""
AI Trading Agent Pro v2 - Configuration
High-End Automated Trading System
"""
import os
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import timedelta


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # App Settings
    APP_NAME: str = "AI Trading Agent Pro"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WEBSOCKET_PORT: int = 8001
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/trading_agent.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Providers (Free Tiers)
    OPENROUTER_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    # Default AI Model
    DEFAULT_AI_MODEL: str = "openrouter/anthropic/claude-3-opus"
    DEFAULT_VISION_MODEL: str = "gemini-pro-vision"
    
    # Financial APIs
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    BINANCE_TESTNET: bool = True
    
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    # Telegram
    TELEGRAM_API_ID: Optional[int] = None
    TELEGRAM_API_HASH: Optional[str] = None
    TELEGRAM_PHONE: Optional[str] = None
    TELEGRAM_SESSION: str = "trading_agent_session"
    
    # Reddit
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "AI-Trading-Agent/2.0"
    
    # MT5
    MT5_ENABLED: bool = False
    MT5_LOGIN: Optional[int] = None
    MT5_PASSWORD: Optional[str] = None
    MT5_SERVER: Optional[str] = None
    MT5_PATH: Optional[str] = None
    
    # Browser Automation
    BROWSER_HEADLESS: bool = True
    BROWSER_TIMEOUT: int = 30
    BROWSER_USER_DATA_DIR: Optional[str] = None
    
    # Timezone
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"  # IST
    
    # Trading Settings
    DEFAULT_PAIRS: List[str] = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD",
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
        "XAUUSD", "XAGUSD", "USOIL", "NATGAS"
    ]
    
    TIMEFRAMES: List[str] = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
    DEFAULT_TIMEFRAME: str = "1h"
    
    # Risk Management
    MAX_DRAWDOWN_PERCENT: float = 10.0
    DAILY_LOSS_LIMIT_PERCENT: float = 2.0
    PER_TRADE_RISK_PERCENT: float = 1.0
    DEFAULT_RISK_REWARD: float = 2.0
    MAX_POSITIONS: int = 5
    
    # Signal Generation
    MIN_CONFIDENCE_THRESHOLD: float = 0.75
    CONFLUENCE_FACTORS_REQUIRED: int = 3
    
    # Monitoring
    MONITOR_INTERVAL_SECONDS: int = 60
    ALERT_ENABLED: bool = True
    
    # Data Collection
    TELEGRAM_CHANNELS: List[str] = field(default_factory=list)
    RSS_FEEDS: List[str] = field(default_factory=list)
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/trading_agent.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Global settings instance
settings = Settings()


# Trading Pairs Configuration
TRADING_PAIRS_CONFIG = {
    "EURUSD": {
        "type": "forex",
        "category": "major",
        "pip_value": 0.0001,
        "spread_avg": 0.0001,
        "volatility": "medium",
        "trading_hours": "24/5",
        "session": "london_ny"
    },
    "GBPUSD": {
        "type": "forex",
        "category": "major",
        "pip_value": 0.0001,
        "spread_avg": 0.0002,
        "volatility": "high",
        "trading_hours": "24/5",
        "session": "london_ny"
    },
    "USDJPY": {
        "type": "forex",
        "category": "major",
        "pip_value": 0.01,
        "spread_avg": 0.01,
        "volatility": "medium",
        "trading_hours": "24/5",
        "session": "tokyo_ny"
    },
    "BTCUSDT": {
        "type": "crypto",
        "category": "major",
        "pip_value": 0.01,
        "spread_avg": 0.5,
        "volatility": "very_high",
        "trading_hours": "24/7",
        "session": "all"
    },
    "ETHUSDT": {
        "type": "crypto",
        "category": "major",
        "pip_value": 0.01,
        "spread_avg": 0.1,
        "volatility": "very_high",
        "trading_hours": "24/7",
        "session": "all"
    },
    "XAUUSD": {
        "type": "commodity",
        "category": "precious_metal",
        "pip_value": 0.01,
        "spread_avg": 0.1,
        "volatility": "medium",
        "trading_hours": "23/5",
        "session": "london_ny"
    },
    "USOIL": {
        "type": "commodity",
        "category": "energy",
        "pip_value": 0.01,
        "spread_avg": 0.03,
        "volatility": "high",
        "trading_hours": "23/5",
        "session": "ny"
    }
}


# AI Provider Configurations
AI_PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "openai/gpt-4-turbo",
            "google/gemini-pro",
            "meta-llama/llama-2-70b-chat"
        ],
        "vision_models": [
            "anthropic/claude-3-opus",
            "google/gemini-pro-vision"
        ],
        "free_tier": True
    },
    "gemini": {
        "name": "Google Gemini",
        "models": [
            "gemini-pro",
            "gemini-pro-vision"
        ],
        "vision_models": [
            "gemini-pro-vision"
        ],
        "free_tier": True
    },
    "groq": {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "llama2-70b-4096",
            "mixtral-8x7b-32768"
        ],
        "free_tier": True
    },
    "anthropic": {
        "name": "Anthropic",
        "models": [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229"
        ],
        "vision_models": [
            "claude-3-opus-20240229"
        ],
        "free_tier": False
    }
}


# Telegram Channels (User Configurable)
DEFAULT_TELEGRAM_CHANNELS = [
    "@forexsignals",
    "@cryptosignals",
    "@tradingview",
    "@forexnews",
    "@cryptonews"
]


# RSS Feeds
RSS_FEEDS = {
    "forexlive": "https://www.forexlive.com/feed",
    "dailyfx": "https://www.dailyfx.com/feeds/market-news",
    "fxstreet": "https://www.fxstreet.com/rss/news",
    "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "investing": "https://www.investing.com/rss/news.rss"
}


# Forex Factory Settings
FOREXFACTORY_CONFIG = {
    "url": "https://www.forexfactory.com/calendar",
    "timezone": "IST",  # Indian Standard Time
    "timezone_offset": "+05:30",
    "update_interval_minutes": 15
}


# Monitoring Settings
MONITORING_CONFIG = {
    "price_check_interval": 60,  # seconds
    "sentiment_check_interval": 300,  # 5 minutes
    "news_check_interval": 600,  # 10 minutes
    "signal_generation_interval": 1800,  # 30 minutes
    "max_alerts_per_hour": 10
}


# Liquidity Zones Configuration
LIQUIDITY_CONFIG = {
    "lookback_periods": 50,
    "zone_merge_threshold": 0.001,  # 0.1%
    "min_zone_width_pips": 5,
    "zone_strength_threshold": 3
}


# Price Action Configuration
PRICE_ACTION_CONFIG = {
    "pinbar_min_wick_ratio": 0.7,
    "engulfing_min_body_ratio": 1.5,
    "doji_max_body_ratio": 0.1,
    "support_resistance_lookback": 100
}
