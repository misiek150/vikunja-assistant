class DomainError(Exception):
    """Base exception for assistant errors."""


class ConfigurationError(DomainError):
    """Missing or inconsistent configuration."""


class AnalysisError(DomainError):
    """Screenshot analysis failed or returned unusable data."""


class VikunjaError(DomainError):
    """Vikunja API request failed."""
