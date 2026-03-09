import pytest
import asyncio
import csv
import builtins
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp
from pathlib import Path

from src.steam_review.scraper.steam_review_scraper import (
    get_reviews,
    flatten_review,
    main,
)


@pytest.fixture
def mock_session():
    return AsyncMock(spec=aiohttp.ClientSession)


@pytest.mark.asyncio
async def test_get_reviews_success(mock_session):
    mock_response = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "success": 1,
            "reviews": [{"review_id": 1, "review": "good"}],
            "cursor": "next_cursor",
        }
    )
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value.__aenter__.return_value = mock_response

    app_id = "123"
    reviews_data = await get_reviews(mock_session, app_id)

    assert reviews_data["success"] == 1
    assert len(reviews_data["reviews"]) == 1
    mock_session.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_reviews_rate_limit(mock_session):
    mock_response_429 = MagicMock()
    mock_response_429.raise_for_status.side_effect = aiohttp.ClientResponseError(
        request_info=MagicMock(), history=(), status=429, headers={"Retry-After": "0"}
    )
    mock_response_success = MagicMock()
    mock_response_success.json.return_value = {
        "success": 1,
        "reviews": [],
        "cursor": "next_cursor",
    }
    mock_response_success.raise_for_status.return_value = None

    mock_session.get.side_effect = [
        aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=429,
            headers={"Retry-After": "0"},
        ),
    ]

    app_id = "123"
    with patch("asyncio.sleep", new=AsyncMock()) as mock_sleep:
        reviews_data = await get_reviews(
            mock_session, app_id, retries=1, backoff_factor=0
        )
        assert reviews_data is None
        assert mock_session.get.call_count == 1
        assert mock_sleep.call_count >= 1


def test_flatten_review():
    nested_review = {
        "review_id": 1,
        "review": "Test review",
        "author": {"steamid": "12345", "num_games_owned": 10, "playtime_forever": 100},
        "voted_up": True,
    }
    flattened = flatten_review(nested_review)
    assert "review_id" in flattened
    assert "author.steamid" in flattened
    assert "author.num_games_owned" in flattened
    assert "author.playtime_forever" in flattened
    assert "author" not in flattened  # Original 'author' key should be removed
    assert flattened["author.steamid"] == "12345"


@pytest.mark.asyncio
async def test_main_function_csv_writing(tmp_path):
    mock_reviews_data = {
        "success": 1,
        "reviews": [
            {
                "review_id": 1,
                "review": "Test 1",
                "author": {"steamid": "1"},
                "voted_up": True,
            },
            {
                "review_id": 2,
                "review": "Test 2",
                "author": {"steamid": "2"},
                "voted_up": False,
            },
        ],
        "cursor": "next_cursor",
    }

    mock_app_name = "TestGame"
    app_id = "test_app"
    expected_filename = f"{mock_app_name}_{app_id}_reviews.csv"

    # Mock get_reviews and get_app_details
    with (
        patch(
            "src.steam_review.scraper.steam_review_scraper.get_reviews",
            new=AsyncMock(return_value=mock_reviews_data),
        ) as mock_get_reviews,
        patch(
            "src.steam_review.scraper.steam_review_scraper.get_app_details",
            new=AsyncMock(return_value=mock_app_name),
        ) as mock_get_app_details,
    ):
        # Mock aiohttp.ClientSession to prevent actual network calls
        # This mock needs to correctly handle the async with statement
        mock_session_get = AsyncMock()
        mock_session_get.__aenter__.return_value = (
            mock_session_get  # Return self for async with
        )
        mock_session_get.__aexit__.return_value = (
            None  # No specific exit behavior needed
        )

        with patch(
            "aiohttp.ClientSession", return_value=mock_session_get
        ) as mock_client_session_constructor:
            # Redirect output to a temporary CSV file with the expected dynamic name
            output_csv_path = tmp_path / expected_filename

            # Mock builtins.open to write to our temporary path
            # We need to ensure that the open call in main() uses our mocked path
            original_open = builtins.open

            def mock_open(
                file,
                mode="r",
                buffering=-1,
                encoding=None,
                errors=None,
                newline=None,
                closefd=True,
            ):
                if isinstance(file, (str, Path)) and str(file).endswith(
                    expected_filename
                ):
                    return original_open(
                        output_csv_path,
                        mode,
                        buffering,
                        encoding,
                        errors,
                        newline,
                        closefd,
                    )
                return original_open(
                    file, mode, buffering, encoding, errors, newline, closefd
                )

            with patch("builtins.open", new=mock_open):
                await main(app_id=app_id, limit=2)

            # Verify get_app_details and get_reviews were called
            mock_get_app_details.assert_called_once_with(mock_session_get, app_id)
            mock_get_reviews.assert_called_once_with(mock_session_get, app_id, "*")

            # Read the created CSV and verify content
            with open(output_csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["review_id"] == "1"
                assert rows[1]["review"] == "Test 2"
                assert "author.steamid" in rows[0]
                assert rows[0]["author.steamid"] == "1"
                assert rows[1]["voted_up"] == "False"  # CSV writes boolean as string
