"""
Sentiment Analysis Module
Analyzes sentiment from multiple sources
"""
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

from ..data_collection.twitter_collector import TwitterCollector
from ..data_collection.reddit_collector import RedditCollector
from ..data_collection.news_collector import NewsCollector
from ..data_collection.web_scraper import WebScraper

logger = logging.getLogger(__name__)


@dataclass
class SentimentScore:
    """Structured sentiment score"""
    source: str
    score: float  # -1 to 1
    label: str
    volume: int
    timestamp: datetime


class SentimentAnalyzer:
    """
    Aggregates sentiment from multiple sources:
    - Twitter/X
    - Reddit
    - News
    - Fear & Greed indices
    """
    
    def __init__(
        self,
        twitter_collector: Optional[TwitterCollector] = None,
        reddit_collector: Optional[RedditCollector] = None,
        news_collector: Optional[NewsCollector] = None,
        web_scraper: Optional[WebScraper] = None
    ):
        self.twitter = twitter_collector
        self.reddit = reddit_collector
        self.news = news_collector
        self.scraper = web_scraper
        
    async def analyze_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Comprehensive sentiment analysis for a symbol
        """
        sentiment_scores = []
        
        # Twitter sentiment
        if self.twitter:
            try:
                twitter_sentiment = await self.twitter.get_trading_sentiment(symbol)
                sentiment_scores.append(SentimentScore(
                    source="twitter",
                    score=twitter_sentiment.get("sentiment_score", 0),
                    label=twitter_sentiment.get("sentiment_label", "neutral"),
                    volume=twitter_sentiment.get("total_tweets", 0),
                    timestamp=datetime.now()
                ))
            except Exception as e:
                logger.error(f"Twitter sentiment error: {e}")
        
        # Reddit sentiment
        if self.reddit:
            try:
                reddit_sentiment = await self.reddit.get_symbol_sentiment(symbol)
                sentiment_scores.append(SentimentScore(
                    source="reddit",
                    score=reddit_sentiment.get("sentiment_score", 0),
                    label=reddit_sentiment.get("sentiment_label", "neutral"),
                    volume=reddit_sentiment.get("total_posts", 0),
                    timestamp=datetime.now()
                ))
            except Exception as e:
                logger.error(f"Reddit sentiment error: {e}")
        
        # Fear & Greed
        fear_greed_score = None
        if self.scraper:
            try:
                fear_greed = await self.scraper.get_fear_greed_index()
                if "crypto" in fear_greed and symbol in ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD"]:
                    crypto_fg = fear_greed["crypto"]
                    # Convert index (0-100) to sentiment score (-1 to 1)
                    normalized = (crypto_fg.get("index", 50) - 50) / 50
                    fear_greed_score = normalized
                elif "stocks" in fear_greed:
                    stock_fg = fear_greed["stocks"]
                    normalized = (stock_fg.get("index", 50) - 50) / 50
                    fear_greed_score = normalized
            except Exception as e:
                logger.error(f"Fear/Greed error: {e}")
        
        # Aggregate scores
        if sentiment_scores:
            # Weight by volume
            total_volume = sum(s.volume for s in sentiment_scores)
            if total_volume > 0:
                weighted_score = sum(s.score * s.volume for s in sentiment_scores) / total_volume
            else:
                weighted_score = sum(s.score for s in sentiment_scores) / len(sentiment_scores)
            
            # Include fear/greed if available
            if fear_greed_score is not None:
                final_score = weighted_score * 0.7 + fear_greed_score * 0.3
            else:
                final_score = weighted_score
        elif fear_greed_score is not None:
            final_score = fear_greed_score
        else:
            final_score = 0
        
        # Determine label
        if final_score > 0.3:
            label = "very_bullish"
        elif final_score > 0.1:
            label = "bullish"
        elif final_score < -0.3:
            label = "very_bearish"
        elif final_score < -0.1:
            label = "bearish"
        else:
            label = "neutral"
        
        return {
            "symbol": symbol,
            "overall_score": round(final_score, 3),
            "label": label,
            "source_breakdown": [
                {
                    "source": s.source,
                    "score": s.score,
                    "label": s.label,
                    "volume": s.volume
                }
                for s in sentiment_scores
            ],
            "fear_greed": fear_greed_score,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """Get overall market sentiment"""
        results = {}
        
        if self.twitter:
            try:
                results["twitter"] = await self.twitter.get_market_wide_sentiment()
            except Exception as e:
                logger.error(f"Twitter market sentiment error: {e}")
        
        if self.reddit:
            try:
                results["reddit"] = await self.reddit.get_market_wide_sentiment()
            except Exception as e:
                logger.error(f"Reddit market sentiment error: {e}")
        
        if self.scraper:
            try:
                results["fear_greed"] = await self.scraper.get_fear_greed_index()
            except Exception as e:
                logger.error(f"Fear/Greed error: {e}")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "sources": results
        }


# Singleton instance
_sentiment_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer(
    twitter_collector: Optional[TwitterCollector] = None,
    reddit_collector: Optional[RedditCollector] = None,
    news_collector: Optional[NewsCollector] = None,
    web_scraper: Optional[WebScraper] = None
) -> SentimentAnalyzer:
    """Get or create sentiment analyzer singleton"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer(
            twitter_collector,
            reddit_collector,
            news_collector,
            web_scraper
        )
    return _sentiment_analyzer
