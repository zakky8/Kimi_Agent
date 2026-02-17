"""
Kimi Agent — Browser Automation Scraper (Part 7)

Uses Playwright headless browser to scrape premium data from free sources:
  • TradingView — chart data, indicator overlays, analyst sentiment
  • CoinGlass   — funding rates, open interest, liquidation data
  • Fear & Greed — already handled via REST API in ingestion.py

All scraped data is cached and published as supplementary context for
the SentimentAgent and TechnicalAgent.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ScrapedData:
    """Container for scraped market intelligence."""
    source: str
    data_type: str          # "funding_rate", "open_interest", "sentiment", etc
    payload: Dict[str, Any]
    timestamp: float
    latency_ms: float = 0.0
    is_stale: bool = False


class AutomatedScraper:
    """
    Headless browser automation via Playwright.
    Runs scheduled scraping tasks in the background.

    Scraping targets (all free, no login required):
      1. CoinGlass funding rates — every 30 min
      2. CoinGlass open interest — every 30 min
      3. TradingView technicals widget — every 15 min (via embed)
    """

    TARGETS = {
        "coinglass_funding": {
            "url": "https://www.coinglass.com/FundingRate",
            "interval_s": 1800,
            "selector": ".ant-table-tbody",
        },
        "coinglass_oi": {
            "url": "https://www.coinglass.com/FuturesOpenInterest",
            "interval_s": 1800,
            "selector": ".ant-table-tbody",
        },
    }

    def __init__(
        self,
        headless: bool = True,
        timeout_s: int = 30,
        on_data: Optional[Callable[[ScrapedData], Any]] = None,
    ) -> None:
        self._headless = headless
        self._timeout = timeout_s * 1000  # Playwright uses ms
        self._on_data = on_data
        self._cache: Dict[str, ScrapedData] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._browser = None

    async def start(self) -> None:
        """Launch browser and start scraping loops."""
        self._running = True
        try:
            from playwright.async_api import async_playwright
            self._pw = await async_playwright().start()
            self._browser = await self._pw.chromium.launch(headless=self._headless)
            logger.info("[Scraper] Playwright browser launched")

            for name, target in self.TARGETS.items():
                task = asyncio.create_task(self._scrape_loop(name, target))
                self._tasks.append(task)

            logger.info(f"[Scraper] {len(self.TARGETS)} scraping tasks started")

        except ImportError:
            logger.warning(
                "[Scraper] Playwright not installed — run: pip install playwright && playwright install chromium"
            )
        except Exception as exc:
            logger.warning(f"[Scraper] Browser launch failed: {exc}")

    async def _scrape_loop(self, name: str, target: Dict[str, Any]) -> None:
        """Periodic scraping loop for a single target."""
        while self._running:
            try:
                start = time.time()
                data = await self._scrape_page(target["url"], target.get("selector"))
                latency = (time.time() - start) * 1000

                scraped = ScrapedData(
                    source=name,
                    data_type=name,
                    payload=data,
                    timestamp=time.time(),
                    latency_ms=latency,
                )
                self._cache[name] = scraped

                if self._on_data:
                    await self._on_data(scraped) if asyncio.iscoroutinefunction(self._on_data) else self._on_data(scraped)

                logger.info(f"[Scraper] {name}: scraped in {latency:.0f}ms")

            except Exception as exc:
                logger.warning(f"[Scraper] {name} error: {exc}")

            await asyncio.sleep(target["interval_s"])

    async def _scrape_page(self, url: str, selector: Optional[str] = None) -> Dict[str, Any]:
        """Scrape a single page and extract text content."""
        if self._browser is None:
            return {"error": "browser_not_available"}

        page = await self._browser.new_page()
        try:
            await page.goto(url, timeout=self._timeout, wait_until="networkidle")

            # Wait for specific selector if provided
            if selector:
                try:
                    await page.wait_for_selector(selector, timeout=10000)
                except Exception:
                    pass  # Selector may not appear on all pages

            # Extract page text
            title = await page.title()
            text = await page.inner_text("body")

            # Truncate to avoid memory issues
            text = text[:5000] if len(text) > 5000 else text

            return {
                "title": title,
                "text": text,
                "url": url,
                "scraped_at": time.time(),
            }

        finally:
            await page.close()

    def get_cached(self, source: str) -> Optional[ScrapedData]:
        """Retrieve cached data for a source."""
        return self._cache.get(source)

    def get_all_cached(self) -> Dict[str, ScrapedData]:
        """Return all cached scraped data."""
        return dict(self._cache)

    async def stop(self) -> None:
        """Shutdown browser and cancel tasks."""
        self._running = False
        for t in self._tasks:
            t.cancel()
        if self._browser:
            await self._browser.close()
        if hasattr(self, "_pw") and self._pw:
            await self._pw.stop()
        logger.info("[Scraper] Stopped")
