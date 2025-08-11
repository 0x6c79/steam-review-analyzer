import matplotlib.pyplot as plt
import seaborn as sns
import logging
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import utils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_sentiment(df):
    logging.info("\n--- Performing Sentiment Analysis ---")

    # Ensure vader_lexicon is downloaded
    try:
        nltk.data.find('sentiment/vader_lexicon')
    except Exception:
        nltk.download('vader_lexicon')

    analyzer = SentimentIntensityAnalyzer()
    def get_vader_sentiment(text):
        try:
            vs = analyzer.polarity_scores(text)
            return vs['compound']
        except TypeError:
            return 0.0 # Return neutral for non-string types

    df['sentiment_score'] = df.apply(lambda row: get_vader_sentiment(row['review']) if row['detected_language'] == 'en' else (1 if row['voted_up'] else 0), axis=1)

    # Overall Sentiment Distribution
    total_reviews = len(df)
    positive_reviews_count = df[df['voted_up']].shape[0]
    negative_reviews_count = df[~df['voted_up']].shape[0]

    logging.info(f"总评论数: {total_reviews}")
    logging.info(f"好评: {positive_reviews_count} ({positive_reviews_count / total_reviews:.2%})")
    logging.info(f"差评: {negative_reviews_count} ({negative_reviews_count / total_reviews:.2%})")
    utils.plot_sentiment_distribution(positive_reviews_count, negative_reviews_count, total_reviews)

    # Sentiment Score Distribution
    plt.figure(figsize=(10, 6))
    sns.histplot(df['sentiment_score'], bins=2, kde=False)
    plt.title('Sentiment Score Distribution')
    plt.xlabel('Sentiment Score (0: Negative, 1: Positive)')
    plt.ylabel('Number of Reviews')
    plt.savefig('plots/sentiment_score_distribution.png')
    plt.close()
    logging.info("Generated plots/sentiment_score_distribution.png")

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

if __name__ == "__main__":
    # This part is for testing the module independently
    # In the main analysis, it will be called with a DataFrame
    pass
