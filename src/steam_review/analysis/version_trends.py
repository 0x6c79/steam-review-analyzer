"""
Game Version/Update Impact Analysis Module

Analyzes how game updates and version changes impact review sentiment and topics.
Detects version mentions in reviews and tracks sentiment trends around update dates.
"""

import sys
import os
import re
import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np

# Setup path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.steam_review import config

config.setup_logging()
logger = logging.getLogger(__name__)


class VersionTrendAnalyzer:
    """
    Analyzes game version impacts on review sentiment and key issues.
    Detects version mentions in review text and correlates with sentiment trends.
    """

    # Common version patterns
    VERSION_PATTERNS = [
        r'v?(\d+\.\d+\.\d+)',                    # v1.2.3 or 1.2.3
        r'version\s+(\d+\.\d+)',                 # version 1.2
        r'update\s+(\d+\.\d+)',                  # update 1.5
        r'patch\s+(\d+\.\d+)',                   # patch 2.0
        r'build\s+(\d+)',                        # build 12345
        r'release\s+(\d{1,2}\.\d{1,2})',        # release 1.5
        r'(?:patch|update|hotfix).*?(\d+\.\d+)', # patch/update 1.2
    ]

    # Update keywords to detect version mentions
    UPDATE_KEYWORDS = {
        'english': [
            'update', 'patch', 'version', 'release', 'build', 'hotfix',
            'improvement', 'fix', 'added', 'fixed', 'new features', 'changelog'
        ],
        'chinese': [
            '更新', '补丁', '版本', '发布', '构建', '修复', '改进',
            '新增', '已修复', '功能', '日志', '版本更新'
        ]
    }

    def __init__(self):
        """Initialize the version trend analyzer."""
        self.detected_versions = {}
        self.version_sentiment_map = {}

    def detect_versions(self, reviews_df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Detect version mentions in review text.

        Args:
            reviews_df: DataFrame containing review text and metadata

        Returns:
            Dictionary mapping review IDs to detected versions
        """
        detected = {}

        for idx, row in reviews_df.iterrows():
            review_text = str(row.get('review', ''))
            if not review_text or review_text.lower() == 'nan':
                continue

            versions = set()

            # Try all version patterns
            for pattern in self.VERSION_PATTERNS:
                matches = re.findall(pattern, review_text, re.IGNORECASE)
                versions.update(matches)

            # Check for update keywords combined with version-like patterns
            text_lower = review_text.lower()
            for keyword in self.UPDATE_KEYWORDS.get('english', []):
                if keyword in text_lower:
                    # Find version numbers near keywords
                    keyword_pos = text_lower.find(keyword)
                    context = review_text[max(0, keyword_pos - 50):min(len(review_text), keyword_pos + 100)]
                    version_match = re.search(r'\d+\.\d+', context)
                    if version_match:
                        versions.add(version_match.group())

            if versions:
                detected[idx] = list(versions)

        self.detected_versions = detected
        return detected

    def analyze_sentiment_by_version(self, reviews_df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Calculate sentiment metrics for each detected version.

        Args:
            reviews_df: DataFrame with 'voted_up' and version detections

        Returns:
            Dictionary with version -> sentiment metrics
        """
        version_stats = {}

        for idx, versions in self.detected_versions.items():
            if idx >= len(reviews_df):
                continue

            row = reviews_df.iloc[idx]
            is_positive = bool(row.get('voted_up', False))

            for version in versions:
                if version not in version_stats:
                    version_stats[version] = {
                        'positive': 0,
                        'negative': 0,
                        'total': 0,
                        'review_indices': []
                    }

                version_stats[version]['total'] += 1
                if is_positive:
                    version_stats[version]['positive'] += 1
                else:
                    version_stats[version]['negative'] += 1
                version_stats[version]['review_indices'].append(idx)

        # Calculate satisfaction rates
        for version in version_stats:
            stats = version_stats[version]
            stats['satisfaction_rate'] = (
                stats['positive'] / stats['total'] * 100
                if stats['total'] > 0 else 0
            )

        self.version_sentiment_map = version_stats
        return version_stats

    def detect_update_impacts(
        self, 
        reviews_df: pd.DataFrame, 
        window_days: int = 7
    ) -> Dict[str, Dict]:
        """
        Detect sentiment changes before/after detected updates.

        Args:
            reviews_df: DataFrame with timestamp and sentiment
            window_days: Days before/after update to analyze

        Returns:
            Dictionary with update impact analysis
        """
        if 'timestamp_created' not in reviews_df.columns:
            logger.warning("No timestamp column found for update impact analysis")
            return {}

        impacts = {}

        # Get reviews with timestamps
        df = reviews_df.copy()
        df['date'] = pd.to_datetime(df['timestamp_created'], unit='s', errors='coerce')
        df = df.dropna(subset=['date'])

        # Group reviews with versions by date
        for idx, versions in self.detected_versions.items():
            if idx >= len(df):
                continue

            review_row = df.iloc[idx]
            review_date = review_row['date']

            for version in versions:
                if version not in impacts:
                    impacts[version] = {
                        'detected_dates': [],
                        'before_sentiment': [],
                        'after_sentiment': [],
                        'review_date': None
                    }

                impacts[version]['detected_dates'].append(review_date)

                # Get sentiment before and after window
                before_start = review_date - timedelta(days=window_days)
                after_end = review_date + timedelta(days=window_days)

                before_reviews = df[
                    (df['date'] >= before_start) & (df['date'] < review_date)
                ]['voted_up'].tolist()

                after_reviews = df[
                    (df['date'] > review_date) & (df['date'] <= after_end)
                ]['voted_up'].tolist()

                if before_reviews:
                    before_rate = sum(before_reviews) / len(before_reviews) * 100
                    impacts[version]['before_sentiment'].append(before_rate)

                if after_reviews:
                    after_rate = sum(after_reviews) / len(after_reviews) * 100
                    impacts[version]['after_sentiment'].append(after_rate)

        # Calculate impact metrics
        for version in impacts:
            data = impacts[version]
            before_avg = np.mean(data['before_sentiment']) if data['before_sentiment'] else None
            after_avg = np.mean(data['after_sentiment']) if data['after_sentiment'] else None

            data['before_avg'] = before_avg
            data['after_avg'] = after_avg
            data['impact'] = (after_avg - before_avg) if (before_avg and after_avg) else None

        return impacts

    def extract_version_context_keywords(
        self, 
        reviews_df: pd.DataFrame,
        top_n: int = 10
    ) -> Dict[str, Dict[str, List[Tuple]]]:
        """
        Extract common keywords mentioned with specific versions.

        Args:
            reviews_df: DataFrame with review text
            top_n: Number of top keywords to extract

        Returns:
            Dictionary mapping versions to top keywords
        """
        from src.steam_review.analysis.keyword_extractor import KeywordAndTopicExtractor

        version_keywords = {}
        extractor = KeywordAndTopicExtractor()

        for version in self.detected_versions.values():
            if not version:
                continue

            # Get all reviews mentioning this version
            version_reviews = []
            for idx_list in [self.detected_versions[i] for i in self.detected_versions if version[0] in self.detected_versions.get(i, [])]:
                if idx_list:
                    version_reviews.append(reviews_df.iloc[list(self.detected_versions.keys())[0]]['review'])

            if version_reviews:
                combined_text = ' '.join(str(r) for r in version_reviews if r and str(r).lower() != 'nan')
                keywords = extractor.extract_keywords(combined_text, top_n)
                version_keywords[version[0]] = keywords

        return version_keywords

    def get_version_sentiment_summary(self) -> pd.DataFrame:
        """
        Get a summary DataFrame of version sentiment metrics.

        Returns:
            DataFrame with version analysis summary
        """
        if not self.version_sentiment_map:
            return pd.DataFrame()

        summary_data = []
        for version, stats in self.version_sentiment_map.items():
            summary_data.append({
                'version': version,
                'total_mentions': stats['total'],
                'positive_count': stats['positive'],
                'negative_count': stats['negative'],
                'satisfaction_rate': round(stats['satisfaction_rate'], 2),
                'sample_size': len(stats['review_indices'])
            })

        return pd.DataFrame(summary_data).sort_values('satisfaction_rate', ascending=False)

    def get_trending_versions(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get most frequently mentioned versions.

        Args:
            limit: Maximum number of versions to return

        Returns:
            List of (version, count) tuples sorted by frequency
        """
        version_counts = Counter()
        for versions in self.detected_versions.values():
            version_counts.update(versions)

        return version_counts.most_common(limit)

    def analyze_version_over_time(
        self, 
        reviews_df: pd.DataFrame,
        time_unit: str = 'W'
    ) -> Dict[str, pd.DataFrame]:
        """
        Analyze sentiment trends for top versions over time.

        Args:
            reviews_df: DataFrame with timestamp
            time_unit: Pandas resampling unit ('D', 'W', 'M')

        Returns:
            Dictionary mapping versions to time-series sentiment data
        """
        if 'timestamp_created' not in reviews_df.columns:
            return {}

        df = reviews_df.copy()
        df['date'] = pd.to_datetime(df['timestamp_created'], unit='s', errors='coerce')
        df = df.dropna(subset=['date']).set_index('date')

        version_trends = {}

        # Analyze top 5 versions
        top_versions = [v for v, _ in self.get_trending_versions(5)]

        for version in top_versions:
            # Get indices of reviews mentioning this version
            version_indices = [
                i for i, versions in self.detected_versions.items()
                if version in versions and i < len(df)
            ]

            if not version_indices:
                continue

            # Get sentiment for these reviews over time
            version_df = df.iloc[version_indices].copy()
            if len(version_df) > 0:
                trend = version_df['voted_up'].resample(time_unit).agg(['sum', 'count'])
                trend['satisfaction_rate'] = (trend['sum'] / trend['count'] * 100).fillna(0)
                version_trends[version] = trend

        return version_trends


def analyze_game_versions(reviews_df: pd.DataFrame) -> Tuple[VersionTrendAnalyzer, Dict]:
    """
    Run full version analysis on review data.

    Args:
        reviews_df: DataFrame with reviews

    Returns:
        Tuple of (analyzer object, summary dictionary)
    """
    analyzer = VersionTrendAnalyzer()

    # Run all analyses
    analyzer.detect_versions(reviews_df)
    sentiment_by_version = analyzer.analyze_sentiment_by_version(reviews_df)
    update_impacts = analyzer.detect_update_impacts(reviews_df)
    version_summary = analyzer.get_version_sentiment_summary()

    summary = {
        'analyzer': analyzer,
        'sentiment_by_version': sentiment_by_version,
        'update_impacts': update_impacts,
        'version_summary': version_summary,
        'trending_versions': analyzer.get_trending_versions(),
        'version_over_time': analyzer.analyze_version_over_time(reviews_df)
    }

    return analyzer, summary


if __name__ == "__main__":
    # Example usage
    logger.info("Version Trends Analysis Module")
