"""Base preprocessor interface for command preprocessing strategies"""

from abc import ABC, abstractmethod


class BasePreprocessor(ABC):
    """
    Abstract base for command preprocessing strategies.

    Preprocessors transform user commands before they're processed by the
    NLP pipeline. This allows app-specific transformations while keeping
    the core pipeline generic.
    """

    @abstractmethod
    def preprocess(self, command: str) -> str:
        """
        Transform a command before NLP processing.

        Args:
            command: The raw user command

        Returns:
            The preprocessed command ready for NLP processing
        """
        pass

    def preprocess_batch(self, commands: list[str]) -> list[str]:
        """
        Preprocess multiple commands.

        Override this for more efficient batch processing if needed.

        Args:
            commands: List of raw commands

        Returns:
            List of preprocessed commands
        """
        return [self.preprocess(cmd) for cmd in commands]
