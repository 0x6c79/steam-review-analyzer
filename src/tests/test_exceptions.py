import pytest


class TestExceptions:
    def test_steam_review_error_base(self):
        from src.steam_review.utils.exceptions import SteamReviewError

        error = SteamReviewError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_steam_review_error_with_original(self):
        from src.steam_review.utils.exceptions import SteamReviewError

        original = ValueError("Original error")
        error = SteamReviewError("Test error", original_error=original)
        assert "Test error" in str(error)
        assert error.original_error is original

    def test_scraper_error(self):
        from src.steam_review.utils.exceptions import ScraperError, SteamReviewError

        error = ScraperError("Scraper failed")
        assert isinstance(error, SteamReviewError)
        assert "Scraper failed" in str(error)

    def test_steam_api_error(self):
        from src.steam_review.utils.exceptions import SteamAPIError, SteamReviewError

        error = SteamAPIError("API failed", status_code=500)
        assert isinstance(error, SteamReviewError)
        assert error.status_code == 500

    def test_rate_limit_error(self):
        from src.steam_review.utils.exceptions import RateLimitError, SteamAPIError

        error = RateLimitError(retry_after=60)
        assert isinstance(error, SteamAPIError)
        assert error.retry_after == 60
        assert error.status_code == 429

    def test_database_error(self):
        from src.steam_review.utils.exceptions import DatabaseError, SteamReviewError

        error = DatabaseError("Database connection failed")
        assert isinstance(error, SteamReviewError)

    def test_configuration_error(self):
        from src.steam_review.utils.exceptions import (
            ConfigurationError,
            SteamReviewError,
        )

        error = ConfigurationError("Config file not found")
        assert isinstance(error, SteamReviewError)

    def test_analysis_error(self):
        from src.steam_review.utils.exceptions import AnalysisError, SteamReviewError

        error = AnalysisError("Analysis failed")
        assert isinstance(error, SteamReviewError)

    def test_validation_error(self):
        from src.steam_review.utils.exceptions import ValidationError, SteamReviewError

        error = ValidationError("Invalid input", field="app_id")
        assert isinstance(error, SteamReviewError)
        assert error.field == "app_id"

    def test_export_error(self):
        from src.steam_review.utils.exceptions import ExportError, SteamReviewError

        error = ExportError("Export failed")
        assert isinstance(error, SteamReviewError)

    def test_import_error_custom(self):
        from src.steam_review.utils.exceptions import (
            ImportError as CustomImportError,
            SteamReviewError,
        )

        error = CustomImportError("Import failed")
        assert isinstance(error, SteamReviewError)

    def test_exception_hierarchy(self):
        from src.steam_review.utils.exceptions import (
            ScraperError,
            SteamAPIError,
            RateLimitError,
            DatabaseError,
            ConfigurationError,
            AnalysisError,
            ValidationError,
            ExportError,
            ImportError,
            SteamReviewError,
        )

        # All custom exceptions should inherit from SteamReviewError
        assert issubclass(ScraperError, SteamReviewError)
        assert issubclass(SteamAPIError, SteamReviewError)
        assert issubclass(RateLimitError, SteamAPIError)
        assert issubclass(DatabaseError, SteamReviewError)
        assert issubclass(ConfigurationError, SteamReviewError)
        assert issubclass(AnalysisError, SteamReviewError)
        assert issubclass(ValidationError, SteamReviewError)
        assert issubclass(ExportError, SteamReviewError)
        assert issubclass(ImportError, SteamReviewError)
