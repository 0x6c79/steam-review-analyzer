"""
Review Recommendation & Ranking Engine

Recommends and ranks reviews based on quality, helpfulness, relevance, and other factors.
Provides personalized recommendations based on player segment and issue filters.
"""

import sys
import os
import logging
from typing import List, Dict, Tuple, Optional
from enum import Enum

import pandas as pd
import numpy as np

# Setup path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.steam_review import config
from src.steam_review.analysis.advanced_analyzer import AdvancedReviewAnalyzer

config.setup_logging()
logger = logging.getLogger(__name__)


class ReviewUsefulness(Enum):
    """Review usefulness categories."""
    HIGHLY_USEFUL = "Highly Useful"
    USEFUL = "Useful"
    MODERATELY_USEFUL = "Moderately Useful"
    LESS_USEFUL = "Less Useful"


class ReviewRecommender:
    """
    Recommends and ranks reviews based on multiple quality metrics.
    Provides personalized recommendations based on filters and segments.
    """

    # Scoring weights for composite ranking
    WEIGHTS = {
        'quality_score': 0.35,      # Review quality (length, structure, detail)
        'helpfulness': 0.25,         # Helpful votes / total votes
        'sentiment_intensity': 0.15, # How strong the opinion is
        'recency': 0.15,             # Newer reviews weighted slightly higher
        'detail_level': 0.10         # How detailed/informative
    }

    def __init__(self):
        """Initialize the review recommender."""
        self.analyzer = None
        self.review_scores = {}
        self.recommendations = []

    def calculate_helpfulness_score(self, review_row: pd.Series) -> float:
        """
        Calculate helpfulness score (0-1) based on helpful votes.

        Args:
            review_row: A review from the DataFrame

        Returns:
            Helpfulness score between 0 and 1
        """
        votes_up = float(review_row.get('votes_up', 0)) if review_row.get('votes_up') else 0
        votes_funny = float(review_row.get('votes_funny', 0)) if review_row.get('votes_funny') else 0
        total_votes = votes_up + votes_funny

        if total_votes == 0:
            return 0.0

        # Normalize to 0-1 scale using sigmoid-like function
        # More votes = higher score, but with diminishing returns
        helpfulness = votes_up / max(total_votes, 1)
        return min(helpfulness, 1.0)

    def calculate_detail_level(self, review_text: str) -> float:
        """
        Calculate detail level (0-1) based on text complexity.

        Args:
            review_text: The review text

        Returns:
            Detail level score between 0 and 1
        """
        if not review_text or str(review_text).lower() == 'nan':
            return 0.0

        text = str(review_text)
        
        # Metrics for detail level
        word_count = len(text.split())
        sentence_count = len([s for s in text.split('.') if s.strip()])
        avg_words_per_sentence = word_count / max(sentence_count, 1)
        
        # More detail = more words, better structure
        detail_score = min(word_count / 500, 1.0) * 0.5 + \
                      min(avg_words_per_sentence / 20, 1.0) * 0.5
        
        return min(detail_score, 1.0)

    def calculate_sentiment_intensity(self, review_row: pd.Series) -> float:
        """
        Calculate how intense/strong the opinion in the review is.

        Args:
            review_row: A review from the DataFrame

        Returns:
            Intensity score between 0 and 1
        """
        review_text = str(review_row.get('review', ''))
        if not review_text or review_text.lower() == 'nan':
            return 0.0

        # Count strong opinion indicators
        strong_words = ['absolutely', 'must', 'never', 'best', 'worst', 'always',
                       'terrible', 'amazing', 'excellent', 'horrible', 'perfect',
                       '完全', '绝对', '最好', '最差', '可怕', '优秀']
        
        count = sum(1 for word in strong_words if word in review_text.lower())
        
        # Normalize to 0-1
        intensity = min(count / 5, 1.0)
        return intensity

    def calculate_recency_score(self, review_row: pd.Series) -> float:
        """
        Calculate recency score (0-1) based on review timestamp.

        Args:
            review_row: A review from the DataFrame with 'timestamp_created'

        Returns:
            Recency score between 0 and 1
        """
        timestamp = review_row.get('timestamp_created')
        if not timestamp or pd.isna(timestamp):
            return 0.5  # Neutral score if no timestamp

        try:
            import time
            current_time = time.time()
            age_days = (current_time - float(timestamp)) / (24 * 3600)
            
            # Reviews from last 30 days get higher scores, decaying after
            if age_days <= 30:
                return 1.0
            elif age_days <= 90:
                return 0.8 - (age_days - 30) / 60 * 0.3
            elif age_days <= 365:
                return 0.5 - (age_days - 90) / 275 * 0.3
            else:
                return 0.2
        except:
            return 0.5

    def score_review(self, review_row: pd.Series, quality_score: float) -> float:
        """
        Calculate composite review usefulness score.

        Args:
            review_row: A review from the DataFrame
            quality_score: Pre-calculated quality score (0-100)

        Returns:
            Composite usefulness score (0-100)
        """
        # Normalize quality score to 0-1
        quality_normalized = quality_score / 100.0

        # Calculate individual components
        helpfulness = self.calculate_helpfulness_score(review_row)
        detail = self.calculate_detail_level(str(review_row.get('review', '')))
        intensity = self.calculate_sentiment_intensity(review_row)
        recency = self.calculate_recency_score(review_row)

        # Weighted composite score
        composite = (
            self.WEIGHTS['quality_score'] * quality_normalized +
            self.WEIGHTS['helpfulness'] * helpfulness +
            self.WEIGHTS['sentiment_intensity'] * intensity +
            self.WEIGHTS['recency'] * recency +
            self.WEIGHTS['detail_level'] * detail
        )

        return composite * 100

    def recommend_reviews(
        self,
        reviews_df: pd.DataFrame,
        top_n: int = 10,
        player_segment: Optional[str] = None,
        issue_filter: Optional[str] = None,
        sentiment_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Recommend top reviews based on scoring and filters.

        Args:
            reviews_df: DataFrame with reviews
            top_n: Number of reviews to recommend
            player_segment: Filter by player type ('Enthusiasts', 'Satisfied', etc.)
            issue_filter: Filter by detected issue
            sentiment_filter: Filter by sentiment ('positive', 'negative', 'all')

        Returns:
            List of top N recommended reviews with scores
        """
        df = reviews_df.copy()
        
        # Initialize analyzer for this dataframe
        if self.analyzer is None:
            self.analyzer = AdvancedReviewAnalyzer(reviews_df)

        # Calculate quality scores for all reviews
        quality_scores = []
        for _, row in df.iterrows():
            # Use a simple quality calculation here
            text = str(row.get('review', ''))
            votes = int(row.get('votes_up', 0)) if row.get('votes_up') else 0
            
            word_count = len(text.split())
            quality = min(word_count / 100 * 50 + votes * 5, 100)
            quality_scores.append(quality)

        df['quality_score'] = quality_scores

        # Calculate composite recommendation scores
        recommendation_scores = []
        for _, row in df.iterrows():
            score = self.score_review(row, row['quality_score'])
            recommendation_scores.append(score)

        df['recommendation_score'] = recommendation_scores

        # Apply filters
        if sentiment_filter and sentiment_filter != 'all':
            if sentiment_filter == 'positive':
                df = df[df['voted_up'] == True]
            elif sentiment_filter == 'negative':
                df = df[df['voted_up'] == False]

        # Player segment filter - would need segment analysis
        # For now, we'll skip as it requires pre-computed segments

        # Issue filter - would need issue detection
        # For now, we'll skip as it requires pre-computed issues

        # Sort by recommendation score and get top N
        top_reviews = df.nlargest(top_n, 'recommendation_score')

        # Format as list of dicts
        recommendations = []
        for idx, (_, row) in enumerate(top_reviews.iterrows(), 1):
            recommendations.append({
                'rank': idx,
                'recommendation_score': round(row['recommendation_score'], 2),
                'quality_score': round(row['quality_score'], 2),
                'review_text': str(row.get('review', '')),
                'sentiment': 'Positive' if row.get('voted_up') else 'Negative',
                'helpful_votes': int(row.get('votes_up', 0)) if row.get('votes_up') else 0,
                'helpful_count': int(row.get('helpful_count', 0)) if row.get('helpful_count') else 0,
                'author': str(row.get('author.num_reviews', 'Unknown')),
                'playtime': int(row.get('author.playtime_forever', 0)) if row.get('author.playtime_forever') else 0,
                'timestamp': row.get('timestamp_created'),
            })

        self.recommendations = recommendations
        return recommendations

    def get_usefulness_category(self, score: float) -> ReviewUsefulness:
        """
        Categorize review based on usefulness score.

        Args:
            score: Usefulness score (0-100)

        Returns:
            ReviewUsefulness enum value
        """
        if score >= 75:
            return ReviewUsefulness.HIGHLY_USEFUL
        elif score >= 60:
            return ReviewUsefulness.USEFUL
        elif score >= 40:
            return ReviewUsefulness.MODERATELY_USEFUL
        else:
            return ReviewUsefulness.LESS_USEFUL

    def recommend_by_category(
        self,
        reviews_df: pd.DataFrame,
        category: ReviewUsefulness,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Get top reviews in a specific usefulness category.

        Args:
            reviews_df: DataFrame with reviews
            category: ReviewUsefulness category
            top_n: Number of reviews in category

        Returns:
            List of top N reviews in specified category
        """
        # First get all recommendations
        all_recommendations = self.recommend_reviews(reviews_df, top_n=len(reviews_df))

        # Filter by category score range
        if category == ReviewUsefulness.HIGHLY_USEFUL:
            filtered = [r for r in all_recommendations if r['recommendation_score'] >= 75]
        elif category == ReviewUsefulness.USEFUL:
            filtered = [r for r in all_recommendations if 60 <= r['recommendation_score'] < 75]
        elif category == ReviewUsefulness.MODERATELY_USEFUL:
            filtered = [r for r in all_recommendations if 40 <= r['recommendation_score'] < 60]
        else:
            filtered = [r for r in all_recommendations if r['recommendation_score'] < 40]

        return filtered[:top_n]

    def get_contrasting_reviews(
        self,
        reviews_df: pd.DataFrame,
        top_n: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Get best positive and negative reviews for comparison.

        Args:
            reviews_df: DataFrame with reviews
            top_n: Number of reviews per sentiment

        Returns:
            Dictionary with 'positive' and 'negative' review lists
        """
        positive_reviews = self.recommend_reviews(
            reviews_df[reviews_df['voted_up'] == True],
            top_n=top_n,
            sentiment_filter='positive'
        )

        negative_reviews = self.recommend_reviews(
            reviews_df[reviews_df['voted_up'] == False],
            top_n=top_n,
            sentiment_filter='negative'
        )

        return {
            'positive': positive_reviews,
            'negative': negative_reviews
        }

    def get_recommendation_summary(self) -> pd.DataFrame:
        """
        Get summary statistics of recommendations.

        Returns:
            DataFrame with recommendation statistics
        """
        if not self.recommendations:
            return pd.DataFrame()

        summary = {
            'total_recommended': len(self.recommendations),
            'avg_quality_score': np.mean([r['quality_score'] for r in self.recommendations]),
            'avg_recommendation_score': np.mean([r['recommendation_score'] for r in self.recommendations]),
            'most_helpful': max([r['helpful_votes'] for r in self.recommendations]),
            'avg_helpful_votes': np.mean([r['helpful_votes'] for r in self.recommendations]),
        }

        return pd.DataFrame([summary])


def get_top_recommendations(
    reviews_df: pd.DataFrame,
    top_n: int = 10
) -> Tuple[ReviewRecommender, List[Dict]]:
    """
    Get top review recommendations.

    Args:
        reviews_df: DataFrame with reviews
        top_n: Number of recommendations

    Returns:
        Tuple of (recommender object, recommendations list)
    """
    recommender = ReviewRecommender()
    recommendations = recommender.recommend_reviews(reviews_df, top_n)
    return recommender, recommendations


if __name__ == "__main__":
    logger.info("Review Recommendation Engine")
