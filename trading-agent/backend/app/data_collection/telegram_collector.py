"""
Telegram Data Collector Module
Collects trading signals and sentiment from Telegram channels/groups
"""
import asyncio
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from collections import Counter
import re

try:
    from telethon import TelegramClient
    from telethon.tl.functions.messages import GetHistoryRequest
    from telethon.tl.types import Channel, Chat, Message
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    PYTHON_TELEGRAM_BOT_AVAILABLE = True
except ImportError:
    PYTHON_TELEGRAM_BOT_AVAILABLE = False

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class TelegramMessage:
    """Structured Telegram message"""
    id: int
    text: str
    sender: str
    channel: str
    date: datetime
    views: int
    forwards: int
    replies: int
    sentiment: Optional[float] = None
    hashtags: List[str] = None
    urls: List[str] = None


class TelegramCollector:
    """
    Collects trading-related messages from Telegram
    Uses Telethon for user client (free) or python-telegram-bot for bot
    """
    
    # Trading-related channels to monitor (public)
    DEFAULT_CHANNELS = [
        "cryptopumpsignals",
        "whale_alert_io",
        "binance_announcements",
        "crypto_trading_signals"
    ]
    
    TRADING_KEYWORDS = [
        "buy", "sell", "long", "short", "pump", "dump",
        "signal", "target", "stop loss", "take profit",
        "breakout", "support", "resistance", "bullish", "bearish",
        "btc", "eth", "crypto", "trading"
    ]
    
    def __init__(
        self,
        api_id: str = None,
        api_hash: str = None,
        bot_token: str = None,
        phone: str = None
    ):
        self.api_id = api_id or settings.TELEGRAM_API_ID
        self.api_hash = api_hash or settings.TELEGRAM_API_HASH
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.phone = phone or settings.TELEGRAM_PHONE
        
        self.client: Optional[TelegramClient] = None
        self.bot: Optional[Bot] = None
        self.session_name = "trading_agent_session"
        self.cache: Dict[str, Any] = {}
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def start(self):
        """Start Telegram client"""
        if not TELETHON_AVAILABLE:
            logger.warning("Telethon not available. Install with: pip install telethon")
            return
        
        if not self.api_id or not self.api_hash:
            logger.warning("Telegram API credentials not configured")
            return
        
        try:
            self.client = TelegramClient(
                self.session_name,
                int(self.api_id),
                self.api_hash
            )
            
            await self.client.start(phone=self.phone)
            
            if await self.client.is_user_authorized():
                logger.info("Telegram client started successfully")
            else:
                logger.warning("Telegram client not authorized")
                
        except Exception as e:
            logger.error(f"Failed to start Telegram client: {e}")
    
    async def close(self):
        """Close Telegram client"""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")
    
    async def get_channel_messages(
        self,
        channel_username: str,
        limit: int = 100
    ) -> List[TelegramMessage]:
        """Get messages from a channel"""
        if not self.client:
            logger.warning("Telegram client not available")
            return []
        
        try:
            # Get channel entity
            entity = await self.client.get_entity(channel_username)
            
            # Get messages
            messages = []
            async for msg in self.client.iter_messages(entity, limit=limit):
                if msg.text:
                    telegram_msg = TelegramMessage(
                        id=msg.id,
                        text=msg.text,
                        sender=msg.sender_id or "unknown",
                        channel=channel_username,
                        date=msg.date,
                        views=msg.views or 0,
                        forwards=msg.forwards or 0,
                        replies=msg.replies.replies if msg.replies else 0,
                        hashtags=self._extract_hashtags(msg.text),
                        urls=self._extract_urls(msg.text)
                    )
                    messages.append(telegram_msg)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages from {channel_username}: {e}")
            return []
    
    async def search_messages(
        self,
        query: str,
        channels: List[str] = None,
        limit: int = 50
    ) -> List[TelegramMessage]:
        """Search for messages containing query"""
        if not channels:
            channels = self.DEFAULT_CHANNELS
        
        all_messages = []
        
        for channel in channels:
            try:
                messages = await self.get_channel_messages(channel, limit=limit)
                
                # Filter by query
                for msg in messages:
                    if query.lower() in msg.text.lower():
                        all_messages.append(msg)
                        
            except Exception as e:
                logger.error(f"Error searching {channel}: {e}")
                continue
        
        # Sort by date
        all_messages.sort(key=lambda x: x.date, reverse=True)
        
        return all_messages[:limit]
    
    async def get_symbol_sentiment(
        self,
        symbol: str,
        channels: List[str] = None
    ) -> Dict[str, Any]:
        """Analyze sentiment for a symbol from Telegram"""
        if not channels:
            channels = self.DEFAULT_CHANNELS
        
        # Search for symbol mentions
        messages = await self.search_messages(symbol, channels, limit=100)
        
        if not messages:
            return {
                "symbol": symbol,
                "total_messages": 0,
                "sentiment_score": 0,
                "sentiment_label": "neutral",
                "channels": []
            }
        
        # Analyze sentiment
        sentiment_data = self._analyze_sentiment_batch(messages)
        
        # Get channel breakdown
        channel_stats = {}
        for msg in messages:
            if msg.channel not in channel_stats:
                channel_stats[msg.channel] = {"count": 0, "views": 0}
            channel_stats[msg.channel]["count"] += 1
            channel_stats[msg.channel]["views"] += msg.views
        
        return {
            "symbol": symbol,
            "total_messages": len(messages),
            "sentiment_score": sentiment_data["score"],
            "sentiment_label": sentiment_data["label"],
            "bullish_count": sentiment_data["bullish"],
            "bearish_count": sentiment_data["bearish"],
            "neutral_count": sentiment_data["neutral"],
            "total_views": sum(m.views for m in messages),
            "total_forwards": sum(m.forwards for m in messages),
            "channels": [
                {
                    "name": name,
                    "mentions": stats["count"],
                    "views": stats["views"]
                }
                for name, stats in channel_stats.items()
            ],
            "recent_messages": [
                {
                    "text": m.text[:200] + "..." if len(m.text) > 200 else m.text,
                    "channel": m.channel,
                    "date": m.date.isoformat(),
                    "views": m.views
                }
                for m in messages[:5]
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_trending_symbols(self, channels: List[str] = None) -> List[Dict[str, Any]]:
        """Extract trending symbols from Telegram"""
        if not channels:
            channels = self.DEFAULT_CHANNELS
        
        all_messages = []
        
        for channel in channels:
            try:
                messages = await self.get_channel_messages(channel, limit=50)
                all_messages.extend(messages)
            except Exception as e:
                continue
        
        # Extract symbols (e.g., $BTC, #ETH)
        symbol_pattern = r'[$#]([A-Z]{2,10})|\b(BTC|ETH|SOL|BNB|XRP|ADA|DOT|AVAX|MATIC|LINK)\b'
        
        symbol_counts = Counter()
        symbol_messages = {}
        
        for msg in all_messages:
            matches = re.findall(symbol_pattern, msg.text.upper())
            for match in matches:
                symbol = match[0] or match[1]
                if len(symbol) >= 2:
                    symbol_counts[symbol] += 1
                    if symbol not in symbol_messages:
                        symbol_messages[symbol] = []
                    symbol_messages[symbol].append(msg)
        
        # Get top symbols with sentiment
        trending = []
        for symbol, count in symbol_counts.most_common(20):
            messages = symbol_messages[symbol]
            sentiment = self._analyze_sentiment_batch(messages)
            
            trending.append({
                "symbol": symbol,
                "mentions": count,
                "sentiment_score": sentiment["score"],
                "sentiment_label": sentiment["label"],
                "avg_views": sum(m.views for m in messages) / len(messages),
                "channels": list(set(m.channel for m in messages))
            })
        
        return trending
    
    def _analyze_sentiment_batch(self, messages: List[TelegramMessage]) -> Dict[str, Any]:
        """Analyze sentiment of messages"""
        bullish_keywords = [
            "bullish", "long", "buy", "pump", "moon", "rocket",
            "breakout", "support", "accumulate", "hodl", "up",
            "calls", "gain", "profit", "target hit"
        ]
        bearish_keywords = [
            "bearish", "short", "sell", "dump", "crash", "down",
            "resistance", "correction", "falling",
            "puts", "loss", "bear", "stop loss hit"
        ]
        
        bullish = 0
        bearish = 0
        neutral = 0
        
        for msg in messages:
            text_lower = msg.text.lower()
            
            bull_count = sum(1 for kw in bullish_keywords if kw in text_lower)
            bear_count = sum(1 for kw in bearish_keywords if kw in text_lower)
            
            # Weight by engagement
            weight = 1 + (msg.views / 1000) + (msg.forwards / 100)
            
            if bull_count > bear_count:
                bullish += weight
                msg.sentiment = 1.0
            elif bear_count > bull_count:
                bearish += weight
                msg.sentiment = -1.0
            else:
                neutral += 1
                msg.sentiment = 0.0
        
        total = bullish + bearish + neutral
        if total == 0:
            total = 1
        
        score = (bullish - bearish) / total
        
        if score > 0.3:
            label = "very_bullish"
        elif score > 0.1:
            label = "bullish"
        elif score < -0.3:
            label = "very_bearish"
        elif score < -0.1:
            label = "bearish"
        else:
            label = "neutral"
        
        return {
            "score": round(score, 3),
            "label": label,
            "bullish": round(bullish, 1),
            "bearish": round(bearish, 1),
            "neutral": round(neutral, 1)
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        return re.findall(r'#(\w+)', text)
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        return re.findall(r'https?://\S+', text)
    
    async def get_market_wide_sentiment(self) -> Dict[str, Any]:
        """Get overall market sentiment from Telegram"""
        channels = self.DEFAULT_CHANNELS[:3]  # Limit to first 3
        
        all_messages = []
        for channel in channels:
            try:
                messages = await self.get_channel_messages(channel, limit=30)
                all_messages.extend(messages)
            except Exception:
                continue
        
        sentiment = self._analyze_sentiment_batch(all_messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_messages": len(all_messages),
            "sentiment": sentiment
        }


# Bot handler for receiving messages
class TelegramBotHandler:
    """Handle Telegram bot commands and messages"""
    
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.application: Optional[Application] = None
    
    async def start_bot(self):
        """Start the Telegram bot"""
        if not PYTHON_TELEGRAM_BOT_AVAILABLE:
            logger.warning("python-telegram-bot not available")
            return
        
        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
            return
        
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("price", self.price_command))
        self.application.add_handler(CommandHandler("signal", self.signal_command))
        
        await self.application.initialize()
        await self.application.start()
        
        logger.info("Telegram bot started")
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.application:
            await self.application.stop()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "Welcome to AI Trading Agent Bot!\n\n"
            "Commands:\n"
            "/price <symbol> - Get current price\n"
            "/signal <symbol> - Get trading signal\n"
            "/help - Show help"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(
            "Available commands:\n\n"
            "/price BTCUSDT - Get Bitcoin price\n"
            "/signal ETHUSDT - Get Ethereum signal\n"
        )
    
    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command"""
        if not context.args:
            await update.message.reply_text("Usage: /price <symbol>")
            return
        
        symbol = context.args[0].upper()
        await update.message.reply_text(f"Getting price for {symbol}...")
        # Integration with market data would go here
    
    async def signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signal command"""
        if not context.args:
            await update.message.reply_text("Usage: /signal <symbol>")
            return
        
        symbol = context.args[0].upper()
        await update.message.reply_text(f"Generating signal for {symbol}...")
        # Integration with signal generator would go here


# Singleton instances
_telegram_collector: Optional[TelegramCollector] = None
_telegram_bot: Optional[TelegramBotHandler] = None


def get_telegram_collector(
    api_id: str = None,
    api_hash: str = None
) -> TelegramCollector:
    """Get or create Telegram collector singleton"""
    global _telegram_collector
    if _telegram_collector is None:
        _telegram_collector = TelegramCollector(api_id, api_hash)
    return _telegram_collector


def get_telegram_bot(bot_token: str = None) -> TelegramBotHandler:
    """Get or create Telegram bot singleton"""
    global _telegram_bot
    if _telegram_bot is None:
        _telegram_bot = TelegramBotHandler(bot_token)
    return _telegram_bot
