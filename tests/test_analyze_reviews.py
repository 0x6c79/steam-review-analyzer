import pytest
import pytest_asyncio # Explicitly import pytest_asyncio
import pandas as pd
from unittest.mock import patch
import sys
import os

# Add the project root to the sys.path to allow imports from the main directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analyze_reviews import main # Removed detect_language_robust from import

# Mock external dependencies that might cause issues or are not part of the unit being tested
@pytest.fixture
def mock_logging_fixture():
    with patch('analyze_reviews.logging', autospec=True) as mock_logging:
        mock_logging.error.return_value = None
        mock_logging.warning.return_value = None
        mock_logging.info.return_value = None
        yield mock_logging

@pytest.fixture
def mock_external_dependencies():
    with patch('sentiment_analysis.nltk', autospec=True) as mock_nltk, \
         patch('analyze_reviews.os', autospec=True) as mock_os, \
         patch('analyze_reviews.asyncio', autospec=True) as mock_asyncio:
        # Prevent actual downloads or system calls
        mock_nltk.download.return_value = None
        mock_os.system.return_value = 0
        mock_asyncio.run.return_value = None # Prevent asyncio.run from actually running main
        yield

@pytest.fixture
def sample_dataframe():
    # Create a sample DataFrame that mimics the structure of reviews.csv
    data = {
        'review': [
            'This game is amazing! I love it.',
            'It\'s okay, but could be better.',
            'Terrible game, full of bugs.',
            '一款非常棒的游戏，我喜欢它。', # Chinese review
            '', # Empty review
            '   ' # Whitespace review
        ],
        'timestamp_created': [1678886400, 1678972800, 1679059200, 1679145600, 1679232000, 1679318400],
        'author.playtime_forever': [1200, 300, 50, 600, 0, 10],
        'voted_up': [True, True, False, True, True, False]
    }
    df = pd.DataFrame(data)
    return df

# Test the main function
@pytest.mark.asyncio
async def test_main_function_success(sample_dataframe, mock_external_dependencies):
    with patch('analyze_reviews.pd.read_csv', return_value=sample_dataframe) as mock_read_csv, \
         patch('analyze_reviews.analyze_sentiment', autospec=True) as mock_analyze_sentiment, \
         patch('analyze_reviews.analyze_keywords', autospec=True) as mock_analyze_keywords, \
         patch('analyze_reviews.analyze_correlation', autospec=True) as mock_analyze_correlation, \
         patch('analyze_reviews.analyze_time_series', autospec=True) as mock_analyze_time_series, \
         patch('analyze_reviews.detect', side_effect=['en', 'en', 'en', 'zh-cn', 'unknown', 'unknown']) as mock_detect: # Mock language detection

        await main("dummy_file_path.csv")

        # Verify pd.read_csv was called
        mock_read_csv.assert_called_once_with("dummy_file_path.csv")

        # Verify language detection was called for each review
        assert mock_detect.call_count == 4

        # Verify that analysis functions were called with a DataFrame
        # We can't directly check the content of the DataFrame passed, but we can check if it's a DataFrame
        mock_analyze_sentiment.assert_called_once()
        assert isinstance(mock_analyze_sentiment.call_args[0][0], pd.DataFrame)

        mock_analyze_keywords.assert_called_once()
        assert isinstance(mock_analyze_keywords.call_args[0][0], pd.DataFrame)

        mock_analyze_correlation.assert_called_once()
        assert isinstance(mock_analyze_correlation.call_args[0][0], pd.DataFrame)

        mock_analyze_time_series.assert_called_once()
        assert isinstance(mock_analyze_time_series.call_args[0][0], pd.DataFrame)

        # Verify DataFrame transformations
        processed_df = mock_analyze_sentiment.call_args[0][0] # Get the DataFrame passed to sentiment analysis

        # Check timestamp conversion and index setting
        assert processed_df.index.name == 'timestamp_created'
        assert pd.api.types.is_datetime64_any_dtype(processed_df.index)

        # Check detected_language and language columns
        assert 'detected_language' in processed_df.columns
        assert 'language' in processed_df.columns
        assert all(lang in ['en', 'zh-cn', 'unknown'] for lang in processed_df['detected_language'])
        assert all(lang in ['en', 'zh-cn', 'unknown'] for lang in processed_df['language'])

        # Check playtime_hours and review_length
        assert 'playtime_hours' in processed_df.columns
        assert 'review_length' in processed_df.columns
        assert processed_df['playtime_hours'].iloc[0] == 1200 / 60
        assert processed_df['review_length'].iloc[0] == len('This game is amazing! I love it.')

# async def test_main_file_not_found(mock_logging_fixture):
#     with patch('analyze_reviews.pd.read_csv', side_effect=FileNotFoundError) as mock_read_csv:
#         await main()
#         mock_read_csv.assert_called_once_with('reviews.csv')
#         mock_logging.error.assert_called_once()
#         assert "Error: The file reviews.csv was not found." in mock_logging.error.call_args[0][0]

# @pytest.mark.asyncio
# async def test_main_empty_dataframe(mock_logging_fixture):
#     with patch('analyze_reviews.pd.read_csv', return_value=pd.DataFrame()) as mock_read_csv, \
#          patch('analyze_reviews.analyze_sentiment', autospec=True) as mock_analyze_sentiment: # Ensure no analysis is called

#         await main()
#         mock_read_csv.assert_called_once_with('reviews.csv')
#         mock_logging_fixture.warning.assert_called_once()
#         assert "Input DataFrame is empty. Exiting analysis." in mock_logging_fixture.warning.call_args[0][0]
#
        

