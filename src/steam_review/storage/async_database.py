"""
Asynchronous database operations for handling large datasets efficiently.
Provides async-aware data loading and processing capabilities.
"""

import asyncio
import sys
import os
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any

project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.steam_review.storage.database import ReviewDatabase

logger = logging.getLogger(__name__)


class AsyncReviewDatabase:
    """Wrapper for ReviewDatabase with async operations."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db = ReviewDatabase(db_path)
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    async def get_reviews_async(
        self, 
        app_id: Optional[str] = None, 
        limit: Optional[int] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
        min_playtime: Optional[float] = None,
        max_playtime: Optional[float] = None,
        language: Optional[str] = None,
        sentiment_min: Optional[float] = None,
        sentiment_max: Optional[float] = None,
        voted_up_only: Optional[bool] = None
    ) -> pd.DataFrame:
        """
        Asynchronously load reviews with filtering.
        Runs database query in thread pool to avoid blocking event loop.
        """
        loop = asyncio.get_event_loop()
        df = await loop.run_in_executor(
            self._executor,
            self.db.get_reviews,
            app_id, limit, start_date, end_date, 
            min_playtime, max_playtime, language, 
            sentiment_min, sentiment_max, voted_up_only
        )
        return df
    
    async def get_stats_async(
        self,
        app_id: Optional[str] = None,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None
    ) -> Dict[str, int]:
        """Asynchronously get statistics with optional filtering."""
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(
            self._executor,
            self.db.get_stats,
            app_id, start_date, end_date
        )
        return stats
    
    async def get_available_languages_async(self, app_id: Optional[str] = None) -> List[str]:
        """Asynchronously get list of unique languages."""
        loop = asyncio.get_event_loop()
        languages = await loop.run_in_executor(
            self._executor,
            self.db.get_available_languages,
            app_id
        )
        return languages
    
    async def get_date_range_async(self, app_id: Optional[str] = None) -> Dict[str, Any]:
        """Asynchronously get date range."""
        loop = asyncio.get_event_loop()
        date_range = await loop.run_in_executor(
            self._executor,
            self.db.get_date_range,
            app_id
        )
        return date_range
    
    async def get_playtime_range_async(self, app_id: Optional[str] = None) -> Dict[str, float]:
        """Asynchronously get playtime range."""
        loop = asyncio.get_event_loop()
        playtime_range = await loop.run_in_executor(
            self._executor,
            self.db.get_playtime_range,
            app_id
        )
        return playtime_range
    
    async def batch_get_reviews(
        self,
        app_ids: List[str],
        limit: Optional[int] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Asynchronously fetch reviews for multiple app IDs in parallel.
        Returns dictionary mapping app_id to DataFrame.
        """
        tasks = [
            self.get_reviews_async(app_id=app_id, limit=limit)
            for app_id in app_ids
        ]
        results = await asyncio.gather(*tasks)
        return {app_id: df for app_id, df in zip(app_ids, results)}
    
    async def export_to_csv_async(self, csv_path: str, app_id: Optional[str] = None) -> None:
        """Asynchronously export reviews to CSV."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self.db.export_to_csv,
            csv_path, app_id
        )
    
    async def export_to_excel_async(self, excel_path: str, app_id: Optional[str] = None) -> None:
        """Asynchronously export reviews to Excel."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self.db.export_to_excel,
            excel_path, app_id
        )
    
    async def export_to_json_async(self, json_path: str, app_id: Optional[str] = None) -> None:
        """Asynchronously export reviews to JSON."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self.db.export_to_json,
            json_path, app_id
        )
    
    def shutdown(self) -> None:
        """Clean up thread pool executor."""
        self._executor.shutdown(wait=True)


def get_async_database(db_path: Optional[str] = None) -> AsyncReviewDatabase:
    """Get an instance of AsyncReviewDatabase."""
    return AsyncReviewDatabase(db_path)
