import sys
import os
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
from collections import Counter
from src.steam_review.utils import utils
from src.steam_review import config

config.setup_logging()

def analyze_time_series(df):
    logging.info("\n--- Performing Time Series Analysis ---")

    # Resample by week and calculate sentiment ratios
    weekly_sentiment = df.resample('W').apply({'voted_up': lambda x: x.sum(),
                                                'review': 'count'})
    weekly_sentiment.rename(columns={'voted_up': 'Positive_Count', 'review': 'Total_Reviews'}, inplace=True)
    weekly_sentiment['Negative_Count'] = weekly_sentiment['Total_Reviews'] - weekly_sentiment['Positive_Count']
    weekly_sentiment['Positive_Ratio'] = weekly_sentiment['Positive_Count'] / weekly_sentiment['Total_Reviews']
    weekly_sentiment['Negative_Ratio'] = weekly_sentiment['Negative_Count'] / weekly_sentiment['Total_Reviews']
    weekly_sentiment.reset_index(inplace=True)
    weekly_sentiment.rename(columns={'timestamp_created': 'time_period'}, inplace=True)

    # Plot sentiment over time
    utils.plot_sentiment_over_time(weekly_sentiment, '评论情感随时间变化趋势', 'sentiment_over_time.png')

    # New Analysis: Keywords over Time
    df['year_month'] = df.index.to_period('M')
    monthly_keywords = {}

    for month, group in df.groupby('year_month'):
        positive_text = " ".join(group[group['voted_up']]['review'].dropna().tolist())
        negative_text = " ".join(group[~group['voted_up']]['review'].dropna().tolist())

        # Use detected_language for preprocessing
        positive_tokens = utils.preprocess_text(positive_text, lang=group['detected_language'].iloc[0] if not group.empty else 'english')
        negative_tokens = utils.preprocess_text(negative_text, lang=group['detected_language'].iloc[0] if not group.empty else 'english')

        positive_ngrams = utils.get_ngrams(positive_tokens, n_range=(1, 2))
        negative_ngrams = utils.get_ngrams(negative_tokens, n_range=(1, 2))

        monthly_keywords[month] = {
            'positive': Counter(positive_ngrams).most_common(10),
            'negative': Counter(negative_ngrams).most_common(10)
        }

    # For now, just log the monthly keywords
    logging.info(f"Monthly Keywords: {monthly_keywords}")

if __name__ == "__main__":
    pass