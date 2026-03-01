"""
Startup optimization and caching system for analysis results.
Prevents redundant re-analysis on every dashboard reload.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


class AnalysisCache:
    """
    Cache system for analysis results with validation and expiration.
    Prevents re-running expensive analysis operations unnecessarily.
    """
    
    CACHE_VERSION = "1.0"
    
    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), '.cache')
        
        self.cache_dir = cache_dir
        self.metadata_file = os.path.join(cache_dir, 'analysis_metadata.json')
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_file_hash(self, file_path: str) -> str:
        """
        Compute MD5 hash of a file to detect changes.
        
        Args:
            file_path: Path to file
        
        Returns:
            MD5 hash string
        """
        md5_hash = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except FileNotFoundError:
            return None
    
    def load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache metadata: {e}")
                return {}
        return {}
    
    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """Save cache metadata."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
        except IOError as e:
            logger.warning(f"Failed to save cache metadata: {e}")
    
    def is_cache_valid(
        self,
        csv_file: str,
        plots_dir: str,
        max_age_hours: int = 24
    ) -> bool:
        """
        Check if cached analysis is still valid.
        
        Args:
            csv_file: Path to CSV file
            plots_dir: Path to plots directory
            max_age_hours: Maximum age in hours before re-analysis
        
        Returns:
            True if cache is valid, False otherwise
        """
        metadata = self.load_metadata()
        
        # Check if CSV file changed
        csv_hash = self.get_file_hash(csv_file)
        cached_hash = metadata.get('csv_file_hash')
        
        if csv_hash != cached_hash:
            logger.info("CSV file changed, cache invalidated")
            return False
        
        # Check cache age
        cached_time = metadata.get('last_analysis_time')
        if cached_time:
            try:
                cached_datetime = datetime.fromisoformat(cached_time)
                age = datetime.now() - cached_datetime
                
                if age > timedelta(hours=max_age_hours):
                    logger.info(f"Cache expired (age: {age})")
                    return False
            except ValueError:
                logger.warning("Invalid cached timestamp")
                return False
        
        # Check if required plot files exist
        prefix = os.path.basename(csv_file).replace('.csv', '')
        required_plots = metadata.get('generated_plots', [])
        
        for plot_file in required_plots:
            plot_path = os.path.join(plots_dir, plot_file)
            if not os.path.exists(plot_path):
                logger.info(f"Missing plot file: {plot_file}")
                return False
        
        logger.info("Cache is valid")
        return True
    
    def record_analysis(
        self,
        csv_file: str,
        plots_dir: str,
        generated_plots: list
    ) -> None:
        """
        Record successful analysis in cache metadata.
        
        Args:
            csv_file: Path to CSV file
            plots_dir: Path to plots directory
            generated_plots: List of generated plot filenames
        """
        metadata = {
            'version': self.CACHE_VERSION,
            'last_analysis_time': datetime.now().isoformat(),
            'csv_file': csv_file,
            'csv_file_hash': self.get_file_hash(csv_file),
            'plots_directory': plots_dir,
            'generated_plots': generated_plots,
            'plot_count': len(generated_plots),
        }
        
        self.save_metadata(metadata)
        logger.info(f"Recorded analysis: {len(generated_plots)} plots")
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        try:
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            logger.info("Cache cleared")
        except IOError as e:
            logger.warning(f"Failed to clear cache: {e}")


class StartupOptimizer:
    """
    Optimizes dashboard startup by skipping unnecessary analysis.
    """
    
    def __init__(self, enable_cache: bool = True):
        self.cache_enabled = enable_cache
        self.cache = AnalysisCache() if enable_cache else None
    
    def should_run_analysis(
        self,
        csv_file: str,
        plots_dir: str,
        force: bool = False
    ) -> bool:
        """
        Determine if analysis should run.
        
        Args:
            csv_file: Path to CSV file
            plots_dir: Path to plots directory
            force: Force analysis regardless of cache
        
        Returns:
            True if analysis should run, False otherwise
        """
        if force:
            logger.info("Force re-analysis requested")
            return True
        
        if not self.cache_enabled:
            return True
        
        # Check if CSV file exists
        if not os.path.exists(csv_file):
            logger.warning(f"CSV file not found: {csv_file}")
            return False
        
        # Get plot prefix
        prefix = os.path.basename(csv_file).replace('.csv', '')
        
        # Check if any plots exist for this dataset
        if os.path.exists(plots_dir):
            existing_plots = [
                f for f in os.listdir(plots_dir)
                if prefix in f and f.endswith('.png')
            ]
            
            if existing_plots:
                # Plots exist, check cache validity
                return not self.cache.is_cache_valid(csv_file, plots_dir)
        
        # No plots found
        logger.info("No existing plots found, analysis needed")
        return True
    
    def record_successful_analysis(
        self,
        csv_file: str,
        plots_dir: str
    ) -> None:
        """
        Record successful analysis completion.
        
        Args:
            csv_file: Path to CSV file
            plots_dir: Path to plots directory
        """
        if not self.cache_enabled:
            return
        
        prefix = os.path.basename(csv_file).replace('.csv', '')
        
        if os.path.exists(plots_dir):
            generated_plots = [
                f for f in os.listdir(plots_dir)
                if prefix in f and f.endswith('.png')
            ]
            
            self.cache.record_analysis(csv_file, plots_dir, generated_plots)


class LazyAnalysisLoader:
    """
    Lazy loader for analysis results to speed up initial dashboard load.
    Loads analysis plots only when needed.
    """
    
    def __init__(self, plots_dir: str):
        self.plots_dir = plots_dir
        self._loaded_plots = {}
    
    def load_plot(self, plot_name: str) -> Optional[str]:
        """
        Lazily load a plot file.
        
        Args:
            plot_name: Name of plot file (without directory)
        
        Returns:
            Path to plot file if exists, None otherwise
        """
        plot_path = os.path.join(self.plots_dir, plot_name)
        
        if os.path.exists(plot_path):
            self._loaded_plots[plot_name] = plot_path
            return plot_path
        
        return None
    
    def get_available_plots(self, prefix: str) -> list:
        """
        Get list of available plots for a dataset.
        
        Args:
            prefix: Dataset prefix (filename without extension)
        
        Returns:
            List of available plot filenames
        """
        if not os.path.exists(self.plots_dir):
            return []
        
        available = [
            f for f in os.listdir(self.plots_dir)
            if prefix in f and f.endswith('.png')
        ]
        
        return sorted(available)


class DashboardStartupConfig:
    """Configuration for dashboard startup behavior."""
    
    def __init__(self):
        self.enable_analysis_cache = True
        self.enable_lazy_loading = True
        self.auto_analysis_enabled = False  # Disabled by default
        self.cache_max_age_hours = 24
        self.show_startup_info = True
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'enable_analysis_cache': self.enable_analysis_cache,
            'enable_lazy_loading': self.enable_lazy_loading,
            'auto_analysis_enabled': self.auto_analysis_enabled,
            'cache_max_age_hours': self.cache_max_age_hours,
            'show_startup_info': self.show_startup_info,
        }


# Global instances
_startup_optimizer = None
_lazy_loader = None


def get_startup_optimizer(enable_cache: bool = True) -> StartupOptimizer:
    """Get or create startup optimizer instance."""
    global _startup_optimizer
    if _startup_optimizer is None:
        _startup_optimizer = StartupOptimizer(enable_cache=enable_cache)
    return _startup_optimizer


def get_lazy_loader(plots_dir: str) -> LazyAnalysisLoader:
    """Get or create lazy analysis loader instance."""
    global _lazy_loader
    if _lazy_loader is None:
        _lazy_loader = LazyAnalysisLoader(plots_dir)
    return _lazy_loader
