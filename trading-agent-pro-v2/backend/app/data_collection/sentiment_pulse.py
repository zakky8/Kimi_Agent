"""
Sentiment Pulse Service
Autonomous scraping of Reddit and RSS feeds for market mood.
"""

import logging
import asyncio
import aiohttp
import re
from datetime import datetime
from typing import Dict, List, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SentimentPulse:
    """
    Scrapes and analyzes social/news sentiment to feed the OpenClaw Brain.
    """

    def __init__(self):
        self.sources = {
            "reddit": [
                "https://www.reddit.com/r/Forex/new/.rss",
                "https://www.reddit.com/r/CryptoCurrency/new/.rss",
                "https://www.reddit.com/r/gold/new/.rss"
            ],
            "news": [
                "https://www.forexlive.com/feed",
                "https://www.dailyfx.com/feeds/market-news"
            ]
        }
        self.last_pulse: Dict[str, Any] = {}

    async def get_pulse(self) -> Dict[str, Any]:
        """Fetch latest sentiment from all sources"""
        logger.info("Fetching Market Pulse...")
        
        tasks = []
        for category, urls in self.sources.items():
            for url in urls:
                tasks.append(self._fetch_source(category, url))
        
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        pulse = {
            "timestamp": datetime.utcnow().isoformat(),
            "sentiment_score": 0.0,  # -1.0 to 1.0
            "top_keywords": [],
            "hot_topics": [],
            "summary": "Market sentiment is neutral."
        }
        
        all_titles = []
        for res in results:
            if res:
                all_titles.extend(res)
        
        if not all_titles:
            return pulse

        # Simple keyword-based sentiment analysis
        bullish_words = ["buy", "bullish", "long", "moon", "rally", "breakout", "support", "gain"]
        bearish_words = ["sell", "bearish", "short", "dump", "crash", "breakdown", "resistance", "loss"]
        
        bull_count = 0
        bear_count = 0
        keywords = {}

        for title in all_titles:
            title_lower = title.lower()
            for word in bullish_words:
                if word in title_lower:
                    bull_count += 1
            for word in bearish_words:
                if word in title_lower:
                    bear_count += 1
            
            # Extract keywords (simple regex)
            words = re.findall(r'\w+', title_lower)
            for w in words:
                if len(w) > 3:
                    keywords[w] = keywords.get(w, 0) + 1

        total = bull_count + bear_count
        if total > 0:
            pulse["sentiment_score"] = (bull_count - bear_count) / total
        
        # Sort keywords
        sorted_keys = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        pulse["top_keywords"] = [k[0] for k in sorted_keys[:10]]
        pulse["hot_topics"] = all_titles[:5]
        
        if pulse["sentiment_score"] > 0.2:
            pulse["summary"] = f"Bullish sentiment detected ({pulse['sentiment_score']:.2f}). Top focus: {pulse['top_keywords'][0]}."
        elif pulse["sentiment_score"] < -0.2:
            pulse["summary"] = f"Bearish sentiment detected ({pulse['sentiment_score']:.2f}). Top focus: {pulse['top_keywords'][0]}."
        
        self.last_pulse = pulse
        return pulse

    async def _fetch_source(self, category: str, url: str) -> List[str]:
        """Fetch and parse RSS/HTML content"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return []
                    
                    text = await response.text()
                    soup = BeautifulSoup(text, 'xml') # Using xml for RSS
                    
                    titles = []
                    # RSS tags: <title> inside <item> or <entry>
                    items = soup.find_all(['item', 'entry'])
                    for item in items:
                        title = item.find('title')
                        if title:
                            titles.append(title.get_text().strip())
                    
                    return titles
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return []

# Singleton instance
sentiment_pulse = SentimentPulse()
