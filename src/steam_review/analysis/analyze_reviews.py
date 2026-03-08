import os
import pandas as pd
import logging
import asyncio
from langdetect import detect, LangDetectException
from langdetect.detector_factory import DetectorFactory
from src.steam_review import config
from src.steam_review.storage.database import get_database
from src.steam_review.analysis import sentiment_analysis
from src.steam_review.analysis import keyword_analysis
from src.steam_review.analysis import correlation_analysis
from src.steam_review.analysis import time_series_analysis
from src.steam_review.analysis.sentiment_analysis_enhanced import (
    analyze_sentiment_complete,
)

config.setup_logging()

DetectorFactory.seed = 0

USE_ENHANCED_SENTIMENT = True  # Set to True to use enhanced sentiment analysis


def detect_language_robust(text):
    text = str(text).strip()
    if not text:
        return "unknown"
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


async def main(file_path: str, save_to_db=False):
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
    df["timestamp_created"] = pd.to_datetime(df["timestamp_created"], unit="s")
    df.set_index("timestamp_created", inplace=True)

    # Add a language column to the DataFrame
    BATCH_SIZE = 1000  # Define a batch size for language detection
    detected_languages = []

    for i in range(0, len(df), BATCH_SIZE):
        batch = df.iloc[i : i + BATCH_SIZE]
        # Apply language detection to the 'review' column of the batch
        batch_languages = batch["review"].astype(str).apply(detect_language_robust)
        detected_languages.extend(batch_languages.tolist())

    df["detected_language"] = detected_languages

    # Calculate playtime_hours and review_length
    df["playtime_hours"] = (
        pd.to_numeric(df["author.playtime_forever"], errors="coerce") / 60
    )
    df["review_length"] = df["review"].astype(str).apply(len)

    # Run analyses
    if USE_ENHANCED_SENTIMENT:
        logging.info("Using enhanced sentiment analysis...")
        df = analyze_sentiment_complete(
            df, text_column="review", lang_column="detected_language"
        )
    else:
        sentiment_analysis.analyze_sentiment(df)
    keyword_analysis.analyze_keywords(df)
    filename_base = os.path.splitext(os.path.basename(file_path))[0]
    correlation_analysis.analyze_correlation(df, filename_base)
    time_series_analysis.analyze_time_series(df)

    # Save to database if requested
    if save_to_db:
        df_export = df.reset_index()
        if "recommendationid" in df_export.columns:
            df_export = df_export.rename(
                columns={"recommendationid": "recommendation_id"}
            )
        if "app_id" not in df_export.columns:
            basename = os.path.splitext(os.path.basename(file_path))[0]
            for part in basename.split("_"):
                if part.isdigit():
                    app_id = part
                    break
            else:
                app_id = "unknown"
            df_export["app_id"] = app_id
        db = get_database()
        db.insert_reviews(df_export)
        logging.info("Reviews saved to database")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze Steam reviews from a CSV file."
    )
    parser.add_argument("file_path", type=str, help="Path to the reviews CSV file.")
    parser.add_argument(
        "--save_db", action="store_true", help="Save analyzed reviews to database"
    )
    args = parser.parse_args()

    asyncio.run(main(args.file_path, args.save_db))
