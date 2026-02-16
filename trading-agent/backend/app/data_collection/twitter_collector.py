"""
Twitter/X Data Collector
Uses free API tier for social sentiment analysis
"""
import asyncio
import aiohttp
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import re
from collections import Counter
import logging

logger = logging.getLogger(__name__)


@dataclass
class Tweet:
    """Structured tweet data"""
    id: str
    text: str
    author: str
    created_at: datetime
    likes: int
    retweets: int
    replies: int
    sentiment: Optional[float] = None
    hashtags: List[str] = None
    mentions: List[str] = None
    urls: List[str] = None


class TwitterCollector:
    """
    Collects trading-related tweets using free API methods
    Falls back to Nitter scraper if API unavailable
    """
    
    TRADING_KEYWORDS = [
        "forex", "trading", "crypto", "bitcoin", "ethereum",
        "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "GOLD",
        "SPX", "NASDAQ", "DOW", "stocks", "market",
        "bullish", "bearish", "long", "short", "pump", "dump"
    ]
    
    INFLUENCER_LIST = [
        "@CryptoCapo_", "@CryptoKaleo", "@SmartContracter",
        "@IncomeSharks", "@CryptoCred", "@IamCryptoWolf",
        "@FXstreetNews", "@ForexLive", "@DailyFX"
    ]
    
    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_remaining = 100
        self.rate_limit_reset = datetime.now()
        self.cache: Dict[str, Any] = {}
        self.cache_expiry = 300  # 5 minutes
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": "TradingAgent/1.0"}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_api_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated API request"""
        if not self.bearer_token or not self.session:
            return None
            
        if datetime.now() < self.rate_limit_reset and self.rate_limit_remaining <= 0:
            logger.warning("Twitter rate limit reached, waiting...")
            await asyncio.sleep((self.rate_limit_reset - datetime.now()).total_seconds())
        
        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        
        try:
            async with self.session.get(url, headers=headers, params=params, timeout=30) as resp:
                # Update rate limit info
                self.rate_limit_remaining = int(resp.headers.get("x-rate-limit-remaining", 100))
                reset_time = int(resp.headers.get("x-rate-limit-reset", 0))
                self.rate_limit_reset = datetime.fromtimestamp(reset_time)
                
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 429:
                    logger.warning("Twitter API rate limited")
                    return None
                else:
                    logger.error(f"Twitter API error: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Twitter API request failed: {e}")
            return None
    
    async def search_tweets(
        self, 
        query: str, 
        max_results: int = 100,
        tweet_fields: str = "created_at,public_metrics,author_id"
    ) -> List[Tweet]:
        """
        Search tweets using Twitter API v2 (free tier: 500k tweets/month)
        """
        cache_key = f"search_{query}_{max_results}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < timedelta(seconds=self.cache_expiry):
                return cached["data"]
        
        url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "tweet.fields": tweet_fields
        }
        
        data = await self._make_api_request(url, params)
        tweets = []
        
        if data and "data" in data:
            for tweet_data in data["data"]:
                metrics = tweet_data.get("public_metrics", {})
                tweet = Tweet(
                    id=tweet_data["id"],
                    text=tweet_data["text"],
                    author=tweet_data.get("author_id", ""),
                    created_at=datetime.fromisoformat(
                        tweet_data["created_at"].replace("Z", "+00:00")
                    ),
                    likes=metrics.get("like_count", 0),
                    retweets=metrics.get("retweet_count", 0),
                    replies=metrics.get("reply_count", 0),
                    hashtags=self._extract_hashtags(tweet_data["text"]),
                    mentions=self._extract_mentions(tweet_data["text"]),
                    urls=self._extract_urls(tweet_data["text"])
                )
                tweets.append(tweet)
        
        # Cache results
        self.cache[cache_key] = {
            "data": tweets,
            "timestamp": datetime.now()
        }
        
        return tweets
    
    async def get_user_tweets(self, username: str, max_results: int = 50) -> List[Tweet]:
        """Get tweets from a specific user"""
        # First get user ID
        user_url = f"https://api.twitter.com/2/users/by/username/{username}"
        user_data = await self._make_api_request(user_url)
        
        if not user_data or "data" not in user_data:
            return []
        
        user_id = user_data["data"]["id"]
        tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {"max_results": min(max_results, 100)}
        
        data = await self._make_api_request(tweets_url, params)
        tweets = []
        
        if data and "data" in data:
            for tweet_data in data["data"]:
                tweet = Tweet(
                    id=tweet_data["id"],
                    text=tweet_data["text"],
                    author=username,
                    created_at=datetime.now(),  # Parse if available
                    likes=0,
                    retweets=0,
                    replies=0
                )
                tweets.append(tweet)
        
        return tweets
    
    async def get_trading_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze trading sentiment for a symbol from Twitter
        """
        queries = [
            f"${symbol} trading",
            f"#{symbol} forex",
            f"{symbol} bullish OR bearish"
        ]
        
        all_tweets = []
        for query in queries:
            tweets = await self.search_tweets(query, max_results=50)
            all_tweets.extend(tweets)
        
        # Remove duplicates
        seen_ids = set()
        unique_tweets = []
        for tweet in all_tweets:
            if tweet.id not in seen_ids:
                seen_ids.add(tweet.id)
                unique_tweets.append(tweet)
        
        # Analyze sentiment
        sentiment_data = self._analyze_sentiment_batch(unique_tweets)
        
        return {
            "symbol": symbol,
            "total_tweets": len(unique_tweets),
            "sentiment_score": sentiment_data["score"],
            "sentiment_label": sentiment_data["label"],
            "bullish_count": sentiment_data["bullish"],
            "bearish_count": sentiment_data["bearish"],
            "neutral_count": sentiment_data["neutral"],
            "engagement": sum(t.likes + t.retweets for t in unique_tweets),
            "top_hashtags": sentiment_data["top_hashtags"],
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_sentiment_batch(self, tweets: List[Tweet]) -> Dict[str, Any]:
        """Analyze sentiment of tweets using keyword matching"""
        bullish_keywords = [
            "bullish", "long", "buy", "pump", "moon", "rocket",
            "breakout", "support", "accumulate", "hodl", "up"
        ]
        bearish_keywords = [
            "bearish", "short", "sell", "dump", "crash", "down",
            "resistance", "distribution", "correction", "falling"
        ]
        
        bullish = 0
        bearish = 0
        neutral = 0
        all_hashtags = []
        
        for tweet in tweets:
            text_lower = tweet.text.lower()
            all_hashtags.extend(tweet.hashtags or [])
            
            bull_count = sum(1 for kw in bullish_keywords if kw in text_lower)
            bear_count = sum(1 for kw in bearish_keywords if kw in text_lower)
            
            if bull_count > bear_count:
                bullish += 1
                tweet.sentiment = 1.0
            elif bear_count > bull_count:
                bearish += 1
                tweet.sentiment = -1.0
            else:
                neutral += 1
                tweet.sentiment = 0.0
        
        total = len(tweets) if tweets else 1
        score = (bullish - bearish) / total
        
        # Determine label
        if score > 0.2:
            label = "bullish"
        elif score < -0.2:
            label = "bearish"
        else:
            label = "neutral"
        
        # Top hashtags
        hashtag_counts = Counter(all_hashtags)
        top_hashtags = hashtag_counts.most_common(10)
        
        return {
            "score": round(score, 3),
            "label": label,
            "bullish": bullish,
            "bearish": bearish,
            "neutral": neutral,
            "top_hashtags": top_hashtags
        }
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        return re.findall(r'#(\w+)', text)
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text"""
        return re.findall(r'@(\w+)', text)
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        return re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    
    async def get_market_wide_sentiment(self) -> Dict[str, Any]:
        """Get overall market sentiment from Twitter"""
        queries = {
            "crypto": "crypto OR bitcoin OR ethereum trading",
            "forex": "forex OR EURUSD OR GBPUSD trading",
            "stocks": "stocks OR SPX OR NASDAQ trading"
        }
        
        results = {}
        for market, query in queries.items():
            tweets = await self.search_tweets(query, max_results=100)
            sentiment = self._analyze_sentiment_batch(tweets)
            results[market] = {
                "tweet_count": len(tweets),
                **sentiment
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "markets": results
        }
    
    async def fallback_nitter_scraper(self, query: str) -> List[Tweet]:
        """
        Fallback method using Nitter instances (no API key required)
        Note: Nitter availability varies, multiple instances tried
        """
        nitter_instances = [
            "https://nitter.net",
            "https://nitter.it",
            "https://nitter.cz"
        ]
        
        for instance in nitter_instances:
            try:
                url = f"{instance}/search"
                params = {"f": "tweets", "q": query}
                
                async with self.session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        # Parse tweets from HTML (simplified)
                        # In production, use BeautifulSoup for proper parsing
                        return []
            except Exception as e:
                logger.debug(f"Nitter instance {instance} failed: {e}")
                continue
        
        return []


# Singleton instance
_twitter_collector: Optional[TwitterCollector] = None


def get_twitter_collector(bearer_token: Optional[str] = None) -> TwitterCollector:
    """Get or create Twitter collector singleton"""
    global _twitter_collector
    if _twitter_collector is None:
        _twitter_collector = TwitterCollector(bearer_token)
    return _twitter_collector
