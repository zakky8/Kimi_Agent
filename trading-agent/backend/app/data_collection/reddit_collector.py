"""
Reddit Data Collector
Uses free PRAW API for community sentiment analysis
"""
import asyncio
import asyncpraw
from asyncpraw.models import Submission, Comment
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import Counter
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class RedditPost:
    """Structured Reddit post data"""
    id: str
    title: str
    text: str
    author: str
    subreddit: str
    created_at: datetime
    upvotes: int
    upvote_ratio: float
    num_comments: int
    sentiment: Optional[float] = None
    flair: Optional[str] = None
    url: Optional[str] = None


class RedditCollector:
    """
    Collects trading-related posts from Reddit
    Free API: 60 requests/minute
    """
    
    TRADING_SUBREDDITS = [
        "wallstreetbets", "stocks", "investing", "StockMarket",
        "Forex", "CryptoCurrency", "CryptoMarkets", "Bitcoin",
        "Daytrading", "algotrading", "options", "SecurityAnalysis",
        "Economics", "wallstreetbetsOGs", "Superstonk"
    ]
    
    CRYPTO_SUBREDDITS = [
        "CryptoCurrency", "CryptoMarkets", "Bitcoin", "ethereum",
        "SatoshiStreetBets", "CryptoMoonShots", "altcoin", "DeFi"
    ]
    
    FOREX_SUBREDDITS = [
        "Forex", "ForexTrading", "FX", "CurrencyTrading"
    ]
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: str = "TradingAgent/1.0"
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.reddit: Optional[asyncpraw.Reddit] = None
        self.cache: Dict[str, Any] = {}
        self.cache_expiry = 300  # 5 minutes
        self.last_request_time = datetime.now()
        self.min_request_interval = 1.0  # seconds between requests
        
    async def __aenter__(self):
        if self.client_id and self.client_secret:
            self.reddit = asyncpraw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.reddit:
            await self.reddit.close()
    
    async def _rate_limited_request(self):
        """Ensure we don't exceed rate limits"""
        elapsed = (datetime.now() - self.last_request_time).total_seconds()
        if elapsed < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - elapsed)
        self.last_request_time = datetime.now()
    
    async def get_subreddit_posts(
        self,
        subreddit_name: str,
        sort: str = "hot",
        limit: int = 50,
        time_filter: str = "day"
    ) -> List[RedditPost]:
        """
        Get posts from a subreddit
        
        Args:
            subreddit_name: Name of subreddit
            sort: 'hot', 'new', 'top', 'rising'
            limit: Number of posts (max 100)
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
        """
        if not self.reddit:
            logger.warning("Reddit not initialized, skipping")
            return []
        
        cache_key = f"{subreddit_name}_{sort}_{limit}_{time_filter}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < timedelta(seconds=self.cache_expiry):
                return cached["data"]
        
        await self._rate_limited_request()
        
        try:
            subreddit = await self.reddit.subreddit(subreddit_name)
            
            if sort == "hot":
                posts = subreddit.hot(limit=limit)
            elif sort == "new":
                posts = subreddit.new(limit=limit)
            elif sort == "top":
                posts = subreddit.top(time_filter=time_filter, limit=limit)
            elif sort == "rising":
                posts = subreddit.rising(limit=limit)
            else:
                posts = subreddit.hot(limit=limit)
            
            reddit_posts = []
            async for post in posts:
                reddit_post = RedditPost(
                    id=post.id,
                    title=post.title,
                    text=post.selftext,
                    author=str(post.author) if post.author else "[deleted]",
                    subreddit=subreddit_name,
                    created_at=datetime.fromtimestamp(post.created_utc),
                    upvotes=post.score,
                    upvote_ratio=post.upvote_ratio,
                    num_comments=post.num_comments,
                    flair=post.link_flair_text,
                    url=post.url
                )
                reddit_posts.append(reddit_post)
            
            # Cache results
            self.cache[cache_key] = {
                "data": reddit_posts,
                "timestamp": datetime.now()
            }
            
            return reddit_posts
            
        except Exception as e:
            logger.error(f"Error fetching Reddit posts from {subreddit_name}: {e}")
            return []
    
    async def search_posts(
        self,
        query: str,
        subreddits: Optional[List[str]] = None,
        limit: int = 50,
        sort: str = "relevance",
        time_filter: str = "week"
    ) -> List[RedditPost]:
        """Search for posts across subreddits"""
        if not self.reddit:
            return []
        
        await self._rate_limited_request()
        
        try:
            if subreddits:
                subreddit_str = "+".join(subreddits)
            else:
                subreddit_str = "all"
            
            subreddit = await self.reddit.subreddit(subreddit_str)
            search_results = subreddit.search(
                query,
                limit=limit,
                sort=sort,
                time_filter=time_filter
            )
            
            posts = []
            async for post in search_results:
                reddit_post = RedditPost(
                    id=post.id,
                    title=post.title,
                    text=post.selftext,
                    author=str(post.author) if post.author else "[deleted]",
                    subreddit=str(post.subreddit),
                    created_at=datetime.fromtimestamp(post.created_utc),
                    upvotes=post.score,
                    upvote_ratio=post.upvote_ratio,
                    num_comments=post.num_comments,
                    flair=post.link_flair_text,
                    url=post.url
                )
                posts.append(reddit_post)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            return []
    
    async def get_symbol_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze sentiment for a trading symbol across Reddit
        """
        # Determine which subreddits to search
        symbol_upper = symbol.upper()
        
        if symbol_upper in ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA"]:
            subreddits = self.CRYPTO_SUBREDDITS
        elif symbol_upper in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]:
            subreddits = self.FOREX_SUBREDDITS
        else:
            subreddits = self.TRADING_SUBREDDITS[:5]
        
        # Search for symbol mentions
        queries = [
            symbol_upper,
            f"${symbol_upper}",
            f"#{symbol_upper}"
        ]
        
        all_posts = []
        for query in queries:
            posts = await self.search_posts(
                query,
                subreddits=subreddits,
                limit=50,
                time_filter="week"
            )
            all_posts.extend(posts)
        
        # Remove duplicates
        seen_ids = set()
        unique_posts = []
        for post in all_posts:
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_posts.append(post)
        
        # Analyze sentiment
        sentiment_data = self._analyze_sentiment_batch(unique_posts)
        
        # Get top discussions
        top_posts = sorted(
            unique_posts,
            key=lambda p: p.upvotes * p.upvote_ratio,
            reverse=True
        )[:10]
        
        return {
            "symbol": symbol,
            "total_posts": len(unique_posts),
            "sentiment_score": sentiment_data["score"],
            "sentiment_label": sentiment_data["label"],
            "bullish_count": sentiment_data["bullish"],
            "bearish_count": sentiment_data["bearish"],
            "neutral_count": sentiment_data["neutral"],
            "total_upvotes": sum(p.upvotes for p in unique_posts),
            "avg_upvote_ratio": sum(p.upvote_ratio for p in unique_posts) / len(unique_posts) if unique_posts else 0,
            "top_discussions": [
                {
                    "title": p.title,
                    "subreddit": p.subreddit,
                    "upvotes": p.upvotes,
                    "url": f"https://reddit.com{r/p.subreddit}/comments/{p.id}"
                }
                for p in top_posts
            ],
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_market_wide_sentiment(self) -> Dict[str, Any]:
        """Get overall market sentiment from Reddit"""
        markets = {
            "crypto": self.CRYPTO_SUBREDDITS[:3],
            "stocks": ["wallstreetbets", "stocks", "investing"],
            "forex": self.FOREX_SUBREDDITS
        }
        
        results = {}
        for market, subs in markets.items():
            posts = []
            for sub in subs:
                sub_posts = await self.get_subreddit_posts(sub, limit=30)
                posts.extend(sub_posts)
            
            sentiment = self._analyze_sentiment_batch(posts)
            results[market] = {
                "post_count": len(posts),
                **sentiment
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "markets": results
        }
    
    def _analyze_sentiment_batch(self, posts: List[RedditPost]) -> Dict[str, Any]:
        """Analyze sentiment of Reddit posts"""
        bullish_keywords = [
            "bullish", "long", "buy", "pump", "moon", "rocket",
            "breakout", "support", "accumulate", "hodl", "up",
            "calls", "yolo", "tendies", "gain", "profit"
        ]
        bearish_keywords = [
            "bearish", "short", "sell", "dump", "crash", "down",
            "resistance", "distribution", "correction", "falling",
            "puts", "loss", "bagholder", "bear"
        ]
        
        bullish = 0
        bearish = 0
        neutral = 0
        
        for post in posts:
            text = (post.title + " " + post.text).lower()
            
            bull_count = sum(1 for kw in bullish_keywords if kw in text)
            bear_count = sum(1 for kw in bearish_keywords if kw in text)
            
            # Weight by engagement
            weight = 1 + (post.upvotes / 100) + (post.num_comments / 50)
            
            if bull_count > bear_count:
                bullish += weight
                post.sentiment = 1.0
            elif bear_count > bull_count:
                bearish += weight
                post.sentiment = -1.0
            else:
                neutral += 1
                post.sentiment = 0.0
        
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
    
    async def get_trending_symbols(self) -> List[Dict[str, Any]]:
        """Extract trending symbols from Reddit"""
        all_posts = []
        
        for sub in self.TRADING_SUBREDDITS[:5]:
            posts = await self.get_subreddit_posts(sub, limit=50)
            all_posts.extend(posts)
        
        # Extract ticker symbols
        ticker_pattern = r'\$([A-Z]{1,5})|\b([A-Z]{2,5})\b'
        symbol_counts = Counter()
        symbol_posts = {}
        
        for post in all_posts:
            text = post.title + " " + post.text
            matches = re.findall(ticker_pattern, text)
            
            for match in matches:
                symbol = match[0] or match[1]
                if len(symbol) >= 2 and symbol not in ["THE", "AND", "FOR", "USD"]:
                    symbol_counts[symbol] += 1
                    if symbol not in symbol_posts:
                        symbol_posts[symbol] = []
                    symbol_posts[symbol].append(post)
        
        # Get top symbols with sentiment
        trending = []
        for symbol, count in symbol_counts.most_common(20):
            posts = symbol_posts[symbol]
            sentiment = self._analyze_sentiment_batch(posts)
            
            trending.append({
                "symbol": symbol,
                "mentions": count,
                "sentiment_score": sentiment["score"],
                "sentiment_label": sentiment["label"],
                "avg_upvotes": sum(p.upvotes for p in posts) / len(posts)
            })
        
        return trending


# Singleton instance
_reddit_collector: Optional[RedditCollector] = None


def get_reddit_collector(
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> RedditCollector:
    """Get or create Reddit collector singleton"""
    global _reddit_collector
    if _reddit_collector is None:
        _reddit_collector = RedditCollector(client_id, client_secret)
    return _reddit_collector
