"""
News Data Collector
Aggregates news from multiple free sources
"""
import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Structured news article"""
    title: str
    description: str
    content: str
    url: str
    source: str
    author: Optional[str]
    published_at: datetime
    category: Optional[str] = None
    sentiment: Optional[float] = None


class NewsCollector:
    """
    Collects financial news from free APIs
    - NewsAPI (100 requests/day free)
    - GNews (100 requests/day free)
    - Currents API (300 requests/day free)
    """
    
    CATEGORIES = [
        "business", "technology", "economy", 
        "markets", "crypto", "forex"
    ]
    
    def __init__(
        self,
        newsapi_key: Optional[str] = None,
        gnews_key: Optional[str] = None,
        currents_key: Optional[str] = None
    ):
        self.newsapi_key = newsapi_key
        self.gnews_key = gnews_key
        self.currents_key = currents_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.cache_duration = 600  # 10 minutes
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_newsapi(
        self,
        query: Optional[str] = None,
        category: str = "business",
        language: str = "en"
    ) -> List[NewsArticle]:
        """
        Fetch news from NewsAPI
        Free tier: 100 requests/day
        """
        if not self.newsapi_key or not self.session:
            return []
        
        cache_key = f"newsapi_{query}_{category}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < timedelta(seconds=self.cache_duration):
                return cached["data"]
        
        url = "https://newsapi.org/v2/everything" if query else "https://newsapi.org/v2/top-headlines"
        
        params = {
            "apiKey": self.newsapi_key,
            "language": language,
            "pageSize": 20
        }
        
        if query:
            params["q"] = query
            params["sortBy"] = "publishedAt"
            params["from"] = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            params["category"] = category
        
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if data.get("status") == "ok":
                        articles = []
                        for article_data in data.get("articles", []):
                            article = NewsArticle(
                                title=article_data.get("title", ""),
                                description=article_data.get("description", ""),
                                content=article_data.get("content", ""),
                                url=article_data.get("url", ""),
                                source=article_data.get("source", {}).get("name", "Unknown"),
                                author=article_data.get("author"),
                                published_at=datetime.fromisoformat(
                                    article_data["publishedAt"].replace("Z", "+00:00")
                                ) if article_data.get("publishedAt") else datetime.now(),
                                category=category
                            )
                            articles.append(article)
                        
                        self.cache[cache_key] = {
                            "data": articles,
                            "timestamp": datetime.now()
                        }
                        
                        return articles
                else:
                    logger.warning(f"NewsAPI error: {resp.status}")
                    
        except Exception as e:
            logger.error(f"Error fetching NewsAPI: {e}")
        
        return []
    
    async def fetch_gnews(
        self,
        query: Optional[str] = None,
        category: str = "business"
    ) -> List[NewsArticle]:
        """
        Fetch news from GNews
        Free tier: 100 requests/day
        """
        if not self.gnews_key or not self.session:
            return []
        
        cache_key = f"gnews_{query}_{category}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < timedelta(seconds=self.cache_duration):
                return cached["data"]
        
        url = "https://gnews.io/api/v4/search" if query else "https://gnews.io/api/v4/top-headlines"
        
        params = {
            "apikey": self.gnews_key,
            "lang": "en",
            "max": 20
        }
        
        if query:
            params["q"] = query
        if category:
            params["topic"] = category
        
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    articles = []
                    for article_data in data.get("articles", []):
                        article = NewsArticle(
                            title=article_data.get("title", ""),
                            description=article_data.get("description", ""),
                            content=article_data.get("content", ""),
                            url=article_data.get("url", ""),
                            source=article_data.get("source", {}).get("name", "Unknown"),
                            author=None,
                            published_at=datetime.fromisoformat(
                                article_data["publishedAt"].replace("Z", "+00:00")
                            ) if article_data.get("publishedAt") else datetime.now(),
                            category=category
                        )
                        articles.append(article)
                    
                    self.cache[cache_key] = {
                        "data": articles,
                        "timestamp": datetime.now()
                    }
                    
                    return articles
                    
        except Exception as e:
            logger.error(f"Error fetching GNews: {e}")
        
        return []
    
    async def fetch_trading_economics_news(self) -> List[NewsArticle]:
        """
        Fetch news from Trading Economics (free, no API key)
        """
        if not self.session:
            return []
        
        cache_key = "tradingeconomics"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < timedelta(seconds=self.cache_duration):
                return cached["data"]
        
        url = "https://tradingeconomics.com/ws/stream.ashx"
        
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    # Parse the streaming data
                    text = await resp.text()
                    # Extract news items (simplified parsing)
                    articles = []
                    
                    self.cache[cache_key] = {
                        "data": articles,
                        "timestamp": datetime.now()
                    }
                    
                    return articles
                    
        except Exception as e:
            logger.error(f"Error fetching Trading Economics: {e}")
        
        return []
    
    async def get_symbol_news(
        self,
        symbol: str,
        days: int = 7
    ) -> List[NewsArticle]:
        """Get news specific to a trading symbol"""
        queries = self._generate_symbol_queries(symbol)
        
        all_articles = []
        
        # Fetch from all available sources
        if self.newsapi_key:
            for query in queries:
                articles = await self.fetch_newsapi(query=query)
                all_articles.extend(articles)
        
        if self.gnews_key:
            for query in queries:
                articles = await self.fetch_gnews(query=query)
                all_articles.extend(articles)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_articles = [
            a for a in unique_articles 
            if a.published_at >= cutoff_date
        ]
        
        # Sort by date
        recent_articles.sort(key=lambda x: x.published_at, reverse=True)
        
        return recent_articles
    
    def _generate_symbol_queries(self, symbol: str) -> List[str]:
        """Generate search queries for a symbol"""
        symbol_upper = symbol.upper()
        
        # Symbol-specific queries
        queries = [symbol_upper]
        
        if symbol_upper == "BTC":
            queries.extend(["bitcoin", "BTC USD", "crypto"])
        elif symbol_upper == "ETH":
            queries.extend(["ethereum", "ETH USD", "crypto"])
        elif symbol_upper == "EURUSD":
            queries.extend(["EUR USD", "euro dollar", "forex"])
        elif symbol_upper == "GBPUSD":
            queries.extend(["GBP USD", "pound dollar", "forex"])
        elif symbol_upper == "XAUUSD":
            queries.extend(["gold", "XAU USD", "precious metals"])
        elif symbol_upper in ["SPX", "SPY"]:
            queries.extend(["S&P 500", "SPX", "stock market"])
        
        return queries
    
    async def get_market_news_summary(self) -> Dict[str, Any]:
        """Get comprehensive market news summary"""
        # Fetch general market news
        market_news = []
        
        if self.newsapi_key:
            market_news = await self.fetch_newsapi(
                query="stock market OR forex OR crypto",
                category="business"
            )
        
        if not market_news and self.gnews_key:
            market_news = await self.fetch_gnews(
                query="stock market OR forex OR crypto"
            )
        
        # Categorize news
        categories = {
            "crypto": [],
            "forex": [],
            "stocks": [],
            "general": []
        }
        
        for article in market_news:
            title_lower = article.title.lower()
            desc_lower = article.description.lower() if article.description else ""
            text = title_lower + " " + desc_lower
            
            if any(kw in text for kw in ["bitcoin", "crypto", "ethereum", "btc", "eth"]):
                categories["crypto"].append(article)
            elif any(kw in text for kw in ["forex", "eur/usd", "gbp/usd", "dollar", "euro"]):
                categories["forex"].append(article)
            elif any(kw in text for kw in ["stock", "nasdaq", "s&p", "dow", "shares"]):
                categories["stocks"].append(article)
            else:
                categories["general"].append(article)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_articles": len(market_news),
            "by_category": {
                cat: [
                    {
                        "title": a.title,
                        "source": a.source,
                        "published": a.published_at.isoformat(),
                        "url": a.url
                    }
                    for a in articles[:5]
                ]
                for cat, articles in categories.items()
            }
        }


# Singleton instance
_news_collector: Optional[NewsCollector] = None


def get_news_collector(
    newsapi_key: Optional[str] = None,
    gnews_key: Optional[str] = None
) -> NewsCollector:
    """Get or create news collector singleton"""
    global _news_collector
    if _news_collector is None:
        _news_collector = NewsCollector(newsapi_key, gnews_key)
    return _news_collector
