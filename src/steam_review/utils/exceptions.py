"""
Custom exceptions for Steam Review Analyzer
"""


class SteamReviewError(Exception):
    """Base exception for Steam Review Analyzer"""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.original_error:
            return f"{self.message} (caused by: {self.original_error})"
        return self.message


class ScraperError(SteamReviewError):
    """Exception raised for scraper-related errors"""

    pass


class SteamAPIError(SteamReviewError):
    """Exception raised for Steam API errors"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        original_error: Exception | None = None,
    ):
        self.status_code = status_code
        super().__init__(message, original_error)


class RateLimitError(SteamAPIError):
    """Exception raised when Steam API rate limit is hit"""

    def __init__(
        self,
        message: str = "Steam API rate limit exceeded",
        retry_after: int | None = None,
    ):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)


class DatabaseError(SteamReviewError):
    """Exception raised for database-related errors"""

    pass


class ConfigurationError(SteamReviewError):
    """Exception raised for configuration errors"""

    pass


class AnalysisError(SteamReviewError):
    """Exception raised for analysis-related errors"""

    pass


class ValidationError(SteamReviewError):
    """Exception raised for data validation errors"""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


class ExportError(SteamReviewError):
    """Exception raised for export-related errors"""

    pass


class ImportError(SteamReviewError):
    """Exception raised for import-related errors"""

    pass
