"""
Configuration settings for the Trading Agent
"""
import os
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # App Settings
    APP_NAME: str = "AI Trading Agent Pro"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WEBSOCKET_PORT: int = 8001
    
    # Database
    DATABASE_URL: str = "sqlite:///./trading_agent.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # ============================================
    # AI PROVIDERS (Multiple supported)
    # ============================================
    
    # OpenAI / OpenRouter
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None
    
    # Groq
    GROQ_API_KEY: Optional[str] = None
    
    # Baseten
    BASETEN_API_KEY: Optional[str] = None
    
    # Default AI Provider
    DEFAULT_AI_PROVIDER: str = "openrouter"  # openrouter, gemini, groq, baseten
    DEFAULT_AI_MODEL: str = "anthropic/claude-3.5-sonnet"
    
    # ============================================
    # FINANCIAL DATA APIs
    # ============================================
    
    # Binance (Free: WebSocket + REST)
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    BINANCE_TESTNET: bool = True
    
    # Alpha Vantage (Free: 25 calls/day)
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    # CryptoCompare (Free: 100k calls/month)
    CRYPTOCOMPARE_API_KEY: Optional[str] = None
    
    # Finnhub (Free: 60 calls/minute)
    FINNHUB_API_KEY: Optional[str] = None
    
    # ============================================
    # SOCIAL MEDIA & MESSAGING APIs
    # ============================================
    
    # Reddit API (Free: 60 req/min)
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "TradingAgent/2.0"
    
    # Telegram API (Free)
    TELEGRAM_API_ID: Optional[str] = None
    TELEGRAM_API_HASH: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_PHONE: Optional[str] = None
    
    # ============================================
    # NEWS & RSS
    # ============================================
    
    # NewsAPI (Free: 100 requests/day)
    NEWSAPI_KEY: Optional[str] = None
    
    # GNews (Free: 100 requests/day)
    GNEWS_API_KEY: Optional[str] = None
    
    # RSS Feeds (comma-separated list)
    RSS_FEEDS: str = "https://www.forexlive.com/feed,https://www.dailyfx.com/feeds/market-news"
    
    # ============================================
    # MT5 DESKTOP INTEGRATION
    # ============================================
    
    MT5_ENABLED: bool = False
    MT5_ACCOUNT: Optional[str] = None
    MT5_PASSWORD: Optional[str] = None
    MT5_SERVER: Optional[str] = None
    MT5_PATH: Optional[str] = None  # Path to terminal64.exe
    
    # ============================================
    # BROWSER AUTOMATION
    # ============================================
    
    BROWSER_HEADLESS: bool = True
    BROWSER_TIMEOUT: int = 30
    
    # ============================================
    # TRADING SETTINGS
    # ============================================
    
    DEFAULT_PAIRS: List[str] = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
        "XAUUSD", "XAGUSD", "USOIL"
    ]
    
    # Risk Management
    MAX_DRAWDOWN_PERCENT: float = 10.0
    DAILY_LOSS_LIMIT_PERCENT: float = 2.0
    PER_TRADE_RISK_PERCENT: float = 1.0
    DEFAULT_RISK_REWARD: float = 2.0
    
    # Signal Generation
    MIN_CONFIDENCE_THRESHOLD: float = 0.75
    CONFLUENCE_FACTORS_REQUIRED: int = 3
    
    # Data Collection
    SOCIAL_MEDIA_SCAN_INTERVAL: int = 300  # 5 minutes
    NEWS_SCAN_INTERVAL: int = 600  # 10 minutes
    CHART_UPDATE_INTERVAL: int = 60  # 1 minute
    
    # Technical Analysis
    TIMEFRAMES: List[str] = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    DEFAULT_TIMEFRAME: str = "1h"
    
    # Web Scraping
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    REQUEST_TIMEOUT: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/trading_agent.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


# Trading Pairs Configuration
TRADING_PAIRS_CONFIG = {
    "EURUSD": {
        "type": "forex",
        "pip_value": 0.0001,
        "spread_avg": 0.0001,
        "volatility": "medium",
        "trading_hours": "24/5"
    },
    "GBPUSD": {
        "type": "forex",
        "pip_value": 0.0001,
        "spread_avg": 0.0002,
        "volatility": "high",
        "trading_hours": "24/5"
    },
    "USDJPY": {
        "type": "forex",
        "pip_value": 0.01,
        "spread_avg": 0.01,
        "volatility": "medium",
        "trading_hours": "24/5"
    },
    "AUDUSD": {
        "type": "forex",
        "pip_value": 0.0001,
        "spread_avg": 0.0002,
        "volatility": "medium",
        "trading_hours": "24/5"
    },
    "USDCAD": {
        "type": "forex",
        "pip_value": 0.0001,
        "spread_avg": 0.0002,
        "volatility": "medium",
        "trading_hours": "24/5"
    },
    "BTCUSDT": {
        "type": "crypto",
        "pip_value": 0.01,
        "spread_avg": 0.5,
        "volatility": "very_high",
        "trading_hours": "24/7"
    },
    "ETHUSDT": {
        "type": "crypto",
        "pip_value": 0.01,
        "spread_avg": 0.1,
        "volatility": "very_high",
        "trading_hours": "24/7"
    },
    "SOLUSDT": {
        "type": "crypto",
        "pip_value": 0.001,
        "spread_avg": 0.01,
        "volatility": "very_high",
        "trading_hours": "24/7"
    },
    "BNBUSDT": {
        "type": "crypto",
        "pip_value": 0.01,
        "spread_avg": 0.05,
        "volatility": "high",
        "trading_hours": "24/7"
    },
    "XAUUSD": {
        "type": "commodity",
        "pip_value": 0.01,
        "spread_avg": 0.1,
        "volatility": "medium",
        "trading_hours": "23/5"
    },
    "XAGUSD": {
        "type": "commodity",
        "pip_value": 0.001,
        "spread_avg": 0.02,
        "volatility": "medium",
        "trading_hours": "23/5"
    },
    "USOIL": {
        "type": "commodity",
        "pip_value": 0.01,
        "spread_avg": 0.03,
        "volatility": "high",
        "trading_hours": "23/5"
    }
}


# Data Sources Configuration
DATA_SOURCES = {
    "binance": {
        "enabled": True,
        "rate_limit": "1200/min",
        "description": "Crypto spot & futures data",
        "free_tier": True
    },
    "yahoo_finance": {
        "enabled": True,
        "rate_limit": "2000/hour",
        "description": "Free stock and crypto data",
        "free_tier": True
    },
    "alpha_vantage": {
        "enabled": True,
        "rate_limit": "25/day",
        "description": "Free forex and stock data",
        "free_tier": True
    },
    "cryptocompare": {
        "enabled": True,
        "rate_limit": "100k/month",
        "description": "Free crypto data",
        "free_tier": True
    },
    "finnhub": {
        "enabled": True,
        "rate_limit": "60/min",
        "description": "Free financial data",
        "free_tier": True
    },
    "reddit": {
        "enabled": True,
        "rate_limit": "60/min",
        "description": "Community sentiment",
        "free_tier": True
    },
    "telegram": {
        "enabled": True,
        "rate_limit": "unlimited",
        "description": "Channel sentiment",
        "free_tier": True
    },
    "newsapi": {
        "enabled": True,
        "rate_limit": "100/day",
        "description": "News headlines",
        "free_tier": True
    },
    "rss": {
        "enabled": True,
        "rate_limit": "respect robots.txt",
        "description": "RSS feed aggregation",
        "free_tier": True
    },
    "mt5": {
        "enabled": False,
        "rate_limit": "real-time",
        "description": "MetaTrader 5 desktop",
        "free_tier": True
    },
    "web_scraping": {
        "enabled": True,
        "rate_limit": "respect robots.txt",
        "description": "Alternative data sources",
        "free_tier": True
    }
}


# AI Providers Configuration
AI_PROVIDERS = {
    "openrouter": {
        "name": "OpenRouter",
        "models": [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-opus",
            "openai/gpt-4o",
            "google/gemini-pro",
            "meta-llama/llama-3.1-70b"
        ],
        "base_url": "https://openrouter.ai/api/v1",
        "free_tier": True
    },
    "gemini": {
        "name": "Google Gemini",
        "models": [
            "gemini-pro",
            "gemini-pro-vision"
        ],
        "free_tier": True
    },
    "groq": {
        "name": "Groq",
        "models": [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ],
        "free_tier": True
    },
    "baseten": {
        "name": "Baseten",
        "models": [
            "llama-3.1-70b",
            "mistral-7b"
        ],
        "free_tier": True
    }
}


# Default RSS Feeds
DEFAULT_RSS_FEEDS = [
    {"name": "ForexLive", "url": "https://www.forexlive.com/feed", "category": "forex"},
    {"name": "DailyFX", "url": "https://www.dailyfx.com/feeds/market-news", "category": "forex"},
    {"name": "FXStreet", "url": "https://www.fxstreet.com/rss/news", "category": "forex"},
    {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "category": "crypto"},
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com/rss", "category": "crypto"},
    {"name": "MarketWatch", "url": "https://www.marketwatch.com/rss/topstories", "category": "stocks"},
    {"name": "ZeroHedge", "url": "https://feeds.feedburner.com/zerohedge/feed", "category": "news"}
]


# Settings Schema for Frontend
SETTINGS_SCHEMA = {
    "ai_providers": {
        "title": "AI Providers",
        "icon": "Brain",
        "description": "Configure AI model providers for analysis",
        "fields": [
            {"key": "OPENROUTER_API_KEY", "label": "OpenRouter API Key", "type": "password", "placeholder": "sk-or-..."},
            {"key": "GEMINI_API_KEY", "label": "Gemini API Key", "type": "password", "placeholder": "AIza..."},
            {"key": "GROQ_API_KEY", "label": "Groq API Key", "type": "password", "placeholder": "gsk_..."},
            {"key": "BASETEN_API_KEY", "label": "Baseten API Key", "type": "password", "placeholder": "..."},
            {"key": "DEFAULT_AI_PROVIDER", "label": "Default Provider", "type": "select", "options": ["openrouter", "gemini", "groq", "baseten"]},
            {"key": "DEFAULT_AI_MODEL", "label": "Default Model", "type": "text", "placeholder": "anthropic/claude-3.5-sonnet"}
        ]
    },
    "financial_apis": {
        "title": "Financial Data APIs",
        "icon": "LineChart",
        "description": "Configure market data providers",
        "fields": [
            {"key": "BINANCE_API_KEY", "label": "Binance API Key", "type": "password"},
            {"key": "BINANCE_API_SECRET", "label": "Binance API Secret", "type": "password"},
            {"key": "BINANCE_TESTNET", "label": "Use Testnet", "type": "toggle"},
            {"key": "ALPHA_VANTAGE_API_KEY", "label": "Alpha Vantage API Key", "type": "password"},
            {"key": "CRYPTOCOMPARE_API_KEY", "label": "CryptoCompare API Key", "type": "password"},
            {"key": "FINNHUB_API_KEY", "label": "Finnhub API Key", "type": "password"}
        ]
    },
    "social_media": {
        "title": "Social Media & Messaging",
        "icon": "MessageSquare",
        "description": "Configure social data collection",
        "fields": [
            {"key": "REDDIT_CLIENT_ID", "label": "Reddit Client ID", "type": "password"},
            {"key": "REDDIT_CLIENT_SECRET", "label": "Reddit Client Secret", "type": "password"},
            {"key": "TELEGRAM_API_ID", "label": "Telegram API ID", "type": "text"},
            {"key": "TELEGRAM_API_HASH", "label": "Telegram API Hash", "type": "password"},
            {"key": "TELEGRAM_BOT_TOKEN", "label": "Telegram Bot Token", "type": "password"}
        ]
    },
    "news_rss": {
        "title": "News & RSS",
        "icon": "Newspaper",
        "description": "Configure news and RSS feeds",
        "fields": [
            {"key": "NEWSAPI_KEY", "label": "NewsAPI Key", "type": "password"},
            {"key": "GNEWS_API_KEY", "label": "GNews API Key", "type": "password"},
            {"key": "RSS_FEEDS", "label": "Custom RSS Feeds", "type": "textarea", "placeholder": "One URL per line"}
        ]
    },
    "mt5": {
        "title": "MetaTrader 5",
        "icon": "Monitor",
        "description": "Configure MT5 desktop integration",
        "fields": [
            {"key": "MT5_ENABLED", "label": "Enable MT5", "type": "toggle"},
            {"key": "MT5_ACCOUNT", "label": "Account Number", "type": "text"},
            {"key": "MT5_PASSWORD", "label": "Password", "type": "password"},
            {"key": "MT5_SERVER", "label": "Server", "type": "text", "placeholder": "Broker-Server"},
            {"key": "MT5_PATH", "label": "Terminal Path", "type": "text", "placeholder": "C:/Program Files/MetaTrader 5/terminal64.exe"}
        ]
    },
    "risk_management": {
        "title": "Risk Management",
        "icon": "Shield",
        "description": "Configure trading risk parameters",
        "fields": [
            {"key": "PER_TRADE_RISK_PERCENT", "label": "Risk Per Trade (%)", "type": "slider", "min": 0.5, "max": 5, "step": 0.5},
            {"key": "MAX_DRAWDOWN_PERCENT", "label": "Max Drawdown (%)", "type": "slider", "min": 5, "max": 20, "step": 1},
            {"key": "DAILY_LOSS_LIMIT_PERCENT", "label": "Daily Loss Limit (%)", "type": "slider", "min": 1, "max": 5, "step": 0.5},
            {"key": "DEFAULT_RISK_REWARD", "label": "Default R:R Ratio", "type": "slider", "min": 1, "max": 5, "step": 0.5}
        ]
    },
    "signal_settings": {
        "title": "Signal Settings",
        "icon": "Signal",
        "description": "Configure signal generation parameters",
        "fields": [
            {"key": "MIN_CONFIDENCE_THRESHOLD", "label": "Min Confidence (%)", "type": "slider", "min": 50, "max": 95, "step": 5},
            {"key": "CONFLUENCE_FACTORS_REQUIRED", "label": "Confluence Factors", "type": "slider", "min": 2, "max": 5, "step": 1},
            {"key": "DEFAULT_TIMEFRAME", "label": "Default Timeframe", "type": "select", "options": ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]},
            {"key": "CHART_UPDATE_INTERVAL", "label": "Chart Update (sec)", "type": "slider", "min": 10, "max": 300, "step": 10}
        ]
    }
}
