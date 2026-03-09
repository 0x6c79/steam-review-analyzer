import pytest
import asyncio
import os
import csv
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp


class TestFlattenReview:
    def test_flatten_review_basic(self):
        from src.steam_review.scraper.steam_review_scraper import flatten_review

        review = {
            "review_id": 1,
            "review": "Test review",
            "author": {
                "steamid": "12345",
                "num_games_owned": 10,
                "playtime_forever": 100,
            },
            "voted_up": True,
        }
        flattened = flatten_review(review)
        assert "review_id" in flattened
        assert flattened["review_id"] == 1
        assert "review" in flattened
        assert "author" not in flattened
        assert "author.steamid" in flattened
        assert flattened["author.steamid"] == "12345"
        assert flattened["author.num_games_owned"] == 10
        assert flattened["author.playtime_forever"] == 100

    def test_flatten_review_no_author(self):
        from src.steam_review.scraper.steam_review_scraper import flatten_review

        review = {"review_id": 1, "review": "Test review"}
        flattened = flatten_review(review)
        assert flattened["review_id"] == 1
        assert flattened["review"] == "Test review"
        assert "author" not in flattened

    def test_flatten_review_empty_author(self):
        from src.steam_review.scraper.steam_review_scraper import flatten_review

        review = {"review_id": 1, "review": "Test", "author": {}}
        flattened = flatten_review(review)
        assert flattened["review_id"] == 1
        assert "author" not in flattened

    def test_flatten_review_preserves_other_fields(self):
        from src.steam_review.scraper.steam_review_scraper import flatten_review

        review = {
            "review": "Test",
            "voted_up": True,
            "language": "english",
            "author": {"steamid": "123"},
        }
        flattened = flatten_review(review)
        assert flattened["voted_up"] is True
        assert flattened["language"] == "english"


class TestLoadExistingReviewIds:
    def test_load_existing_review_ids_nonexistent_file(self):
        from src.steam_review.scraper.steam_review_scraper import (
            load_existing_review_ids,
        )

        result = load_existing_review_ids("/nonexistent/path/file.csv")
        assert result == set()

    def test_load_existing_review_ids_with_file(self, tmp_path):
        from src.steam_review.scraper.steam_review_scraper import (
            load_existing_review_ids,
        )

        csv_file = tmp_path / "test_reviews.csv"
        csv_file.write_text(
            "recommendation_id,review,language\n1,Test1,en\n2,Test2,en\n",
            encoding="utf-8",
        )
        result = load_existing_review_ids(str(csv_file))
        assert "1" in result
        assert "2" in result

    def test_load_existing_review_ids_with_alternate_column_name(self, tmp_path):
        from src.steam_review.scraper.steam_review_scraper import (
            load_existing_review_ids,
        )

        csv_file = tmp_path / "test_reviews.csv"
        csv_file.write_text(
            "recommendationid,review,language\n1,Test1,en\n2,Test2,en\n",
            encoding="utf-8",
        )
        result = load_existing_review_ids(str(csv_file))
        assert "1" in result
        assert "2" in result


class TestCheckpoint:
    def test_save_checkpoint(self, tmp_path):
        from src.steam_review.scraper.steam_review_scraper import save_checkpoint

        app_id = "test_app"
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            save_checkpoint(app_id, "cursor123", 100)
            checkpoint_file = f".checkpoint_{app_id}.txt"
            assert os.path.exists(checkpoint_file)
            with open(checkpoint_file, "r") as f:
                content = f.read()
            assert "cursor123" in content
            assert "100" in content
        finally:
            os.chdir(old_cwd)

    def test_load_checkpoint_exists(self, tmp_path):
        from src.steam_review.scraper.steam_review_scraper import (
            save_checkpoint,
            load_checkpoint,
        )

        app_id = "test_app"
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            save_checkpoint(app_id, "cursor456", 200)
            cursor, total = load_checkpoint(app_id)
            assert cursor == "cursor456"
            assert total == 200
            assert not os.path.exists(f".checkpoint_{app_id}.txt")
        finally:
            os.chdir(old_cwd)

    def test_load_checkpoint_nonexistent(self, tmp_path):
        from src.steam_review.scraper.steam_review_scraper import load_checkpoint

        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            cursor, total = load_checkpoint("nonexistent_app")
            assert cursor == "*"
            assert total == 0
        finally:
            os.chdir(old_cwd)


class TestGetAppDetails:
    @pytest.mark.asyncio
    async def test_get_app_details_success(self):
        from src.steam_review.scraper.steam_review_scraper import get_app_details

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json = AsyncMock(
            return_value={"12345": {"success": True, "data": {"name": "Test Game"}}}
        )
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await get_app_details(mock_session, "12345")
        assert result == "Test Game"

    @pytest.mark.asyncio
    async def test_get_app_details_failure(self):
        from src.steam_review.scraper.steam_review_scraper import get_app_details

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.json = AsyncMock(return_value={"12345": {"success": False}})
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await get_app_details(mock_session, "12345")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_app_details_network_error(self):
        from src.steam_review.scraper.steam_review_scraper import get_app_details

        mock_session = MagicMock()
        mock_session.get.side_effect = aiohttp.ClientError("Network error")

        result = await get_app_details(mock_session, "12345")
        assert result is None


class TestGetReviews:
    @pytest.mark.asyncio
    async def test_get_reviews_success(self):
        from src.steam_review.scraper.steam_review_scraper import get_reviews

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"success": 1, "reviews": [], "cursor": "next"}
        )
        mock_response.raise_for_status = MagicMock()
        mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)

        result = await get_reviews(mock_session, "12345")
        assert result["success"] == 1

    @pytest.mark.asyncio
    async def test_get_reviews_rate_limit_429(self):
        from src.steam_review.scraper.steam_review_scraper import get_reviews

        mock_session = AsyncMock()
        mock_response = MagicMock()
        mock_response.status = 429
        mock_response.headers = {"Retry-After": "1"}
        mock_response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=429,
            headers={"Retry-After": "1"},
        )
        mock_session.get.return_value.__aenter__.return_value = mock_response

        with patch("asyncio.sleep", new=AsyncMock()):
            result = await get_reviews(
                mock_session, "12345", retries=1, backoff_factor=0
            )

    @pytest.mark.asyncio
    async def test_get_reviews_timeout(self):
        from src.steam_review.scraper.steam_review_scraper import get_reviews

        mock_session = AsyncMock()
        mock_session.get.side_effect = asyncio.TimeoutError()

        with patch("asyncio.sleep", new=AsyncMock()):
            result = await get_reviews(
                mock_session, "12345", retries=1, backoff_factor=0
            )
            assert result is None


class TestScraperModule:
    def test_scraper_import(self):
        from src.steam_review.scraper import steam_review_scraper

        assert steam_review_scraper is not None

    def test_default_timeout(self):
        from src.steam_review.scraper.steam_review_scraper import DEFAULT_TIMEOUT

        assert DEFAULT_TIMEOUT.total == 10
