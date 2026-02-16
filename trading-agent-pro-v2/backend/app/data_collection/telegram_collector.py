"""
Telegram Data Collector
Collects real-time data from multiple Telegram channels
"""
import asyncio
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import re

from telethon import TelegramClient
from telethon.tl.types import Message, Channel

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class TelegramMessage:
    """Structured Telegram message"""
    id: int
    channel: str
    text: str
    sender: Optional[str]
    timestamp: datetime
    views: int
    forwards: int
    replies: int
    has_media: bool
    symbols: List[str]
    sentiment: Optional[float] = None


class TelegramCollector:
    """
    Multi-Channel Telegram Data Collector
    - Collects messages from configured channels
    - Extracts trading symbols
    - Analyzes sentiment
    - Tracks trending symbols
    """
    
    # Trading-related keywords for symbol extraction
    TRADING_SYMBOLS = [
        "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOT", "AVAX",
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD",
        "XAUUSD", "XAGUSD", "USOIL", "NATGAS", "SPX", "NASDAQ"
    ]
    
    # Sentiment keywords
    BULLISH_KEYWORDS = [
        "bullish", "long", "buy", "pump", "moon", "rocket", "breakout",
        "support", "accumulate", "hodl", "up", "rise", "gain", "profit",
        "calls", "target", "resistance broken", " ATH", "all time high"
    ]
    
    BEARISH_KEYWORDS = [
        "bearish", "short", "sell", "dump", "crash", "down", "fall",
        "resistance", "distribution", "correction", "falling", "loss",
        "puts", "bagholder", "bear", "decline", "drop", "support broken"
    ]
    
    def __init__(
        self,
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None,
        phone: Optional[str] = None,
        session_name: str = "trading_agent_session"
    ):
        self.api_id = api_id or settings.TELEGRAM_API_ID
        self.api_hash = api_hash or settings.TELEGRAM_API_HASH
        self.phone = phone or settings.TELEGRAM_PHONE
        self.session_name = session_name
        
        self.client: Optional[TelegramClient] = None
        self.channels: List[str] = settings.TELEGRAM_CHANNELS or []
        self.messages: List[TelegramMessage] = []
        self.symbol_mentions: Dict[str, List[TelegramMessage]] = defaultdict(list)
        self.is_connected = False
        
    async def __aenter__(self):
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
    
    async def connect(self) -> bool:
        """Connect to Telegram"""
        if not self.api_id or not self.api_hash:
            logger.error("Telegram API credentials not configured")
            return False
        
        try:
            self.client = TelegramClient(
                self.session_name,
                self.api_id,
                self.api_hash
            )
            
            await self.client.start(phone=self.phone)
            self.is_connected = True
            
            logger.info("Telegram client connected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
            logger.info("Telegram client disconnected")
    
    def add_channels(self, channels: List[str]):
        """Add channels to monitor"""
        for channel in channels:
            if channel not in self.channels:
                self.channels.append(channel)
                logger.info(f"Added channel: {channel}")
    
    def remove_channel(self, channel: str):
        """Remove a channel from monitoring"""
        if channel in self.channels:
            self.channels.remove(channel)
            logger.info(f"Removed channel: {channel}")
    
    async def fetch_messages(
        self,
        channel: str,
        limit: int = 100,
        hours_back: int = 24
    ) -> List[TelegramMessage]:
        """
        Fetch messages from a channel
        
        Args:
            channel: Channel username or ID
            limit: Maximum messages to fetch
            hours_back: Only fetch messages from last N hours
        """
        if not self.is_connected:
            logger.error("Not connected to Telegram")
            return []
        
        messages = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        try:
            # Get channel entity
            entity = await self.client.get_entity(channel)
            
            # Fetch messages
            async for message in self.client.iter_messages(
                entity,
                limit=limit
            ):
                # Skip old messages
                if message.date.replace(tzinfo=None) < cutoff_time:
                    continue
                
                # Skip messages without text
                if not message.text:
                    continue
                
                # Extract symbols
                symbols = self._extract_symbols(message.text)
                
                # Create message object
                msg = TelegramMessage(
                    id=message.id,
                    channel=channel,
                    text=message.text,
                    sender=message.sender_id,
                    timestamp=message.date.replace(tzinfo=None),
                    views=message.views or 0,
                    forwards=message.forwards or 0,
                    replies=message.replies.replies if message.replies else 0,
                    has_media=message.media is not None,
                    symbols=symbols
                )
                
                # Analyze sentiment
                msg.sentiment = self._analyze_sentiment(message.text)
                
                messages.append(msg)
                
                # Track symbol mentions
                for symbol in symbols:
                    self.symbol_mentions[symbol].append(msg)
            
            logger.info(f"Fetched {len(messages)} messages from {channel}")
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages from {channel}: {e}")
            return []
    
    async def fetch_all_channels(
        self,
        limit_per_channel: int = 50,
        hours_back: int = 24
    ) -> Dict[str, List[TelegramMessage]]:
        """Fetch messages from all configured channels"""
        all_messages = {}
        
        for channel in self.channels:
            try:
                messages = await self.fetch_messages(
                    channel,
                    limit=limit_per_channel,
                    hours_back=hours_back
                )
                all_messages[channel] = messages
                self.messages.extend(messages)
            except Exception as e:
                logger.error(f"Error fetching from {channel}: {e}")
                all_messages[channel] = []
        
        return all_messages
    
    def _extract_symbols(self, text: str) -> List[str]:
        """Extract trading symbols from message text"""
        symbols = []
        text_upper = text.upper()
        
        for symbol in self.TRADING_SYMBOLS:
            # Check for $SYMBOL or #SYMBOL or just SYMBOL
            patterns = [
                rf'\${symbol}\b',
                rf'#{symbol}\b',
                rf'\b{symbol}\b'
            ]
            
            for pattern in patterns:
                if re.search(pattern, text_upper):
                    if symbol not in symbols:
                        symbols.append(symbol)
                    break
        
        return symbols
    
    def _analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of message text
        Returns score from -1 (bearish) to 1 (bullish)
        """
        text_lower = text.lower()
        
        bullish_count = sum(1 for kw in self.BULLISH_KEYWORDS if kw in text_lower)
        bearish_count = sum(1 for kw in self.BEARISH_KEYWORDS if kw in text_lower)
        
        total = bullish_count + bearish_count
        if total == 0:
            return 0.0
        
        # Calculate sentiment score
        score = (bullish_count - bearish_count) / total
        
        # Normalize to -1 to 1
        return max(-1.0, min(1.0, score))
    
    def get_symbol_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment analysis for a specific symbol"""
        mentions = self.symbol_mentions.get(symbol, [])
        
        if not mentions:
            return {
                "symbol": symbol,
                "mentions": 0,
                "sentiment_score": 0,
                "sentiment_label": "neutral",
                "channels": []
            }
        
        # Calculate average sentiment
        sentiments = [m.sentiment for m in mentions if m.sentiment is not None]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        # Determine label
        if avg_sentiment > 0.3:
            label = "very_bullish"
        elif avg_sentiment > 0.1:
            label = "bullish"
        elif avg_sentiment < -0.3:
            label = "very_bearish"
        elif avg_sentiment < -0.1:
            label = "bearish"
        else:
            label = "neutral"
        
        # Get unique channels
        channels = list(set(m.channel for m in mentions))
        
        return {
            "symbol": symbol,
            "mentions": len(mentions),
            "sentiment_score": round(avg_sentiment, 3),
            "sentiment_label": label,
            "channels": channels,
            "latest_messages": [
                {
                    "text": m.text[:200] + "..." if len(m.text) > 200 else m.text,
                    "channel": m.channel,
                    "timestamp": m.timestamp.isoformat(),
                    "sentiment": m.sentiment
                }
                for m in mentions[-5:]
            ]
        }
    
    def get_trending_symbols(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending symbols based on mention count"""
        symbol_data = []
        
        for symbol, mentions in self.symbol_mentions.items():
            if len(mentions) >= 2:  # At least 2 mentions
                sentiments = [m.sentiment for m in mentions if m.sentiment is not None]
                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
                
                symbol_data.append({
                    "symbol": symbol,
                    "mentions": len(mentions),
                    "sentiment_score": round(avg_sentiment, 3),
                    "channels": len(set(m.channel for m in mentions))
                })
        
        # Sort by mention count
        symbol_data.sort(key=lambda x: x["mentions"], reverse=True)
        
        return symbol_data[:limit]
    
    def get_channel_stats(self) -> Dict[str, Any]:
        """Get statistics for all channels"""
        stats = {}
        
        for channel in self.channels:
            channel_messages = [m for m in self.messages if m.channel == channel]
            
            stats[channel] = {
                "total_messages": len(channel_messages),
                "with_media": sum(1 for m in channel_messages if m.has_media),
                "total_views": sum(m.views for m in channel_messages),
                "total_forwards": sum(m.forwards for m in channel_messages),
                "symbols_mentioned": len(set(
                    symbol for m in channel_messages for symbol in m.symbols
                ))
            }
        
        return stats
    
    async def listen_realtime(self, callback: callable):
        """Listen for real-time messages"""
        if not self.is_connected:
            logger.error("Not connected to Telegram")
            return
        
        @self.client.on(events.NewMessage(chats=self.channels))
        async def handler(event):
            message = event.message
            
            if not message.text:
                return
            
            # Extract symbols
            symbols = self._extract_symbols(message.text)
            
            # Create message object
            msg = TelegramMessage(
                id=message.id,
                channel=str(event.chat_id),
                text=message.text,
                sender=message.sender_id,
                timestamp=message.date.replace(tzinfo=None),
                views=message.views or 0,
                forwards=message.forwards or 0,
                replies=message.replies.replies if message.replies else 0,
                has_media=message.media is not None,
                symbols=symbols,
                sentiment=self._analyze_sentiment(message.text)
            )
            
            # Call callback
            await callback(msg)
        
        logger.info("Started real-time listening")
        await self.client.run_until_disconnected()


# Import events for real-time listening
from telethon import events


# Singleton instance
_telegram_collector: Optional[TelegramCollector] = None


def get_telegram_collector() -> TelegramCollector:
    """Get or create Telegram collector singleton"""
    global _telegram_collector
    if _telegram_collector is None:
        _telegram_collector = TelegramCollector()
    return _telegram_collector
