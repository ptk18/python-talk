"""Turtle-specific command preprocessor"""

import re
from .base import BasePreprocessor


class TurtlePreprocessor(BasePreprocessor):
    """
    Preprocessor for turtle graphics commands.

    Normalizes natural language turtle commands to a more parseable format:
    - Removes filler words ("the turtle", "the pen", etc.)
    - Rewrites "move/go forward" patterns
    - Rewrites "turn left/right" patterns
    - Removes punctuation
    """

    FILLER_PATTERNS = [
        r"\bthe\s+turtle\b",
        r"\bturtle\b",
        r"\bthe\s+pen\b",
        r"\bit\s+to\b",
        r"\bit\b",
        r"\bagain\b",
        r'["\']',
    ]

    def preprocess(self, command: str) -> str:
        processed = command.lower()

        for pattern in self.FILLER_PATTERNS:
            processed = re.sub(pattern, "", processed, flags=re.IGNORECASE)

        processed = re.sub(r"[.,!?;:]+", " ", processed)

        processed = re.sub(
            r"\b(move|go)\s+(\d+)\s*(?:steps?\s*)?(forward|backward|back)\b",
            r"\3 \2",
            processed,
        )
        processed = re.sub(
            r"\b(move|go)\s+(forward|backward|back)\s*(\d+)?\s*(?:steps?)?\b",
            r"\2 \3",
            processed,
        )
        processed = re.sub(
            r"\b(turn)\s+(\d+)\s*(?:degrees?\s*)?(left|right)\b",
            r"\3 \2",
            processed,
        )
        processed = re.sub(
            r"\b(turn)\s+(left|right)\s*(\d+)?\s*(?:degrees?)?\b",
            r"\2 \3",
            processed,
        )

        return " ".join(processed.split())
