"""Velbus exceptions."""


class VelbusException(Exception):
    """Velbus Exception."""

    def __init__(self, value: str) -> None:
        """Initialize the exception."""
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        """Return the exception as a string."""
        return repr(self.value)


class VelbusConnectionFailed(VelbusException):
    """Exception for connection setup failure."""

    def __init__(self) -> None:
        """Initialize the exception."""
        super().__init__("Connection setup failed")


class VelbusConnectionTerminated(VelbusException):
    """Exception for connection termination."""

    def __init__(self) -> None:
        """Initialize the exception."""
        super().__init__("Connection terminated")
