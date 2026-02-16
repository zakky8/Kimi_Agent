"""
Research Engine Module
Handles automated research tasks using browser automation
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

from .browser_agent import BrowserAgent, ResearchResult

logger = logging.getLogger(__name__)


@dataclass
class ResearchTask:
    """Research task definition"""
    task_id: str
    query: str
    sources: List[str]
    max_results: int
    status: str = "pending"
    results: List[ResearchResult] = None
    created_at: datetime = None
    completed_at: datetime = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = []
        if self.created_at is None:
            self.created_at = datetime.now()


class ResearchEngine:
    """
    Research engine for automated data collection
    """
    
    # Predefined research sources
    SOURCES = {
        "market_news": [
            "https://www.forexlive.com",
            "https://www.dailyfx.com",
            "https://www.fxstreet.com",
            "https://www.investing.com"
        ],
        "crypto_news": [
            "https://www.coindesk.com",
            "https://cointelegraph.com",
            "https://cryptonews.com"
        ],
        "economic_calendar": [
            "https://www.forexfactory.com/calendar",
            "https://www.investing.com/economic-calendar/"
        ],
        "sentiment": [
            "https://alternative.me/crypto/fear-and-greed-index/",
            "https://money.cnn.com/data/fear-and-greed/"
        ],
        "api_docs": [
            "https://binance-docs.github.io/apidocs/",
            "https://www.alphavantage.co/documentation/",
            "https://openrouter.ai/docs"
        ]
    }
    
    def __init__(self):
        self.tasks: Dict[str, ResearchTask] = {}
        self.browser: Optional[BrowserAgent] = None
    
    async def __aenter__(self):
        self.browser = BrowserAgent()
        await self.browser.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
    
    async def research_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Comprehensive research for a trading symbol
        """
        logger.info(f"Starting research for {symbol}")
        
        results = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "news": [],
            "sentiment": {},
            "technical_analysis": {},
            "related_searches": []
        }
        
        try:
            # Search for recent news
            search_query = f"{symbol} trading news today"
            google_results = await self.browser.search_google(search_query)
            results["news"] = google_results[:5]
            
            # Get fear & greed index
            fear_greed = await self.browser.get_fear_greed_index()
            results["sentiment"] = fear_greed
            
            # Search for technical analysis
            ta_query = f"{symbol} technical analysis support resistance"
            ta_results = await self.browser.search_google(ta_query)
            results["technical_analysis"] = ta_results[:3]
            
            # Related searches
            related_query = f"{symbol} price prediction forecast"
            related_results = await self.browser.search_google(related_query)
            results["related_searches"] = related_results[:3]
            
        except Exception as e:
            logger.error(f"Research error for {symbol}: {e}")
        
        return results
    
    async def research_api(self, api_name: str) -> Dict[str, Any]:
        """
        Research API documentation
        """
        logger.info(f"Researching API: {api_name}")
        
        try:
            result = await self.browser.research_api_docs(api_name)
            
            return {
                "api_name": api_name,
                "title": result.title,
                "url": result.url,
                "content_length": len(result.content),
                "timestamp": result.timestamp.isoformat(),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"API research error: {e}")
            return {
                "api_name": api_name,
                "error": str(e),
                "status": "failed"
            }
    
    async def monitor_economic_calendar(self) -> List[Dict[str, Any]]:
        """
        Monitor economic calendar for upcoming events
        """
        logger.info("Monitoring economic calendar")
        
        events = []
        
        try:
            # Navigate to ForexFactory calendar
            await self.browser.navigate("https://www.forexfactory.com/calendar")
            
            # Extract events
            if self.browser.page:
                # Wait for calendar to load
                await self.browser.page.wait_for_selector('table.calendar__table', timeout=10000)
                
                # Extract event rows
                rows = await self.browser.page.query_selector_all('tr.calendar__row')
                
                for row in rows[:20]:  # Limit to 20 events
                    try:
                        time_elem = await row.query_selector('td.calendar__time')
                        currency_elem = await row.query_selector('td.calendar__currency')
                        event_elem = await row.query_selector('td.calendar__event')
                        impact_elem = await row.query_selector('td.calendar__impact')
                        
                        if event_elem:
                            event_data = {
                                "time": await time_elem.inner_text() if time_elem else "",
                                "currency": await currency_elem.inner_text() if currency_elem else "",
                                "event": await event_elem.inner_text() if event_elem else "",
                                "impact": "high" if impact_elem and await impact_elem.query_selector('span.high') else "low"
                            }
                            events.append(event_data)
                    except Exception as e:
                        continue
                        
        except Exception as e:
            logger.error(f"Calendar monitoring error: {e}")
        
        return events
    
    async def collect_sentiment_data(self) -> Dict[str, Any]:
        """
        Collect sentiment data from multiple sources
        """
        logger.info("Collecting sentiment data")
        
        sentiment_data = {
            "timestamp": datetime.now().isoformat(),
            "crypto_fear_greed": {},
            "stock_fear_greed": {},
            "trending_searches": []
        }
        
        try:
            # Crypto fear & greed
            await self.browser.navigate("https://alternative.me/crypto/fear-and-greed-index/")
            
            if self.browser.page:
                # Extract index value
                index_elem = await self.browser.page.query_selector('.fng-circle')
                if index_elem:
                    index_text = await index_elem.inner_text()
                    sentiment_data["crypto_fear_greed"]["index"] = index_text.strip()
            
            # Stock fear & greed
            stock_fg = await self.browser.get_fear_greed_index()
            sentiment_data["stock_fear_greed"] = stock_fg
            
            # Trending searches
            trending = await self.browser.search_google("trending stocks crypto today")
            sentiment_data["trending_searches"] = trending[:5]
            
        except Exception as e:
            logger.error(f"Sentiment collection error: {e}")
        
        return sentiment_data
    
    async def create_research_task(
        self,
        task_id: str,
        query: str,
        sources: List[str] = None,
        max_results: int = 10
    ) -> ResearchTask:
        """Create and queue a research task"""
        
        if sources is None:
            sources = ["market_news", "sentiment"]
        
        task = ResearchTask(
            task_id=task_id,
            query=query,
            sources=sources,
            max_results=max_results
        )
        
        self.tasks[task_id] = task
        
        # Execute task
        asyncio.create_task(self._execute_task(task))
        
        return task
    
    async def _execute_task(self, task: ResearchTask):
        """Execute a research task"""
        task.status = "running"
        
        try:
            for source in task.sources:
                if source == "market_news":
                    results = await self.browser.search_google(task.query)
                    for r in results[:task.max_results]:
                        task.results.append(ResearchResult(
                            url=r.get("url", ""),
                            title=r.get("title", ""),
                            content=r.get("snippet", ""),
                            timestamp=datetime.now(),
                            metadata={"source": "google_search"}
                        ))
                
                elif source == "sentiment":
                    sentiment = await self.collect_sentiment_data()
                    task.results.append(ResearchResult(
                        url="",
                        title="Sentiment Analysis",
                        content=json.dumps(sentiment),
                        timestamp=datetime.now(),
                        metadata={"source": "sentiment"}
                    ))
                
                elif source == "economic_calendar":
                    events = await self.monitor_economic_calendar()
                    task.results.append(ResearchResult(
                        url="https://www.forexfactory.com/calendar",
                        title="Economic Calendar",
                        content=json.dumps(events),
                        timestamp=datetime.now(),
                        metadata={"source": "economic_calendar"}
                    ))
            
            task.status = "completed"
            task.completed_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            task.status = "failed"
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status,
            "query": task.query,
            "results_count": len(task.results),
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }
    
    def get_task_results(self, task_id: str) -> Optional[List[Dict]]:
        """Get task results"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return [asdict(r) for r in task.results]


# Singleton instance
_research_engine: Optional[ResearchEngine] = None


async def get_research_engine() -> ResearchEngine:
    """Get or create research engine singleton"""
    global _research_engine
    if _research_engine is None:
        _research_engine = ResearchEngine()
    return _research_engine
