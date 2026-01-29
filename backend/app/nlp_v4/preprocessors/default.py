"""Default no-op preprocessor - passes commands through unchanged"""

from .base import BasePreprocessor


class DefaultPreprocessor(BasePreprocessor):
    """No-op preprocessor that passes commands through unchanged."""

    def preprocess(self, command: str) -> str:
        return command
