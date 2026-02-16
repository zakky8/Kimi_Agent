"""
Data Collection Module
Handles free data sources for trading signals
"""

from .reddit_collector import RedditCollector, get_reddit_collector
from .telegram_collector import TelegramCollector, TelegramBotHandler, get_telegram_collector, get_telegram_bot
from .web_scraper import WebScraper, get_web_scraper
from .news_collector import NewsCollector, get_news_collector
from .market_data import MarketDataCollector, get_market_collector
from .binance_client import BinanceClient, get_binance_client
from .mt5_client import MT5Client, get_mt5_client
from .rss_collector import RSSCollector, get_rss_collector

__all__ = [
    "RedditCollector",
    "TelegramCollector",
    "TelegramBotHandler",
    "WebScraper",
    "NewsCollector",
    "MarketDataCollector",
    "BinanceClient",
    "MT5Client",
    "RSSCollector",
    "get_reddit_collector",
    "get_telegram_collector",
    "get_telegram_bot",
    "get_web_scraper",
    "get_news_collector",
    "get_market_collector",
    "get_binance_client",
    "get_mt5_client",
    "get_rss_collector"
]
