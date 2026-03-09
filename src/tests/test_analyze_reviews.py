import pytest
import pytest_asyncio
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio


@pytest.fixture
def sample_dataframe():
    data = {
        "review": [
            "This game is amazing! I love it.",
            "It's okay, but could be better.",
            "Terrible game, full of bugs.",
            "一款非常棒的游戏，我喜欢它。",
            "",
            "   ",
        ],
        "timestamp_created": [
            1678886400,
            1678972800,
            1679059200,
            1679145600,
            1679232000,
            1679318400,
        ],
        "author.playtime_forever": [1200, 300, 50, 600, 0, 10],
        "voted_up": [True, True, False, True, True, False],
    }
    df = pd.DataFrame(data)
    return df


@pytest.mark.asyncio
async def test_detect_language_robust():
    from src.steam_review.analysis.analyze_reviews import detect_language_robust

    assert detect_language_robust("This is a great game") == "en"
    assert detect_language_robust("这是一个好游戏") in ["zh-cn", "zh-tw", "ko-ja"]
    assert detect_language_robust("") == "unknown"
    assert detect_language_robust("   ") == "unknown"


def test_detect_language_robust_french():
    from src.steam_review.analysis.analyze_reviews import detect_language_robust

    result = detect_language_robust("Ce jeu est incroyable")
    assert result in ["fr", "en"]


def test_analyze_reviews_import():
    from src.steam_review.analysis import analyze_reviews

    assert analyze_reviews is not None
    assert hasattr(analyze_reviews, "detect_language_robust")
    assert hasattr(analyze_reviews, "main")
    assert hasattr(analyze_reviews, "USE_ENHANCED_SENTIMENT")


def test_sentiment_analysis_import():
    from src.steam_review.analysis import sentiment_analysis

    assert sentiment_analysis is not None


def test_keyword_analysis_import():
    from src.steam_review.analysis import keyword_analysis

    assert keyword_analysis is not None


def test_correlation_analysis_import():
    from src.steam_review.analysis import correlation_analysis

    assert correlation_analysis is not None


def test_time_series_analysis_import():
    from src.steam_review.analysis import time_series_analysis

    assert time_series_analysis is not None
