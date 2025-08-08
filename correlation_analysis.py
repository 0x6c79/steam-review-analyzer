import pandas as pd
import logging
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
from utils import analyze_by_playtime, analyze_by_review_length, analyze_by_early_access

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_correlation(df):
    logging.info("\n--- Performing Correlation Analysis ---")

    # New Analysis: Correlation between Sentiment Score and Playtime/Review Length
    df_en = df[df['detected_language'] == 'en'].copy() # Filter for English reviews for VADER correlation
    if not df_en.empty:
        correlation_playtime, p_value_playtime = stats.pearsonr(df_en['playtime_hours'].dropna(), df_en['sentiment_score'].dropna())
        logging.info(f"Pearson correlation between English sentiment score and playtime: {correlation_playtime:.2f} (p-value: {p_value_playtime:.3f})")

        correlation_review_length, p_value_review_length = stats.pearsonr(df_en['review_length'].dropna(), df_en['sentiment_score'].dropna())
        logging.info(f"Pearson correlation between English sentiment score and review length: {correlation_review_length:.2f} (p-value: {p_value_review_length:.3f})")

    # Other Analyses
    analyze_by_playtime(df.copy())
    analyze_by_review_length(df.copy())
    analyze_by_early_access(df.copy())

if __name__ == "__main__":
    pass