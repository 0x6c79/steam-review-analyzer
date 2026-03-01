"""
Advanced caching utilities for Streamlit dashboard.
Provides intelligent caching with dependency tracking and cache invalidation.
"""

import streamlit as st
import pandas as pd
import hashlib
import json
from typing import Any, Callable, Optional, Tuple
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class StreamlitCacheManager:
    """
    Manages caching for Streamlit with dependency tracking and invalidation.
    Provides both session-level and persistent caching strategies.
    """
    
    CACHE_PREFIX = "steam_review_cache_"
    
    @staticmethod
    def get_cache_key(namespace: str, **kwargs) -> str:
        """Generate a deterministic cache key from parameters."""
        key_data = {
            'namespace': namespace,
            **kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        hash_key = hashlib.md5(key_str.encode()).hexdigest()
        return f"{StreamlitCacheManager.CACHE_PREFIX}{namespace}_{hash_key}"
    
    @staticmethod
    def cache_data_with_deps(
        ttl: int = 300,
        dependencies: Optional[list] = None
    ) -> Callable:
        """
        Decorator for caching Streamlit session data with dependency tracking.
        
        Args:
            ttl: Time-to-live in seconds
            dependencies: List of cache keys that invalidate this cache if changed
        """
        def decorator(func: Callable) -> Callable:
            @st.cache_data(ttl=ttl)
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                # Check if dependencies are valid
                if dependencies:
                    for dep_key in dependencies:
                        if dep_key not in st.session_state:
                            # Dependency missing, invalidate cache
                            st.session_state[dep_key] = None
                
                result = func(*args, **kwargs)
                
                # Track this cache in session state
                cache_key = StreamlitCacheManager.get_cache_key(func.__name__, *args, **kwargs)
                st.session_state[cache_key] = result
                
                return result
            
            return wrapper
        return decorator
    
    @staticmethod
    def invalidate_cache(pattern: Optional[str] = None) -> None:
        """
        Invalidate cached items matching a pattern.
        
        Args:
            pattern: Prefix pattern to match (e.g., "steam_review_cache_reviews_")
        """
        if pattern is None:
            # Clear all caches
            keys_to_delete = [
                k for k in st.session_state.keys()
                if isinstance(k, str) and k.startswith(StreamlitCacheManager.CACHE_PREFIX)
            ]
        else:
            keys_to_delete = [
                k for k in st.session_state.keys()
                if isinstance(k, str) and k.startswith(pattern)
            ]
        
        for key in keys_to_delete:
            del st.session_state[key]
            logger.info(f"Invalidated cache: {key}")
    
    @staticmethod
    def get_cached(namespace: str, **kwargs) -> Optional[Any]:
        """Get a cached value if it exists."""
        cache_key = StreamlitCacheManager.get_cache_key(namespace, **kwargs)
        return st.session_state.get(cache_key)
    
    @staticmethod
    def set_cached(namespace: str, value: Any, **kwargs) -> str:
        """Store a value in cache and return the cache key."""
        cache_key = StreamlitCacheManager.get_cache_key(namespace, **kwargs)
        st.session_state[cache_key] = value
        return cache_key


class DataFrameCacheManager:
    """Specialized caching for DataFrames with memory efficiency."""
    
    @staticmethod
    @st.cache_data(ttl=300)
    def cache_reviews_data(
        app_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_playtime: Optional[float] = None,
        max_playtime: Optional[float] = None,
        language: Optional[str] = None,
        limit: int = 5000
    ) -> pd.DataFrame:
        """
        Cached loading of review data with filtering options.
        This function itself is cached by Streamlit, avoiding redundant DB calls.
        """
        from src.steam_review.storage.database import get_database
        
        db = get_database()
        df = db.get_reviews(
            app_id=app_id,
            limit=limit,
            start_date=start_date,
            end_date=end_date,
            min_playtime=min_playtime,
            max_playtime=max_playtime,
            language=language
        )
        return df
    
    @staticmethod
    @st.cache_data(ttl=300)
    def cache_stats_data(
        app_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict:
        """Cached loading of review statistics."""
        from src.steam_review.storage.database import get_database
        
        db = get_database()
        return db.get_stats(app_id=app_id, start_date=start_date, end_date=end_date)
    
    @staticmethod
    @st.cache_data(ttl=3600)
    def cache_metadata(app_id: Optional[str] = None) -> dict:
        """
        Cached metadata including available filters.
        Uses longer TTL as metadata changes less frequently.
        """
        from src.steam_review.storage.database import get_database
        
        db = get_database()
        return {
            'languages': db.get_available_languages(app_id),
            'date_range': db.get_date_range(app_id),
            'playtime_range': db.get_playtime_range(app_id)
        }
    
    @staticmethod
    def get_filtered_data(
        app_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_playtime: Optional[float] = None,
        max_playtime: Optional[float] = None,
        language: Optional[str] = None,
        limit: int = 5000
    ) -> pd.DataFrame:
        """
        Get filtered review data, leveraging caching.
        Handles cache invalidation based on filter changes.
        """
        # Create a cache key based on filters
        cache_key = f"reviews_{app_id}_{start_date}_{end_date}_{min_playtime}_{max_playtime}_{language}_{limit}"
        
        # Check if we have it in session state
        if cache_key in st.session_state:
            logger.info(f"Using cached data for key: {cache_key}")
            return st.session_state[cache_key]
        
        # Load from database with caching
        df = DataFrameCacheManager.cache_reviews_data(
            app_id=app_id,
            start_date=start_date,
            end_date=end_date,
            min_playtime=min_playtime,
            max_playtime=max_playtime,
            language=language,
            limit=limit
        )
        
        # Store in session state for fast retrieval
        st.session_state[cache_key] = df
        return df


class CacheConfig:
    """Configuration for cache behavior."""
    
    # Cache TTL settings (in seconds)
    TTL_SHORT = 60  # For frequently changing data
    TTL_MEDIUM = 300  # For general data (default)
    TTL_LONG = 3600  # For metadata that rarely changes
    
    # Memory optimization
    MAX_CACHED_DATAFRAMES = 5  # Maximum number of DataFrames to keep in cache
    
    @staticmethod
    def get_ttl_for_data_type(data_type: str) -> int:
        """Get appropriate TTL based on data type."""
        ttl_map = {
            'reviews': CacheConfig.TTL_MEDIUM,
            'stats': CacheConfig.TTL_MEDIUM,
            'metadata': CacheConfig.TTL_LONG,
            'analysis': CacheConfig.TTL_MEDIUM,
            'export': CacheConfig.TTL_SHORT,
        }
        return ttl_map.get(data_type, CacheConfig.TTL_MEDIUM)


def init_cache_session_state() -> None:
    """Initialize session state for cache management."""
    if 'cache_initialized' not in st.session_state:
        st.session_state.cache_initialized = True
        st.session_state.last_cache_clear = None
        logger.info("Initialized cache session state")
