
import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_ff")

async def test_forex_factory():
    logger.info("Starting Playwright...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info("Navigating to Forex Factory...")
            # Try to set timezone cookie for IST (GMT+5:30) -> ID 19 in standard forex factory map? 
            # Actually, standard is usually to just let it load and see.
            
            await page.goto("https://www.forexfactory.com/calendar?week=today", timeout=60000)
            title = await page.title()
            logger.info(f"Page Title: {title}")
            
            # extract some events
            events = await page.query_selector_all("tr.calendar_row")
            logger.info(f"Found {len(events)} events")
            
            if len(events) > 0:
                first_event = await events[0].inner_text()
                logger.info(f"First event sample: {first_event[:100]}...")
            
            await browser.close()
            logger.info("Success!")
    except Exception as e:
        logger.error(f"Playwright failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_forex_factory())
