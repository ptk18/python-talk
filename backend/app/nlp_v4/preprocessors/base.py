"""Base preprocessor interface for command preprocessing strategies"""

from abc import ABC, abstractmethod


class BasePreprocessor(ABC):
    """Abstract base for command preprocessing strategies."""

    @abstractmethod
    def preprocess(self, command: str) -> str:
        pass

    def preprocess_batch(self, commands: list[str]) -> list[str]:
        return [self.preprocess(cmd) for cmd in commands]
