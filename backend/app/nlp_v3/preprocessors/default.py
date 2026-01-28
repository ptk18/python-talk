"""Default no-op preprocessor - passes commands through unchanged"""

from .base import BasePreprocessor


class DefaultPreprocessor(BasePreprocessor):
    """
    No-op preprocessor that passes commands through unchanged.

    Used when no special preprocessing is needed (e.g., Codespace app).
    """

    def preprocess(self, command: str) -> str:
        """Return command unchanged"""
        return command
