#!/usr/bin/env python3
"""
Advanced Review Analysis Module
Provides: Sentiment Intensity, Quality Scoring, Issue Detection, etc.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import Counter
import re

class AdvancedReviewAnalyzer:
    """Comprehensive review analysis with multiple dimensions"""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize analyzer with review dataframe"""
        self.df = df.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for analysis"""
        # Ensure required columns
        if 'review' not in self.df.columns:
            self.df['review'] = ''
        if 'voted_up' not in self.df.columns:
            self.df['voted_up'] = 0
    
    # ==================== SENTIMENT INTENSITY ====================
    
    def analyze_sentiment_intensity(self) -> Dict:
        """
        Analyze sentiment beyond binary positive/negative
        Returns: Intensity levels (very positive, positive, negative, very negative)
        """
        def get_intensity(row):
            review_text = str(row.get('review', '')).lower()
            voted = int(row.get('voted_up', 0))
            
            # Strong positive indicators
            very_positive_words = ['excellent', 'amazing', 'love', 'perfect', 'fantastic', 
                                  '太棒', '太好', '非常好', '完美', '喜欢']
            # Mild positive indicators
            positive_words = ['good', 'nice', 'fun', 'enjoy', 'great',
                            '不错', '还可以', '有趣', '不做']
            # Strong negative indicators
            very_negative_words = ['terrible', 'horrible', 'hate', 'worst', 'awful',
                                 '太差', '很差', '讨厌', '垃圾']
            # Mild negative indicators
            negative_words = ['bad', 'boring', 'issue', 'problem', 'disappointing',
                            '不好', '一般', '问题']
            
            score = 0
            # Count indicators
            score += sum(1 for word in very_positive_words if word in review_text) * 2
            score += sum(1 for word in positive_words if word in review_text) * 1
            score -= sum(1 for word in very_negative_words if word in review_text) * 2
            score -= sum(1 for word in negative_words if word in review_text) * 1
            
            # Combine with vote
            if voted:
                score += 1
            else:
                score -= 1
            
            # Classify
            if score >= 2:
                return 'Very Positive'
            elif score >= 0:
                return 'Positive'
            elif score >= -2:
                return 'Negative'
            else:
                return 'Very Negative'
        
        self.df['sentiment_intensity'] = self.df.apply(get_intensity, axis=1)
        
        intensity_dist = self.df['sentiment_intensity'].value_counts().to_dict()
        return {
            'distribution': intensity_dist,
            'percentages': {k: f"{v/len(self.df)*100:.1f}%" for k, v in intensity_dist.items()}
        }
    
    # ==================== QUALITY SCORING ====================
    
    def calculate_quality_score(self) -> pd.Series:
        """
        Calculate review quality score (0-100)
        Factors: length, detail, helpful votes, language clarity
        """
        def score_review(row):
            text = str(row.get('review', ''))
            votes = int(row.get('voted_up', 0))
            
            score = 0
            
            # Length factor (0-25 points)
            word_count = len(text.split())
            if word_count >= 500:
                score += 25
            elif word_count >= 200:
                score += 20
            elif word_count >= 100:
                score += 15
            elif word_count >= 50:
                score += 10
            elif word_count > 0:
                score += 5
            
            # Detail factor (0-25 points)
            has_details = any(keyword in text.lower() for keyword in 
                            ['gameplay', 'graphics', 'performance', 'story', 'characters',
                             '游戏', '画面', '性能', '故事', '角色'])
            if has_details:
                score += 15
            
            # Punctuation/Structure (0-20 points)
            if '.' in text or '。' in text:
                score += 10
            if '\n' in text:
                score += 5
            if len(set(text.split())) > len(text.split()) * 0.3:  # Vocabulary diversity
                score += 5
            
            # Helpfulness factor (0-30 points)
            # This would come from Steam's helpful votes in real data
            if votes:
                score += 10
            
            return min(100, score)
        
        self.df['quality_score'] = self.df.apply(score_review, axis=1)
        return self.df['quality_score']
    
    # ==================== ISSUE DETECTION ====================
    
    def detect_issues(self) -> Dict[str, List[str]]:
        """
        Detect common issues/problems mentioned in reviews
        """
        issue_patterns = {
            'Performance': ['lag', 'fps', 'slow', 'crash', 'freeze', '卡顿', '延迟', '崩溃'],
            'Graphics': ['graphics', 'texture', 'resolution', 'graphics card', '画面', '贴图'],
            'Gameplay': ['gameplay', 'balance', 'mechanic', 'control', '游戏平衡', '机制'],
            'Story/Content': ['story', 'plot', 'mission', 'content', '故事', '情节'],
            'Audio': ['sound', 'audio', 'music', 'voice', '声音', '音乐'],
            'Network/Multiplayer': ['server', 'lag', 'multiplayer', 'connection', '服务器', '联网'],
            'Bugs/Glitches': ['bug', 'glitch', 'error', 'broken', '漏洞', '错误'],
            'DLC/Pricing': ['price', 'expensive', 'dlc', 'pay', '价格', '昂贵'],
        }
        
        detected_issues = {category: 0 for category in issue_patterns.keys()}
        issue_reviews = {category: [] for category in issue_patterns.keys()}
        
        for idx, row in self.df.iterrows():
            text = str(row.get('review', '')).lower()
            for category, keywords in issue_patterns.items():
                if any(keyword in text for keyword in keywords):
                    detected_issues[category] += 1
                    if len(issue_reviews[category]) < 3:  # Store sample reviews
                        issue_reviews[category].append(text[:100])
        
        return {
            'issue_count': detected_issues,
            'issue_percentage': {k: f"{v/len(self.df)*100:.1f}%" for k, v in detected_issues.items()},
            'sample_reviews': issue_reviews
        }
    
    # ==================== PLAYER SEGMENTATION ====================
    
    def segment_players(self) -> Dict:
        """
        Segment players based on review patterns
        """
        segments = {
            'Enthusiasts': [],  # Very positive, detailed
            'Satisfied': [],     # Positive, moderate detail
            'Cautious': [],      # Mixed, concerned about issues
            'Dissatisfied': [],  # Negative reviews
            'Critical': []       # Very negative, detailed issues
        }
        
        for idx, row in self.df.iterrows():
            text = str(row.get('review', ''))
            voted = int(row.get('voted_up', 0))
            length = len(text.split())
            
            if voted and length > 100:
                segments['Enthusiasts'].append(idx)
            elif voted and length > 20:
                segments['Satisfied'].append(idx)
            elif voted and length < 20:
                segments['Satisfied'].append(idx)
            elif not voted and length > 100:
                segments['Critical'].append(idx)
            elif not voted and length > 20:
                segments['Dissatisfied'].append(idx)
            else:
                segments['Cautious'].append(idx)
        
        return {
            'segments': {k: len(v) for k, v in segments.items()},
            'percentages': {k: f"{len(v)/len(self.df)*100:.1f}%" for k, v in segments.items()},
            'samples': {k: v[:3] for k, v in segments.items()}
        }
    
    # ==================== TOP REVIEWS ====================
    
    def get_top_reviews(self, n: int = 5, by: str = 'quality') -> pd.DataFrame:
        """
        Get top reviews by quality score or helpfulness
        """
        if 'quality_score' not in self.df.columns:
            self.calculate_quality_score()
        
        if by == 'quality':
            return self.df.nlargest(n, 'quality_score')[['review', 'quality_score', 'voted_up']]
        else:
            return self.df.nlargest(n, 'voted_up')[['review', 'voted_up', 'quality_score']]
    
    # ==================== TEMPORAL ANALYSIS ====================
    
    def analyze_temporal_trends(self, period: str = 'daily') -> Dict:
        """
        Analyze sentiment trends over time
        period: 'daily', 'weekly', 'monthly'
        """
        if 'timestamp_created' not in self.df.columns:
            return {}
        
        # Convert to datetime
        df_temp = self.df.copy()
        df_temp['date'] = pd.to_datetime(df_temp['timestamp_created'], unit='s')
        
        if period == 'daily':
            groupby_col = df_temp['date'].dt.date
        elif period == 'weekly':
            groupby_col = df_temp['date'].dt.to_period('W')
        else:  # monthly
            groupby_col = df_temp['date'].dt.to_period('M')
        
        trends = df_temp.groupby(groupby_col).agg({
            'voted_up': ['sum', 'count', 'mean']
        }).round(3)
        
        return {
            'trend_data': trends.to_dict(),
            'positive_trend': 'improving' if df_temp.groupby(groupby_col)['voted_up'].mean().iloc[-1] > 
                            df_temp.groupby(groupby_col)['voted_up'].mean().iloc[0] else 'declining'
        }
    
    # ==================== COMPARISON METRICS ====================
    
    def get_comparison_metrics(self) -> Dict:
        """
        Get metrics for comparing with other games
        """
        return {
            'avg_review_length': len(' '.join(self.df['review'].astype(str)).split()),
            'avg_quality_score': self.df['quality_score'].mean() if 'quality_score' in self.df.columns else 0,
            'positive_rate': (self.df['voted_up'].sum() / len(self.df) * 100) if len(self.df) > 0 else 0,
            'review_count': len(self.df),
            'avg_playtime_hours': 0,  # Would need playtime data
            'update_frequency': 'N/A'  # Would need version data
        }


def analyze_reviews_comprehensive(csv_file: str = None, df: pd.DataFrame = None) -> Dict:
    """
    Perform comprehensive review analysis
    """
    if df is None and csv_file:
        df = pd.read_csv(csv_file)
    elif df is None:
        raise ValueError("Must provide either csv_file or df")
    
    analyzer = AdvancedReviewAnalyzer(df)
    
    # Run all analyses
    results = {
        'sentiment_intensity': analyzer.analyze_sentiment_intensity(),
        'quality_scores': analyzer.calculate_quality_score().describe().to_dict(),
        'issue_detection': analyzer.detect_issues(),
        'player_segments': analyzer.segment_players(),
        'temporal_trends': analyzer.analyze_temporal_trends(),
        'comparison_metrics': analyzer.get_comparison_metrics(),
        'top_reviews': analyzer.get_top_reviews(5).to_dict()
    }
    
    return results, analyzer


if __name__ == '__main__':
    # Example usage
    import sys
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        results, analyzer = analyze_reviews_comprehensive(csv_file=csv_file)
        print(results)
