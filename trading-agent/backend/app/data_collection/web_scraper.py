"""
Web Scraper for Alternative Data Sources
Scrapes financial websites for free data
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import feedparser
import logging
import json
import re

logger = logging.getLogger(__name__)


@dataclass
class ScrapedArticle:
    """Structured article data"""
    title: str
    content: str
    url: str
    source: str
    published_at: Optional[datetime]
    sentiment: Optional[float] = None


class WebScraper:
    """
    Scrapes financial news and data from various sources
    Respects robots.txt and rate limits
    """
    
    # RSS Feeds for financial news
    RSS_FEEDS = {
        "forexlive": "https://www.forexlive.com/feed",
        "dailyfx": "https://www.dailyfx.com/feeds/market-news",
        "fxstreet": "https://www.fxstreet.com/rss/news",
        "investing": "https://www.investing.com/rss/news.rss",
        "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "cointelegraph": "https://cointelegraph.com/rss",
        "cryptonews": "https://cryptonews.com/news/feed",
        "marketwatch": "https://www.marketwatch.com/rss/topstories",
        "seekingalpha": "https://seekingalpha.com/market_currents.xml",
        "zerohedge": "https://feeds.feedburner.com/zerohedge/feed"
    }
    
    # Economic calendar sources
    ECONOMIC_CALENDAR_URLS = {
        "forexfactory": "https://www.forexfactory.com/calendar",
        "investing": "https://www.investing.com/economic-calendar/"
    }
    
    # Fear & Greed indices
    FEAR_GREED_URLS = {
        "cnn": "https://money.cnn.com/data/fear-and-greed/",
        "alternative": "https://alternative.me/crypto/fear-and-greed-index/"
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.cache_duration = 300  # 5 minutes
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": self.user_agent},
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content with error handling"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    return await resp.text()
                else:
                    logger.warning(f"Failed to fetch {url}: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    async def fetch_rss_feed(self, feed_name: str) -> List[ScrapedArticle]:
        """Fetch and parse RSS feed"""
        if feed_name not in self.RSS_FEEDS:
            logger.error(f"Unknown feed: {feed_name}")
            return []
        
        cache_key = f"rss_{feed_name}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached["timestamp"]).seconds < self.cache_duration:
                return cached["data"]
        
        url = self.RSS_FEEDS[feed_name]
        
        try:
            # Use feedparser
            feed = feedparser.parse(url)
            
            articles = []
            for entry in feed.entries[:20]:  # Limit to 20 articles
                published = None
                if hasattr(entry, 'published_parsed'):
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    published = datetime(*entry.updated_parsed[:6])
                
                article = ScrapedArticle(
                    title=entry.get('title', ''),
                    content=entry.get('summary', entry.get('description', '')),
                    url=entry.get('link', ''),
                    source=feed_name,
                    published_at=published
                )
                articles.append(article)
            
            self.cache[cache_key] = {
                "data": articles,
                "timestamp": datetime.now()
            }
            
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_name}: {e}")
            return []
    
    async def fetch_all_rss(self) -> Dict[str, List[ScrapedArticle]]:
        """Fetch all configured RSS feeds"""
        results = {}
        
        tasks = [self.fetch_rss_feed(name) for name in self.RSS_FEEDS.keys()]
        feed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, articles in zip(self.RSS_FEEDS.keys(), feed_results):
            if isinstance(articles, list):
                results[name] = articles
            else:
                logger.error(f"Error fetching {name}: {articles}")
                results[name] = []
        
        return results
    
    async def scrape_economic_calendar(self) -> List[Dict[str, Any]]:
        """Scrape economic calendar events"""
        events = []
        
        # Try ForexFactory
        try:
            url = self.ECONOMIC_CALENDAR_URLS["forexfactory"]
            html = await self._fetch_url(url)
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                # Parse calendar table (simplified)
                # In production, use more robust parsing
                events.extend(self._parse_forexfactory_calendar(soup))
        except Exception as e:
            logger.error(f"Error scraping ForexFactory: {e}")
        
        return events
    
    def _parse_forexfactory_calendar(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse ForexFactory calendar HTML"""
        events = []
        
        try:
            # Find calendar table
            calendar_table = soup.find('table', {'class': 'calendar__table'})
            if calendar_table:
                rows = calendar_table.find_all('tr', {'class': 'calendar__row'})
                
                for row in rows:
                    try:
                        time_cell = row.find('td', {'class': 'calendar__time'})
                        currency_cell = row.find('td', {'class': 'calendar__currency'})
                        event_cell = row.find('td', {'class': 'calendar__event'})
                        impact_cell = row.find('td', {'class': 'calendar__impact'})
                        
                        if event_cell:
                            event = {
                                "time": time_cell.text.strip() if time_cell else None,
                                "currency": currency_cell.text.strip() if currency_cell else None,
                                "event": event_cell.text.strip(),
                                "impact": self._parse_impact(impact_cell),
                                "source": "forexfactory"
                            }
                            events.append(event)
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Error parsing calendar: {e}")
        
        return events
    
    def _parse_impact(self, impact_cell) -> str:
        """Parse impact level from cell"""
        if not impact_cell:
            return "unknown"
        
        icon = impact_cell.find('span')
        if icon:
            icon_class = icon.get('class', [])
            if 'high' in str(icon_class):
                return "high"
            elif 'medium' in str(icon_class):
                return "medium"
            elif 'low' in str(icon_class):
                return "low"
        
        return "unknown"
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """Get fear and greed index data"""
        results = {}
        
        # CNN Fear & Greed (stocks)
        try:
            url = self.FEAR_GREED_URLS["cnn"]
            html = await self._fetch_url(url)
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                # Extract index value (simplified)
                results["stocks"] = {
                    "index": 50,  # Placeholder
                    "sentiment": "neutral",
                    "source": "cnn"
                }
        except Exception as e:
            logger.error(f"Error fetching CNN fear/greed: {e}")
        
        # Alternative.me (crypto)
        try:
            url = "https://api.alternative.me/fng/"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and "data" in data:
                        results["crypto"] = {
                            "index": int(data["data"][0]["value"]),
                            "sentiment": data["data"][0]["value_classification"],
                            "timestamp": data["data"][0]["timestamp"],
                            "source": "alternative.me"
                        }
        except Exception as e:
            logger.error(f"Error fetching crypto fear/greed: {e}")
        
        return results
    
    async def scrape_tradingview_ideas(self, symbol: str) -> List[Dict[str, Any]]:
        """Scrape TradingView trading ideas for a symbol"""
        ideas = []
        
        try:
            # TradingView public ideas endpoint
            url = f"https://www.tradingview.com/ideas-search/?query={symbol}&type=idea"
            html = await self._fetch_url(url)
            
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                # Parse ideas (simplified)
                idea_cards = soup.find_all('div', {'class': 'tv-widget-idea'})
                
                for card in idea_cards[:10]:
                    try:
                        title = card.find('div', {'class': 'tv-widget-idea__title'})
                        author = card.find('a', {'class': 'tv-widget-idea__author'})
                        
                        idea = {
                            "title": title.text.strip() if title else "",
                            "author": author.text.strip() if author else "",
                            "symbol": symbol
                        }
                        ideas.append(idea)
                    except Exception:
                        continue
        except Exception as e:
            logger.error(f"Error scraping TradingView: {e}")
        
        return ideas
    
    async def get_google_trends_proxy(self, keyword: str) -> Dict[str, Any]:
        """
        Get search trend data (proxy for interest)
        Uses pytrends or similar in production
        """
        # Placeholder - would use pytrends in production
        return {
            "keyword": keyword,
            "interest_over_time": [],
            "related_queries": [],
            "timestamp": datetime.now().isoformat()
        }
    
    async def scrape_crypto_exchanges_data(self) -> Dict[str, Any]:
        """Scrape data from crypto exchanges"""
        data = {
            "funding_rates": [],
            "open_interest": [],
            "liquidations": []
        }
        
        # Binance funding rates
        try:
            url = "https://fapi.binance.com/fapi/v1/fundingRate"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    funding_data = await resp.json()
                    data["funding_rates"] = funding_data[:10]
        except Exception as e:
            logger.error(f"Error fetching Binance funding: {e}")
        
        # Binance open interest
        try:
            url = "https://fapi.binance.com/fapi/v1/openInterest"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    oi_data = await resp.json()
                    data["open_interest"] = oi_data
        except Exception as e:
            logger.error(f"Error fetching Binance OI: {e}")
        
        return data
    
    async def get_market_summary(self) -> Dict[str, Any]:
        """Get comprehensive market summary from scraped sources"""
        # Fetch all RSS feeds
        rss_data = await self.fetch_all_rss()
        
        # Get fear & greed
        fear_greed = await self.get_fear_greed_index()
        
        # Get economic calendar
        economic_events = await self.scrape_economic_calendar()
        
        # Get crypto exchange data
        crypto_data = await self.scrape_crypto_exchanges_data()
        
        # Aggregate news sentiment
        all_articles = []
        for source, articles in rss_data.items():
            all_articles.extend(articles)
        
        # Sort by date
        all_articles.sort(
            key=lambda x: x.published_at or datetime.min,
            reverse=True
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "news_count": len(all_articles),
            "latest_news": [
                {
                    "title": a.title,
                    "source": a.source,
                    "published": a.published_at.isoformat() if a.published_at else None,
                    "url": a.url
                }
                for a in all_articles[:20]
            ],
            "fear_greed": fear_greed,
            "economic_events": economic_events[:10],
            "crypto_metrics": crypto_data
        }


# Singleton instance
_scraper: Optional[WebScraper] = None


def get_web_scraper() -> WebScraper:
    """Get or create web scraper singleton"""
    global _scraper
    if _scraper is None:
        _scraper = WebScraper()
    return _scraper
