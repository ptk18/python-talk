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

    # Filler words/phrases to remove
    FILLER_PATTERNS = [
        r'\bthe\s+turtle\b',   # "the turtle"
        r'\bturtle\b',         # "turtle"
        r'\bthe\s+pen\b',      # "the pen"
        r'\bit\s+to\b',        # "it to"
        r'\bit\b',             # "it"
        r'\bagain\b',          # "again"
        r'["\']',              # quotes
    ]

    def preprocess(self, command: str) -> str:
        """
        Normalize natural language to turtle-friendly format.

        Examples:
            "move the turtle forward 50 steps" -> "forward 50"
            "turn left 90 degrees" -> "left 90"
            "go backward 100" -> "backward 100"
        """
        processed = command.lower()

        # Remove filler words
        for pattern in self.FILLER_PATTERNS:
            processed = re.sub(pattern, '', processed, flags=re.IGNORECASE)

        # Remove punctuation
        processed = re.sub(r'[.,!?;:]+', ' ', processed)

        # Rewrite "move/go + NUMBER + direction" patterns
        # "move 50 steps forward" -> "forward 50"
        processed = re.sub(
            r'\b(move|go)\s+(\d+)\s*(?:steps?\s*)?(forward|backward|back)\b',
            r'\3 \2',
            processed
        )

        # Rewrite "move/go + direction + NUMBER" patterns
        # "move forward 50 steps" -> "forward 50"
        processed = re.sub(
            r'\b(move|go)\s+(forward|backward|back)\s*(\d+)?\s*(?:steps?)?\b',
            r'\2 \3',
            processed
        )

        # Rewrite "turn + NUMBER + direction" patterns
        # "turn 90 degrees left" -> "left 90"
        processed = re.sub(
            r'\b(turn)\s+(\d+)\s*(?:degrees?\s*)?(left|right)\b',
            r'\3 \2',
            processed
        )

        # Rewrite "turn + direction + NUMBER" patterns
        # "turn left 90 degrees" -> "left 90"
        processed = re.sub(
            r'\b(turn)\s+(left|right)\s*(\d+)?\s*(?:degrees?)?\b',
            r'\2 \3',
            processed
        )

        # Normalize whitespace
        return ' '.join(processed.split())
