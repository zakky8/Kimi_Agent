"""
System Browser Automation
Uses locally installed Chrome/Edge/Firefox without requiring APIs
"""
import asyncio
import subprocess
import platform
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import logging
import json
import tempfile
import shutil

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeout
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


@dataclass
class BrowserSession:
    """Browser session data"""
    session_id: str
    browser_type: str
    page_count: int
    created_at: datetime
    user_data_dir: Optional[str] = None


@dataclass
class ScrapedData:
    """Scraped web data"""
    url: str
    title: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]


class SystemBrowser:
    """
    System Browser Automation using locally installed browsers
    Supports Chrome, Edge, Firefox - no API keys required
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.sessions: Dict[str, BrowserSession] = {}
        self._user_data_dir: Optional[str] = None
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        
    async def start(self, browser_type: str = "chrome") -> bool:
        """
        Start browser automation
        
        Args:
            browser_type: "chrome", "edge", "firefox"
        """
        try:
            self.playwright = await async_playwright().start()
            
            # Detect system browser
            browser_path = self._detect_browser(browser_type)
            
            # Create temporary user data directory
            self._user_data_dir = tempfile.mkdtemp(prefix="trading_agent_browser_")
            
            # Launch browser with system executable
            if browser_type == "chrome" or browser_type == "edge":
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    executable_path=browser_path,
                    args=[
                        f"--user-data-dir={self._user_data_dir}",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-web-security",
                        "--disable-features=IsolateOrigins,site-per-process",
                    ]
                )
            elif browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(
                    headless=self.headless
                )
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=self._get_realistic_user_agent(),
                locale="en-US",
                timezone_id="Asia/Kolkata",  # IST
                permissions=["geolocation"],
            )
            
            # Add stealth scripts
            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                window.chrome = { runtime: {} };
            """)
            
            self.page = await self.context.new_page()
            
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.sessions[session_id] = BrowserSession(
                session_id=session_id,
                browser_type=browser_type,
                page_count=1,
                created_at=datetime.now(),
                user_data_dir=self._user_data_dir
            )
            
            logger.info(f"Browser started: {browser_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return False
    
    def _detect_browser(self, browser_type: str) -> Optional[str]:
        """Detect system browser executable path"""
        system = platform.system()
        
        if system == "Windows":
            paths = {
                "chrome": [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
                ],
                "edge": [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                ],
                "firefox": [
                    r"C:\Program Files\Mozilla Firefox\firefox.exe",
                    r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
                ]
            }
        elif system == "Darwin":  # macOS
            paths = {
                "chrome": [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                ],
                "edge": [
                    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                ],
                "firefox": [
                    "/Applications/Firefox.app/Contents/MacOS/firefox",
                    "~/Applications/Firefox.app/Contents/MacOS/firefox",
                ]
            }
        else:  # Linux
            paths = {
                "chrome": [
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable",
                    "/usr/bin/chromium",
                    "/usr/bin/chromium-browser",
                ],
                "edge": [
                    "/usr/bin/microsoft-edge",
                    "/usr/bin/microsoft-edge-stable",
                ],
                "firefox": [
                    "/usr/bin/firefox",
                    "/usr/lib/firefox/firefox",
                ]
            }
        
        for path in paths.get(browser_type, []):
            expanded_path = Path(path).expanduser()
            if expanded_path.exists():
                return str(expanded_path)
        
        # Try to find using which command on Unix
        if system != "Windows":
            try:
                result = subprocess.run(
                    ["which", browser_type],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
        
        logger.warning(f"Could not detect {browser_type}, using default")
        return None
    
    def _get_realistic_user_agent(self) -> str:
        """Get realistic user agent string"""
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    async def navigate(self, url: str, wait_for: str = "networkidle") -> bool:
        """Navigate to URL"""
        if not self.page:
            logger.error("Browser not started")
            return False
        
        try:
            await self.page.goto(url, wait_until=wait_for, timeout=self.timeout * 1000)
            logger.info(f"Navigated to: {url}")
            return True
        except PlaywrightTimeout:
            logger.warning(f"Timeout navigating to {url}")
            return False
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False
    
    async def get_page_content(self) -> str:
        """Get full page content"""
        if not self.page:
            return ""
        try:
            return await self.page.content()
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            return ""
    
    async def extract_text(self, selector: str) -> str:
        """Extract text from element"""
        if not self.page:
            return ""
        try:
            element = await self.page.query_selector(selector)
            if element:
                return await element.inner_text()
            return ""
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    async def extract_table(self, selector: str) -> List[Dict[str, str]]:
        """Extract data from HTML table"""
        if not self.page:
            return []
        
        try:
            table = await self.page.query_selector(selector)
            if not table:
                return []
            
            rows = await table.query_selector_all("tr")
            data = []
            
            for row in rows:
                cells = await row.query_selector_all("td, th")
                row_data = {}
                for i, cell in enumerate(cells):
                    text = await cell.inner_text()
                    row_data[f"col_{i}"] = text.strip()
                if row_data:
                    data.append(row_data)
            
            return data
        except Exception as e:
            logger.error(f"Error extracting table: {e}")
            return []
    
    async def click(self, selector: str) -> bool:
        """Click on element"""
        if not self.page:
            return False
        try:
            await self.page.click(selector, timeout=5000)
            return True
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return False
    
    async def fill_input(self, selector: str, text: str) -> bool:
        """Fill input field"""
        if not self.page:
            return False
        try:
            await self.page.fill(selector, text)
            return True
        except Exception as e:
            logger.error(f"Error filling input: {e}")
            return False
    
    async def scroll_to_bottom(self) -> bool:
        """Scroll to bottom of page"""
        if not self.page:
            return False
        try:
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
            return False
    
    async def wait_for_element(self, selector: str, timeout: int = 10) -> bool:
        """Wait for element to appear"""
        if not self.page:
            return False
        try:
            await self.page.wait_for_selector(selector, timeout=timeout * 1000)
            return True
        except:
            return False
    
    async def take_screenshot(self, path: Optional[str] = None) -> Optional[bytes]:
        """Take screenshot"""
        if not self.page:
            return None
        try:
            if path:
                await self.page.screenshot(path=path, full_page=True)
                return None
            else:
                return await self.page.screenshot(full_page=True)
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript on page"""
        if not self.page:
            return None
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return None
    
    async def close(self):
        """Close browser and cleanup"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            # Cleanup user data directory
            if self._user_data_dir and Path(self._user_data_dir).exists():
                shutil.rmtree(self._user_data_dir, ignore_errors=True)
            
            logger.info("Browser closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    # ==================== Selenium Fallback ====================
    
    def start_selenium(self, browser_type: str = "chrome") -> bool:
        """Start Selenium browser as fallback"""
        try:
            options = uc.ChromeOptions()
            
            if self.headless:
                options.add_argument("--headless")
            
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--window-size=1920,1080")
            options.add_argument(f"--user-agent={self._get_realistic_user_agent()}")
            
            self.selenium_driver = uc.Chrome(options=options)
            self.selenium_driver.set_page_load_timeout(self.timeout)
            
            logger.info("Selenium browser started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Selenium: {e}")
            return False
    
    def selenium_navigate(self, url: str) -> bool:
        """Navigate using Selenium"""
        try:
            self.selenium_driver.get(url)
            return True
        except Exception as e:
            logger.error(f"Selenium navigation error: {e}")
            return False
    
    def selenium_close(self):
        """Close Selenium browser"""
        try:
            if hasattr(self, 'selenium_driver'):
                self.selenium_driver.quit()
        except:
            pass


# Singleton instance
_browser_instance: Optional[SystemBrowser] = None


async def get_browser(headless: bool = True) -> SystemBrowser:
    """Get or create browser instance"""
    global _browser_instance
    if _browser_instance is None:
        _browser_instance = SystemBrowser(headless=headless)
        await _browser_instance.start()
    return _browser_instance


async def close_browser():
    """Close global browser instance"""
    global _browser_instance
    if _browser_instance:
        await _browser_instance.close()
        _browser_instance = None
