"""
Browser Agent Module
Handles browser automation using Playwright/Selenium for research
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import json

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Result from browser research"""
    url: str
    title: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]


class BrowserAgent:
    """
    Browser automation agent for research and data collection
    Uses Playwright (preferred) or Selenium as fallback
    """
    
    def __init__(self, headless: bool = None):
        self.headless = headless if headless is not None else settings.BROWSER_HEADLESS
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.driver = None
        self.use_playwright = PLAYWRIGHT_AVAILABLE
        self.use_selenium = SELENIUM_AVAILABLE and not PLAYWRIGHT_AVAILABLE
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def start(self):
        """Start browser instance"""
        if self.use_playwright:
            await self._start_playwright()
        elif self.use_selenium:
            self._start_selenium()
        else:
            raise RuntimeError("Neither Playwright nor Selenium is available")
    
    async def _start_playwright(self):
        """Start Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with options
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            # Create context with custom settings
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=settings.USER_AGENT,
                accept_downloads=True
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Set default timeout
            self.page.set_default_timeout(settings.BROWSER_TIMEOUT * 1000)
            
            logger.info("Playwright browser started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Playwright: {e}")
            raise
    
    def _start_selenium(self):
        """Start Selenium browser (fallback)"""
        try:
            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'--user-agent={settings.USER_AGENT}')
            options.add_argument('--window-size=1920,1080')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(settings.BROWSER_TIMEOUT)
            
            logger.info("Selenium browser started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Selenium: {e}")
            raise
    
    async def close(self):
        """Close browser instance"""
        if self.use_playwright:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
        elif self.use_selenium and self.driver:
            self.driver.quit()
        
        logger.info("Browser closed")
    
    async def navigate(self, url: str, wait_for: str = None) -> bool:
        """Navigate to URL"""
        try:
            if self.use_playwright and self.page:
                await self.page.goto(url, wait_until='networkidle')
                if wait_for:
                    await self.page.wait_for_selector(wait_for)
                return True
            elif self.use_selenium and self.driver:
                self.driver.get(url)
                if wait_for:
                    WebDriverWait(self.driver, settings.BROWSER_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                    )
                return True
        except Exception as e:
            logger.error(f"Navigation error: {e}")
            return False
    
    async def get_page_content(self) -> str:
        """Get current page content"""
        if self.use_playwright and self.page:
            return await self.page.content()
        elif self.use_selenium and self.driver:
            return self.driver.page_source
        return ""
    
    async def extract_text(self, selector: str) -> str:
        """Extract text from element"""
        try:
            if self.use_playwright and self.page:
                element = await self.page.query_selector(selector)
                if element:
                    return await element.inner_text()
            elif self.use_selenium and self.driver:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                return element.text
        except Exception as e:
            logger.error(f"Extraction error: {e}")
        return ""
    
    async def extract_all_text(self, selector: str) -> List[str]:
        """Extract text from all matching elements"""
        texts = []
        try:
            if self.use_playwright and self.page:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    if text:
                        texts.append(text)
            elif self.use_selenium and self.driver:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text
                    if text:
                        texts.append(text)
        except Exception as e:
            logger.error(f"Extraction error: {e}")
        return texts
    
    async def scroll_page(self, amount: int = 1000):
        """Scroll page down"""
        try:
            if self.use_playwright and self.page:
                await self.page.evaluate(f'window.scrollBy(0, {amount})')
            elif self.use_selenium and self.driver:
                self.driver.execute_script(f'window.scrollBy(0, {amount})')
        except Exception as e:
            logger.error(f"Scroll error: {e}")
    
    async def click(self, selector: str) -> bool:
        """Click element"""
        try:
            if self.use_playwright and self.page:
                await self.page.click(selector)
                return True
            elif self.use_selenium and self.driver:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                element.click()
                return True
        except Exception as e:
            logger.error(f"Click error: {e}")
        return False
    
    async def fill_form(self, selector: str, value: str):
        """Fill form field"""
        try:
            if self.use_playwright and self.page:
                await self.page.fill(selector, value)
            elif self.use_selenium and self.driver:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                element.clear()
                element.send_keys(value)
        except Exception as e:
            logger.error(f"Form fill error: {e}")
    
    async def take_screenshot(self, path: str):
        """Take screenshot"""
        try:
            if self.use_playwright and self.page:
                await self.page.screenshot(path=path, full_page=True)
            elif self.use_selenium and self.driver:
                self.driver.save_screenshot(path)
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
    
    async def research_api_docs(self, api_name: str) -> ResearchResult:
        """Research API documentation"""
        api_urls = {
            "binance": "https://binance-docs.github.io/apidocs/spot/en/",
            "alpha_vantage": "https://www.alphavantage.co/documentation/",
            "openrouter": "https://openrouter.ai/docs",
            "gemini": "https://ai.google.dev/docs",
            "groq": "https://console.groq.com/docs",
            "baseten": "https://docs.baseten.co/",
            "telegram": "https://core.telegram.org/bots/api",
            "reddit": "https://www.reddit.com/dev/api/",
            "finnhub": "https://finnhub.io/docs/api"
        }
        
        url = api_urls.get(api_name.lower())
        if not url:
            raise ValueError(f"Unknown API: {api_name}")
        
        await self.navigate(url)
        
        # Extract main content
        content = await self.get_page_content()
        
        # Get page title
        title = ""
        if self.use_playwright and self.page:
            title = await self.page.title()
        elif self.use_selenium and self.driver:
            title = self.driver.title
        
        return ResearchResult(
            url=url,
            title=title,
            content=content,
            timestamp=datetime.now(),
            metadata={"api_name": api_name}
        )
    
    async def search_google(self, query: str) -> List[Dict[str, str]]:
        """Search Google and return results"""
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        await self.navigate(search_url)
        
        results = []
        
        # Extract search results
        if self.use_playwright and self.page:
            # Wait for results
            await self.page.wait_for_selector('div#search', timeout=10000)
            
            # Extract result elements
            result_elements = await self.page.query_selector_all('div.g')
            
            for element in result_elements[:10]:
                try:
                    title_elem = await element.query_selector('h3')
                    link_elem = await element.query_selector('a')
                    snippet_elem = await element.query_selector('div.VwiC3b')
                    
                    if title_elem and link_elem:
                        title = await title_elem.inner_text()
                        href = await link_elem.get_attribute('href')
                        snippet = await snippet_elem.inner_text() if snippet_elem else ""
                        
                        results.append({
                            "title": title,
                            "url": href,
                            "snippet": snippet
                        })
                except Exception as e:
                    continue
        
        return results
    
    async def get_fear_greed_index(self) -> Dict[str, Any]:
        """Get CNN Fear & Greed Index"""
        url = "https://money.cnn.com/data/fear-and-greed/"
        await self.navigate(url)
        
        result = {"index": 50, "sentiment": "neutral"}
        
        try:
            if self.use_playwright and self.page:
                # Extract index value
                index_elem = await self.page.query_selector('#fearGreedIndex')
                if index_elem:
                    index_text = await index_elem.inner_text()
                    result["index"] = int(index_text.strip())
                    
                    # Determine sentiment
                    if result["index"] > 75:
                        result["sentiment"] = "extreme_greed"
                    elif result["index"] > 55:
                        result["sentiment"] = "greed"
                    elif result["index"] > 45:
                        result["sentiment"] = "neutral"
                    elif result["index"] > 25:
                        result["sentiment"] = "fear"
                    else:
                        result["sentiment"] = "extreme_fear"
        except Exception as e:
            logger.error(f"Error getting fear/greed: {e}")
        
        return result


# Singleton instance
_browser_agent: Optional[BrowserAgent] = None


async def get_browser_agent() -> BrowserAgent:
    """Get or create browser agent singleton"""
    global _browser_agent
    if _browser_agent is None:
        _browser_agent = BrowserAgent()
    return _browser_agent
