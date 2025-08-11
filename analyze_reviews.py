import pandas as pd
import logging
from langdetect import detect, DetectorFactory, LangDetectException
import os
import asyncio

# Import analysis modules
from sentiment_analysis import analyze_sentiment
from keyword_analysis import analyze_keywords
from correlation_analysis import analyze_correlation
from time_series_analysis import analyze_time_series

# Add a language column to the DataFrame
def detect_language_robust(text):
    text = str(text).strip()
    if not text: # Handle empty strings after stripping
        return 'unknown'
    try:
        return detect(text)
    except LangDetectException:
        return 'unknown'

# Ensure reproducibility for langdetect
DetectorFactory.seed = 0

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main(file_path: str):
    # Create plots directory if it doesn't exist
    plots_dir = "plots"
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
        logging.info(f"Created directory: {plots_dir}")

    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        logging.error(f"Error: The file {file_path} was not found.")
        return

    if df.empty:
        logging.warning("Input DataFrame is empty. Exiting analysis.")
        return

    # Convert timestamp to datetime and set as index for time-series analysis
    df['timestamp_created'] = pd.to_datetime(df['timestamp_created'], unit='s')
    df.set_index('timestamp_created', inplace=True)

    # Add a language column to the DataFrame
    BATCH_SIZE = 1000 # Define a batch size for language detection
    detected_languages = []

    for i in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[i:i + BATCH_SIZE]
        # Apply language detection to the 'review' column of the batch
        batch_languages = batch['review'].astype(str).apply(detect_language_robust)
        detected_languages.extend(batch_languages.tolist())

    df['detected_language'] = detected_languages
    df['language'] = df['detected_language'] # Use detected language for analysis

    # Calculate playtime_hours and review_length
    df['playtime_hours'] = pd.to_numeric(df['author.playtime_forever'], errors='coerce') / 60
    df['review_length'] = df['review'].astype(str).apply(len)

    # Run analyses
    analyze_sentiment(df)
    analyze_keywords(df)
    analyze_correlation(df)
    analyze_time_series(df)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Steam reviews from a CSV file.")
    parser.add_argument("file_path", type=str, help="Path to the reviews CSV file.")
    args = parser.parse_args()

    # Download langdetect data
    try:
        detect("test")
    except Exception as e:
        logging.warning(f"langdetect data not found or error: {e}. Attempting to download.")
        os.system("python3 -m langdetect.detector_factory --update-profile")

    asyncio.run(main(args.file_path))