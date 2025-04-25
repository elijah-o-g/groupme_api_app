class GroupMeScraperError(Exception):
    """Base exception for GroupMe scraper."""


class TokenMissingError(GroupMeScraperError):
    """Raised when the GROUPME_TOKEN is not provided."""


class GroupSelectionError(GroupMeScraperError):
    """Raised when an invalid group index is selected."""


class MessageFetchError(GroupMeScraperError):
    """Raised when there is an error fetching messages."""


class AggressionAnalysisError(GroupMeScraperError):
    """Raised if aggression classification fails."""


class ImageDownloadError(GroupMeScraperError):
    """Raised when downloading images fails."""


class OpenAIServiceError(GroupMeScraperError):
    """Raised when OpenAI API returns an error or fails."""
