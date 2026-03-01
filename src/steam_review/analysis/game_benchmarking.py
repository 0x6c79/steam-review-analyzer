"""
Multi-Dimensional Game Benchmarking Module

Compares games across multiple dimensions to provide comprehensive benchmarking insights.
Supports side-by-side comparison of sentiment, quality, issues, and player satisfaction metrics.
"""

import sys
import os
import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

# Setup path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.steam_review import config
from src.steam_review.analysis.advanced_analyzer import AdvancedReviewAnalyzer
from src.steam_review.analysis.keyword_extractor import KeywordAndTopicExtractor

config.setup_logging()
logger = logging.getLogger(__name__)


class GameBenchmark:
    """
    Benchmarks and compares games across multiple dimensions.
    Provides standardized metrics for fair game comparison.
    """

    # Dimensions for comparison
    BENCHMARK_DIMENSIONS = [
        'positive_rate',
        'avg_quality_score',
        'issue_diversity',
        'player_satisfaction',
        'review_engagement',
        'sentiment_intensity',
        'topic_variety'
    ]

    def __init__(self):
        """Initialize the benchmarking module."""
        self.analyzer = None
        self.extractor = None
        self.benchmarks = {}

    def calculate_positive_rate(self, reviews_df: pd.DataFrame) -> float:
        """
        Calculate positive review rate.

        Args:
            reviews_df: DataFrame with reviews

        Returns:
            Percentage of positive reviews (0-100)
        """
        if reviews_df.empty:
            return 0.0

        positive_count = (reviews_df['voted_up'] == True).sum()
        total = len(reviews_df)

        return (positive_count / total * 100) if total > 0 else 0.0

    def calculate_avg_quality_score(self, reviews_df: pd.DataFrame) -> float:
        """
        Calculate average review quality score across all reviews.

        Args:
            reviews_df: DataFrame with reviews

        Returns:
            Average quality score (0-100)
        """
        if reviews_df.empty:
            return 0.0

        quality_scores = []
        for _, row in reviews_df.iterrows():
            text = str(row.get('review', ''))
            votes = int(row.get('votes_up', 0)) if row.get('votes_up') else 0
            
            # Simple quality calculation
            word_count = len(text.split())
            quality = min(word_count / 100 * 50 + votes * 5, 100)
            quality_scores.append(quality)

        return np.mean(quality_scores) if quality_scores else 0.0

    def calculate_issue_diversity(self, reviews_df: pd.DataFrame) -> float:
        """
        Calculate diversity of issues mentioned (0-1 scale).
        More diverse issues = higher score.

        Args:
            reviews_df: DataFrame with reviews

        Returns:
            Issue diversity score (0-1)
        """
        if reviews_df.empty:
            return 0.0

        # Detect some common issues based on text
        issue_keywords = {
            'performance': ['lag', 'fps', 'stutter', 'slow', 'performance'],
            'graphics': ['graphics', 'visual', 'texture', 'render'],
            'gameplay': ['gameplay', 'mechanics', 'controls', 'balance'],
            'audio': ['audio', 'sound', 'music', 'voice'],
            'bugs': ['bug', 'crash', 'glitch', 'error', 'broken'],
            'story': ['story', 'narrative', 'plot', 'character'],
        }

        issue_counts = {}
        for _, row in reviews_df.iterrows():
            text = str(row.get('review', '')).lower()
            for issue, keywords in issue_keywords.items():
                if any(keyword in text for keyword in keywords):
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1

        if not issue_counts:
            return 0.0

        # Calculate Shannon diversity
        proportions = np.array(list(issue_counts.values())) / sum(issue_counts.values())
        diversity = -np.sum(proportions * np.log(proportions + 1e-10))

        # Normalize to 0-1 (max diversity is log(6) for 6 issue types)
        max_diversity = np.log(6)
        return min(diversity / max_diversity, 1.0)

    def calculate_player_satisfaction(self, reviews_df: pd.DataFrame) -> float:
        """
        Calculate overall player satisfaction score.

        Args:
            reviews_df: DataFrame with reviews

        Returns:
            Satisfaction score (0-100)
        """
        if reviews_df.empty:
            return 0.0

        # Combine positive rate with quality
        pos_rate = self.calculate_positive_rate(reviews_df)
        quality = self.calculate_avg_quality_score(reviews_df) / 100.0

        # Weight positive rate more heavily
        satisfaction = pos_rate * 0.7 + quality * 100 * 0.3

        return satisfaction

    def calculate_review_engagement(self, reviews_df: pd.DataFrame) -> float:
        """
        Calculate review engagement (helpful votes, comments).

        Args:
            reviews_df: DataFrame with reviews

        Returns:
            Engagement score (0-100)
        """
        if reviews_df.empty:
            return 0.0

        # Average helpful votes per review
        if 'votes_up' in reviews_df.columns:
            votes_up = pd.to_numeric(reviews_df['votes_up'], errors='coerce').fillna(0)
            avg_votes = votes_up.mean()
        else:
            avg_votes = 0.0

        # Normalize (assume 10 avg votes = 100% engagement)
        engagement = min(avg_votes / 10 * 100, 100)

        return float(engagement)

    def calculate_sentiment_intensity(self, reviews_df: pd.DataFrame) -> float:
        """
        Calculate average sentiment intensity across reviews.

        Args:
            reviews_df: DataFrame with reviews

        Returns:
            Intensity score (0-100)
        """
        if reviews_df.empty:
            return 0.0

        intensity_scores = []

        strong_words = ['absolutely', 'must', 'never', 'best', 'worst',
                       'terrible', 'amazing', 'excellent', 'horrible']

        for _, row in reviews_df.iterrows():
            text = str(row.get('review', '')).lower()
            intensity = sum(1 for word in strong_words if word in text)
            intensity_scores.append(min(intensity, 5) / 5 * 100)

        return np.mean(intensity_scores) if intensity_scores else 0.0

    def calculate_topic_variety(self, reviews_df: pd.DataFrame) -> float:
        """
        Calculate variety of topics discussed.

        Args:
            reviews_df: DataFrame with reviews

        Returns:
            Topic variety score (0-100)
        """
        if reviews_df.empty:
            return 0.0

        # Count unique keywords to estimate topic variety
        all_keywords = set()
        for _, row in reviews_df.iterrows():
            text = str(row.get('review', '')).lower().split()
            all_keywords.update([w for w in text if len(w) > 3])

        # Normalize (100 unique keywords = 100%)
        variety = min(len(all_keywords) / 100 * 100, 100)

        return variety

    def benchmark_game(
        self,
        reviews_df: pd.DataFrame,
        game_name: str,
        app_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Calculate comprehensive benchmark for a game.

        Args:
            reviews_df: DataFrame with reviews
            game_name: Name of the game
            app_id: Optional Steam app ID

        Returns:
            Dictionary with all benchmark metrics
        """
        benchmark = {
            'game_name': game_name,
            'app_id': app_id,
            'total_reviews': len(reviews_df),
            'positive_rate': self.calculate_positive_rate(reviews_df),
            'avg_quality_score': round(self.calculate_avg_quality_score(reviews_df), 2),
            'issue_diversity': round(self.calculate_issue_diversity(reviews_df), 2),
            'player_satisfaction': round(self.calculate_player_satisfaction(reviews_df), 2),
            'review_engagement': round(self.calculate_review_engagement(reviews_df), 2),
            'sentiment_intensity': round(self.calculate_sentiment_intensity(reviews_df), 2),
            'topic_variety': round(self.calculate_topic_variety(reviews_df), 2),
        }

        self.benchmarks[game_name] = benchmark
        return benchmark

    def compare_games(
        self,
        games_dict: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Compare multiple games across all dimensions.

        Args:
            games_dict: Dictionary mapping game names to their review DataFrames

        Returns:
            DataFrame with comparison results
        """
        benchmarks = []

        for game_name, reviews_df in games_dict.items():
            benchmark = self.benchmark_game(reviews_df, game_name)
            benchmarks.append(benchmark)

        comparison_df = pd.DataFrame(benchmarks)

        # Calculate rankings for each dimension
        for dimension in self.BENCHMARK_DIMENSIONS:
            if dimension in comparison_df.columns:
                comparison_df[f'{dimension}_rank'] = comparison_df[dimension].rank(ascending=False)

        return comparison_df

    def get_percentile_rank(
        self,
        game_name: str,
        dimension: str,
        all_games_df: pd.DataFrame
    ) -> float:
        """
        Calculate percentile rank for a game in a specific dimension.

        Args:
            game_name: Name of the game
            dimension: Benchmark dimension
            all_games_df: DataFrame with all game benchmarks

        Returns:
            Percentile rank (0-100)
        """
        if game_name not in all_games_df['game_name'].values:
            return None

        value = all_games_df[all_games_df['game_name'] == game_name][dimension].values[0]
        all_values = all_games_df[dimension].values

        percentile = (all_values < value).sum() / len(all_values) * 100

        return percentile

    def get_benchmark_summary(self, game_name: str) -> Optional[Dict]:
        """
        Get summary of benchmark for a specific game.

        Args:
            game_name: Name of the game

        Returns:
            Dictionary with game benchmark summary
        """
        return self.benchmarks.get(game_name)

    def identify_strengths_weaknesses(
        self,
        game_name: str,
        comparison_df: pd.DataFrame
    ) -> Dict[str, List[str]]:
        """
        Identify strengths and weaknesses of a game relative to others.

        Args:
            game_name: Name of the game
            comparison_df: DataFrame with all game benchmarks

        Returns:
            Dictionary with 'strengths' and 'weaknesses' lists
        """
        if game_name not in comparison_df['game_name'].values:
            return {'strengths': [], 'weaknesses': []}

        game_row = comparison_df[comparison_df['game_name'] == game_name].iloc[0]

        strengths = []
        weaknesses = []

        for dimension in self.BENCHMARK_DIMENSIONS:
            if dimension in comparison_df.columns:
                rank_col = f'{dimension}_rank'
                if rank_col in comparison_df.columns:
                    rank = game_row[rank_col]
                    total_games = len(comparison_df)

                    if rank == 1:
                        strengths.append(f"Best {dimension.replace('_', ' ')}")
                    elif rank <= total_games / 2:
                        strengths.append(f"Above average {dimension.replace('_', ' ')}")
                    else:
                        weaknesses.append(f"Below average {dimension.replace('_', ' ')}")

        return {'strengths': strengths, 'weaknesses': weaknesses}


def benchmark_games(
    games_dict: Dict[str, pd.DataFrame]
) -> Tuple[GameBenchmark, pd.DataFrame]:
    """
    Benchmark multiple games across all dimensions.

    Args:
        games_dict: Dictionary mapping game names to DataFrames

    Returns:
        Tuple of (benchmarker object, comparison DataFrame)
    """
    benchmarker = GameBenchmark()
    comparison = benchmarker.compare_games(games_dict)
    return benchmarker, comparison


if __name__ == "__main__":
    logger.info("Multi-Dimensional Game Benchmarking Module")
