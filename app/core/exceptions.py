class DebateError(Exception):
    """Base debate error."""


class DebateNotFound(DebateError):
    """Raised when a session cannot be found."""


class InvalidStateTransition(DebateError):
    """Raised when an action is invalid for the current phase."""


class InvalidDebateAction(DebateError):
    """Raised when an action breaks business rules."""

