from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import logging

class Event:
    def __init__(self, title: str, date: str, venue: str, price: str, url: str, source: str, ticket_status: str = "Available", category: str = "General"):
        self.title = title
        self.date = date
        self.venue = venue
        self.price = price
        self.url = url
        self.source = source
        self.ticket_status = ticket_status
        self.category = category

    def __repr__(self):
        return f"<Event {self.title} @ {self.venue}>"

class BaseScraper(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"scraper.{name}")

    @abstractmethod
    async def fetch_events(self) -> List[Event]:
        """
        Fetches events from the source.
        Returns a list of Event objects.
        """
        pass

    async def setup(self):
        """
        Optional setup method (e.g., launching browser).
        """
        pass

    async def teardown(self):
        """
        Optional teardown method (e.g., closing browser).
        """
        pass
