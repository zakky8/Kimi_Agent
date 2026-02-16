"""
RSS Feed Collector Module
Aggregates news from multiple RSS feeds
"""
import asyncio
import aiohttp
import feedparser
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import re

from ..config import settings, DEFAULT_RSS_FEEDS

logger = logging.getLogger(__name__)


@dataclass
class RSSArticle:
    """Structured RSS article"""
    title: str
    link: str
    description: str
    published: datetime
    source: str
    category: str
    sentiment: Optional[float] = None


class RSSCollector:
    """
    RSS Feed Collector
    Aggregates news from configured RSS feeds
    """
    
    def __init__(self, feeds: List[Dict[str, str]] = None):
        self.feeds = feeds or DEFAULT_RSS_FEEDS
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, List[RSSArticle]] = {}
        self.cache_duration = 300  # 5 minutes
        self.last_fetch: Dict[str, datetime] = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": settings.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_feed(self, feed_url: str) -> List[RSSArticle]:
        """Fetch and parse a single RSS feed"""
        # Check cache
        if feed_url in self.cache:
            last_fetch = self.last_fetch.get(feed_url)
            if last_fetch and (datetime.now() - last_fetch).seconds < self.cache_duration:
                return self.cache[feed_url]
        
        try:
            if self.session:
                async with self.session.get(feed_url) as response:
                    if response.status == 200:
                        content = await response.text()
                    else:
                        logger.warning(f"RSS feed returned {response.status}: {feed_url}")
                        return []
            else:
                # Fallback to synchronous fetch
                import requests
                response = requests.get(feed_url, headers={"User-Agent": settings.USER_AGENT}, timeout=30)
                content = response.text
            
            # Parse feed
            feed = feedparser.parse(content)
            
            articles = []
            for entry in feed.entries[:20]:  # Limit to 20 articles per feed
                # Parse published date
                published = self._parse_date(entry)
                
                article = RSSArticle(
                    title=entry.get('title', ''),
                    link=entry.get('link', ''),
                    description=self._clean_html(entry.get('summary', entry.get('description', ''))),
                    published=published,
                    source=feed.feed.get('title', 'Unknown'),
                    category=self._categorize_article(entry)
                )
                articles.append(article)
            
            # Update cache
            self.cache[feed_url] = articles
            self.last_fetch[feed_url] = datetime.now()
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []
    
    async def fetch_all_feeds(self) -> Dict[str, List[RSSArticle]]:
        """Fetch all configured RSS feeds"""
        results = {}
        
        tasks = []
        for feed in self.feeds:
            task = self.fetch_feed(feed['url'])
            tasks.append((feed['name'], task))
        
        # Fetch all concurrently
        for name, task in tasks:
            try:
                articles = await task
                results[name] = articles
            except Exception as e:
                logger.error(f"Error fetching {name}: {e}")
                results[name] = []
        
        return results
    
    async def get_latest_news(
        self,
        category: str = None,
        limit: int = 50
    ) -> List[RSSArticle]:
        """Get latest news from all feeds"""
        all_feeds = await self.fetch_all_feeds()
        
        all_articles = []
        for feed_name, articles in all_feeds.items():
            for article in articles:
                if category is None or article.category == category:
                    all_articles.append(article)
        
        # Sort by published date
        all_articles.sort(key=lambda x: x.published, reverse=True)
        
        return all_articles[:limit]
    
    async def search_news(
        self,
        query: str,
        limit: int = 20
    ) -> List[RSSArticle]:
        """Search news by keyword"""
        all_feeds = await self.fetch_all_feeds()
        
        results = []
        query_lower = query.lower()
        
        for feed_name, articles in all_feeds.items():
            for article in articles:
                if (query_lower in article.title.lower() or 
                    query_lower in article.description.lower()):
                    results.append(article)
        
        # Sort by published date
        results.sort(key=lambda x: x.published, reverse=True)
        
        return results[:limit]
    
    async def get_symbol_news(
        self,
        symbol: str,
        limit: int = 20
    ) -> List[RSSArticle]:
        """Get news for a specific trading symbol"""
        # Generate search queries for symbol
        queries = self._get_symbol_queries(symbol)
        
        all_results = []
        for query in queries:
            results = await self.search_news(query, limit=limit)
            all_results.extend(results)
        
        # Remove duplicates based on link
        seen_links = set()
        unique_results = []
        for article in all_results:
            if article.link not in seen_links:
                seen_links.add(article.link)
                unique_results.append(article)
        
        # Sort by date
        unique_results.sort(key=lambda x: x.published, reverse=True)
        
        return unique_results[:limit]
    
    def _get_symbol_queries(self, symbol: str) -> List[str]:
        """Generate search queries for a symbol"""
        symbol_upper = symbol.upper()
        queries = [symbol_upper]
        
        # Add common variations
        if symbol_upper == "BTC" or symbol_upper == "BTCUSDT":
            queries.extend(["bitcoin", "btc"])
        elif symbol_upper == "ETH" or symbol_upper == "ETHUSDT":
            queries.extend(["ethereum", "eth"])
        elif symbol_upper == "SOL" or symbol_upper == "SOLUSDT":
            queries.extend(["solana", "sol"])
        elif symbol_upper == "EURUSD":
            queries.extend(["EUR/USD", "euro dollar", "euro"])
        elif symbol_upper == "GBPUSD":
            queries.extend(["GBP/USD", "pound dollar", "sterling"])
        elif symbol_upper == "XAUUSD":
            queries.extend(["gold", "XAU/USD", "precious metals"])
        elif symbol_upper == "USOIL":
            queries.extend(["oil", "crude oil", "WTI"])
        
        return queries
    
    def _parse_date(self, entry) -> datetime:
        """Parse published date from entry"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
            elif hasattr(entry, 'published'):
                # Try common formats
                for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z']:
                    try:
                        return datetime.strptime(entry.published, fmt)
                    except ValueError:
                        continue
        except Exception:
            pass
        
        return datetime.now()
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text"""
        if not html:
            return ""
        
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', html)
        # Decode HTML entities
        import html as html_module
        clean = html_module.unescape(clean)
        # Limit length
        return clean[:500] + "..." if len(clean) > 500 else clean
    
    def _categorize_article(self, entry) -> str:
        """Categorize article based on content"""
        title = entry.get('title', '').lower()
        description = entry.get('summary', entry.get('description', '')).lower()
        text = title + " " + description
        
        # Check for crypto keywords
        crypto_keywords = ['bitcoin', 'crypto', 'ethereum', 'btc', 'eth', 'blockchain', 'altcoin']
        if any(kw in text for kw in crypto_keywords):
            return "crypto"
        
        # Check for forex keywords
        forex_keywords = ['forex', 'eur/usd', 'gbp/usd', 'dollar', 'euro', 'fed', 'interest rate']
        if any(kw in text for kw in forex_keywords):
            return "forex"
        
        # Check for stocks
        stock_keywords = ['stock', 'nasdaq', 's&p', 'dow', 'shares', 'equity']
        if any(kw in text for kw in stock_keywords):
            return "stocks"
        
        # Check for commodities
        commodity_keywords = ['gold', 'silver', 'oil', 'commodity', 'crude']
        if any(kw in text for kw in commodity_keywords):
            return "commodities"
        
        return "general"
    
    async def get_feeds_summary(self) -> Dict[str, Any]:
        """Get summary of all feeds"""
        all_feeds = await self.fetch_all_feeds()
        
        total_articles = sum(len(articles) for articles in all_feeds.values())
        
        # Count by category
        category_counts = {}
        for articles in all_feeds.values():
            for article in articles:
                cat = article.category
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Get latest article from each feed
        latest_by_feed = {}
        for feed_name, articles in all_feeds.items():
            if articles:
                latest = max(articles, key=lambda x: x.published)
                latest_by_feed[feed_name] = {
                    "title": latest.title,
                    "published": latest.published.isoformat(),
                    "link": latest.link
                }
        
        return {
            "total_articles": total_articles,
            "feeds_count": len(self.feeds),
            "category_counts": category_counts,
            "latest_by_feed": latest_by_feed,
            "timestamp": datetime.now().isoformat()
        }
    
    def add_feed(self, name: str, url: str, category: str = "general"):
        """Add a new RSS feed"""
        self.feeds.append({
            "name": name,
            "url": url,
            "category": category
        })
        logger.info(f"Added RSS feed: {name}")
    
    def remove_feed(self, name: str):
        """Remove an RSS feed"""
        self.feeds = [f for f in self.feeds if f['name'] != name]
        # Clear cache
        self.cache.pop(name, None)
        logger.info(f"Removed RSS feed: {name}")


# Singleton instance
_rss_collector: Optional[RSSCollector] = None


def get_rss_collector(feeds: List[Dict[str, str]] = None) -> RSSCollector:
    """Get or create RSS collector singleton"""
    global _rss_collector
    if _rss_collector is None:
        _rss_collector = RSSCollector(feeds)
    return _rss_collector
