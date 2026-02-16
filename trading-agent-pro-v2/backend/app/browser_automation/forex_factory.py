"""
Forex Factory Calendar Scraper
Scrapes economic calendar from forexfactory.com with IST timezone
"""
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import pytz
import logging
import re

from bs4 import BeautifulSoup

from .system_browser import SystemBrowser

logger = logging.getLogger(__name__)


class ImpactLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class EconomicEvent:
    """Economic calendar event"""
    date: datetime
    time_ist: str
    currency: str
    event_name: str
    impact: ImpactLevel
    actual: Optional[str]
    forecast: Optional[str]
    previous: Optional[str]
    source: str = "forexfactory"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "time_ist": self.time_ist,
            "currency": self.currency,
            "event_name": self.event_name,
            "impact": self.impact.value,
            "actual": self.actual,
            "forecast": self.forecast,
            "previous": self.previous,
            "source": self.source
        }


class ForexFactoryCalendar:
    """
    Forex Factory Economic Calendar Scraper
    Converts all times to IST (Indian Standard Time, UTC+5:30)
    """
    
    BASE_URL = "https://www.forexfactory.com/calendar"
    
    # Timezone conversion
    IST = pytz.timezone('Asia/Kolkata')
    
    def __init__(self):
        self.browser = SystemBrowser(headless=True, timeout=45)
        self.cache: Dict[str, List[EconomicEvent]] = {}
        self.cache_duration = timedelta(minutes=15)
        self.last_update: Optional[datetime] = None
        
    async def __aenter__(self):
        await self.browser.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.browser.close()
    
    async def get_calendar(
        self,
        days: int = 7,
        currencies: Optional[List[str]] = None,
        impact_filter: Optional[List[ImpactLevel]] = None
    ) -> List[EconomicEvent]:
        """
        Get economic calendar events
        
        Args:
            days: Number of days to fetch (default 7)
            currencies: Filter by currencies (e.g., ["USD", "EUR"])
            impact_filter: Filter by impact level
        """
        cache_key = f"calendar_{days}"
        
        # Check cache
        if cache_key in self.cache:
            if self.last_update and (datetime.now() - self.last_update) < self.cache_duration:
                events = self.cache[cache_key]
                return self._filter_events(events, currencies, impact_filter)
        
        try:
            # Navigate to calendar
            success = await self.browser.navigate(self.BASE_URL)
            if not success:
                logger.error("Failed to navigate to Forex Factory")
                return []
            
            # Wait for calendar to load
            await self.browser.wait_for_element("table.calendar__table", timeout=20)
            
            # Get page content
            content = await self.browser.get_page_content()
            
            # Parse events
            events = self._parse_calendar(content)
            
            # Cache results
            self.cache[cache_key] = events
            self.last_update = datetime.now()
            
            # Filter and return
            return self._filter_events(events, currencies, impact_filter)
            
        except Exception as e:
            logger.error(f"Error fetching calendar: {e}")
            return []
    
    def _parse_calendar(self, html: str) -> List[EconomicEvent]:
        """Parse calendar HTML and extract events"""
        events = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', {'class': 'calendar__table'})
            
            if not table:
                logger.warning("Calendar table not found")
                return events
            
            rows = table.find_all('tr', {'class': 'calendar__row'})
            
            current_date = None
            
            for row in rows:
                try:
                    # Check if this is a date row
                    date_cell = row.find('td', {'class': 'calendar__date'})
                    if date_cell:
                        date_text = date_cell.get_text(strip=True)
                        current_date = self._parse_date(date_text)
                        continue
                    
                    # Parse event row
                    time_cell = row.find('td', {'class': 'calendar__time'})
                    currency_cell = row.find('td', {'class': 'calendar__currency'})
                    event_cell = row.find('td', {'class': 'calendar__event'})
                    impact_cell = row.find('td', {'class': 'calendar__impact'})
                    actual_cell = row.find('td', {'class': 'calendar__actual'})
                    forecast_cell = row.find('td', {'class': 'calendar__forecast'})
                    previous_cell = row.find('td', {'class': 'calendar__previous'})
                    
                    if not event_cell:
                        continue
                    
                    # Parse time and convert to IST
                    time_str = time_cell.get_text(strip=True) if time_cell else ""
                    time_ist = self._convert_to_ist(time_str, current_date)
                    
                    # Parse impact
                    impact = self._parse_impact(impact_cell)
                    
                    # Create event
                    event = EconomicEvent(
                        date=current_date or datetime.now(),
                        time_ist=time_ist,
                        currency=currency_cell.get_text(strip=True) if currency_cell else "",
                        event_name=event_cell.get_text(strip=True),
                        impact=impact,
                        actual=actual_cell.get_text(strip=True) if actual_cell else None,
                        forecast=forecast_cell.get_text(strip=True) if forecast_cell else None,
                        previous=previous_cell.get_text(strip=True) if previous_cell else None
                    )
                    
                    events.append(event)
                    
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
            
            logger.info(f"Parsed {len(events)} events from Forex Factory")
            return events
            
        except Exception as e:
            logger.error(f"Error parsing calendar HTML: {e}")
            return events
    
    def _parse_date(self, date_text: str) -> datetime:
        """Parse date text from calendar"""
        try:
            # Forex Factory format: "Mon Jan 15" or "Today" or "Tomorrow"
            today = datetime.now()
            
            if "today" in date_text.lower():
                return today
            
            if "tomorrow" in date_text.lower():
                return today + timedelta(days=1)
            
            # Parse format like "Mon Jan 15"
            match = re.search(r'(\w{3})\s+(\w{3})\s+(\d{1,2})', date_text)
            if match:
                month_str = match.group(2)
                day = int(match.group(3))
                
                month_map = {
                    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                    'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                    'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                }
                
                month = month_map.get(month_str.lower(), today.month)
                year = today.year
                
                # If month is earlier than current month, assume next year
                if month < today.month:
                    year += 1
                
                return datetime(year, month, day)
            
            return today
            
        except Exception as e:
            logger.warning(f"Error parsing date '{date_text}': {e}")
            return datetime.now()
    
    def _convert_to_ist(self, time_str: str, date: datetime) -> str:
        """
        Convert Forex Factory time to IST
        Forex Factory uses ET (Eastern Time, UTC-5 or UTC-4)
        IST is UTC+5:30
        """
        try:
            if not time_str or time_str.lower() in ['tentative', '']:
                return "Tentative"
            
            # Parse time (format: "8:30am" or "2:00pm")
            match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)', time_str.lower())
            if not match:
                return time_str
            
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3)
            
            # Convert to 24-hour format
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            # Create ET datetime (assume EST/EDT based on date)
            et = pytz.timezone('US/Eastern')
            et_time = et.localize(datetime(date.year, date.month, date.day, hour, minute))
            
            # Convert to IST
            ist_time = et_time.astimezone(self.IST)
            
            # Format as string
            return ist_time.strftime("%I:%M %p IST")
            
        except Exception as e:
            logger.warning(f"Error converting time '{time_str}': {e}")
            return time_str
    
    def _parse_impact(self, impact_cell) -> ImpactLevel:
        """Parse impact level from cell"""
        try:
            if not impact_cell:
                return ImpactLevel.NONE
            
            # Find impact icon
            icon = impact_cell.find('span')
            if not icon:
                return ImpactLevel.NONE
            
            icon_class = icon.get('class', [])
            icon_str = ' '.join(icon_class)
            
            if 'high' in icon_str:
                return ImpactLevel.HIGH
            elif 'medium' in icon_str:
                return ImpactLevel.MEDIUM
            elif 'low' in icon_str:
                return ImpactLevel.LOW
            
            return ImpactLevel.NONE
            
        except Exception as e:
            logger.debug(f"Error parsing impact: {e}")
            return ImpactLevel.NONE
    
    def _filter_events(
        self,
        events: List[EconomicEvent],
        currencies: Optional[List[str]],
        impact_filter: Optional[List[ImpactLevel]]
    ) -> List[EconomicEvent]:
        """Filter events by criteria"""
        filtered = events
        
        if currencies:
            filtered = [e for e in filtered if e.currency.upper() in [c.upper() for c in currencies]]
        
        if impact_filter:
            filtered = [e for e in filtered if e.impact in impact_filter]
        
        return filtered
    
    async def get_high_impact_events(self, days: int = 1) -> List[EconomicEvent]:
        """Get only high impact events"""
        return await self.get_calendar(
            days=days,
            impact_filter=[ImpactLevel.HIGH]
        )
    
    async def get_events_for_currency(
        self,
        currency: str,
        days: int = 7
    ) -> List[EconomicEvent]:
        """Get events for specific currency"""
        return await self.get_calendar(
            days=days,
            currencies=[currency]
        )
    
    def get_next_high_impact_event(self) -> Optional[EconomicEvent]:
        """Get the next upcoming high impact event"""
        cache_key = "calendar_7"
        if cache_key not in self.cache:
            return None
        
        now = datetime.now(self.IST)
        
        for event in self.cache[cache_key]:
            if event.impact == ImpactLevel.HIGH:
                # Parse event time
                try:
                    event_time = datetime.strptime(
                        f"{event.date.date()} {event.time_ist.replace(' IST', '')}",
                        "%Y-%m-%d %I:%M %p"
                    )
                    event_time = self.IST.localize(event_time)
                    
                    if event_time > now:
                        return event
                except:
                    continue
        
        return None


# Singleton instance
_calendar_instance: Optional[ForexFactoryCalendar] = None


async def get_calendar() -> ForexFactoryCalendar:
    """Get or create calendar instance"""
    global _calendar_instance
    if _calendar_instance is None:
        _calendar_instance = ForexFactoryCalendar()
    return _calendar_instance
