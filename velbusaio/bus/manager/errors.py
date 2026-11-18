"""Signum Manager client errors."""


class VelbusManagerError(OSError):
    """HTTP or transport failure while talking to the Signum Manager."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        """Initialize the exception."""
        super().__init__(message)
        self.status = status
