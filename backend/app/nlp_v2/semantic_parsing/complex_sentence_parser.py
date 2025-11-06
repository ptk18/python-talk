"""
Complex sentence parser for handling loops, conditionals, and conjunctions
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import re


@dataclass
class CommandNode:
    """Represents a single command or control structure"""
    type: str  # 'action', 'loop', 'conditional', 'sequence'
    text: str
    children: List['CommandNode'] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []
        if self.metadata is None:
            self.metadata = {}


class ComplexSentenceParser:
    """Parse complex sentences into executable command trees"""

    # Conjunction patterns
    CONJUNCTIONS = ['and', 'then', 'after that', 'followed by', 'next', 'also', 'plus']

    # Loop patterns
    LOOP_PATTERNS = [
        (r'repeat\s+(\d+)\s+times?\s*[:;]?\s*(.+)', 'repeat_times'),
        (r'do\s+(.+?)\s+(\d+)\s+times?', 'do_times'),
        (r'(\d+)\s+times?\s*[:;]?\s*(.+)', 'times_action'),
        (r'for\s+(\d+)\s+times?\s*[:;]?\s*(.+)', 'for_times'),
        (r'loop\s+(\d+)\s+times?\s*[:;]?\s*(.+)', 'loop_times'),
    ]

    # Conditional patterns
    CONDITIONAL_PATTERNS = [
        (r'if\s+(.+?)\s+then\s+(.+)', 'if_then'),
        (r'when\s+(.+?)\s+then\s+(.+)', 'when_then'),
        (r'if\s+(.+?),\s*(.+)', 'if_comma'),
        (r'when\s+(.+?),\s*(.+)', 'when_comma'),
    ]

    # Conditional operators
    CONDITION_OPERATORS = {
        'greater than': '>',
        'less than': '<',
        'equal to': '==',
        'equals': '==',
        'is': '==',
        'not equal to': '!=',
        'at least': '>=',
        'at most': '<=',
    }

    def parse(self, text: str) -> CommandNode:
        """Main entry point - parse text into command tree"""
        text = text.strip()

        # Try loop patterns first
        loop_result = self._parse_loop(text)
        if loop_result:
            return loop_result

        # Try conditional patterns
        conditional_result = self._parse_conditional(text)
        if conditional_result:
            return conditional_result

        # Try conjunction splitting
        sequence_result = self._parse_sequence(text)
        if sequence_result:
            return sequence_result

        # Default: single action
        return CommandNode(type='action', text=text)

    def _parse_loop(self, text: str) -> Optional[CommandNode]:
        """Parse loop constructs"""
        for pattern, pattern_type in self.LOOP_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()

                # Extract iterations and body
                if pattern_type in ['repeat_times', 'times_action', 'for_times', 'loop_times']:
                    iterations = int(groups[0])
                    body_text = groups[1] if len(groups) > 1 else groups[0]
                elif pattern_type == 'do_times':
                    body_text = groups[0]
                    iterations = int(groups[1])

                # Parse body (might contain sequences)
                body_node = self._parse_sequence(body_text.strip())

                return CommandNode(
                    type='loop',
                    text=text,
                    metadata={'iterations': iterations},
                    children=[body_node] if body_node else []
                )

        return None

    def _parse_conditional(self, text: str) -> Optional[CommandNode]:
        """Parse conditional constructs"""
        for pattern, pattern_type in self.CONDITIONAL_PATTERNS:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                condition_text = match.group(1).strip()
                action_text = match.group(2).strip()

                # Parse condition
                condition = self._parse_condition(condition_text)

                # Parse action (might be a sequence)
                action_node = self._parse_sequence(action_text)

                return CommandNode(
                    type='conditional',
                    text=text,
                    metadata={'condition': condition, 'condition_text': condition_text},
                    children=[action_node] if action_node else []
                )

        return None

    def _parse_condition(self, condition_text: str) -> Dict[str, Any]:
        """Parse condition into structured format"""
        # Try to identify comparison operators
        for op_text, op_symbol in self.CONDITION_OPERATORS.items():
            if op_text in condition_text.lower():
                parts = re.split(op_text, condition_text, flags=re.IGNORECASE)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()

                    # Extract numeric value if present
                    num_match = re.search(r'(-?\d+(?:\.\d+)?)', right)
                    if num_match:
                        right_value = float(num_match.group(1))
                    else:
                        right_value = right

                    return {
                        'left': left,
                        'operator': op_symbol,
                        'right': right_value,
                        'raw': condition_text
                    }

        # If no operator found, treat as boolean check (e.g., "pen is down")
        return {
            'type': 'boolean_check',
            'expression': condition_text,
            'raw': condition_text
        }

    def _parse_sequence(self, text: str) -> Optional[CommandNode]:
        """Parse conjunctions into sequence of commands"""
        # Split by conjunctions
        parts = self._split_by_conjunctions(text)

        if len(parts) <= 1:
            # Not a sequence, try nested parsing
            loop = self._parse_loop(text)
            if loop:
                return loop
            cond = self._parse_conditional(text)
            if cond:
                return cond
            return CommandNode(type='action', text=text)

        # Create sequence node with each part as child
        children = []
        for part in parts:
            part = part.strip()
            if part:
                # Recursively parse each part (might contain loops/conditionals)
                child = self.parse(part)
                children.append(child)

        return CommandNode(
            type='sequence',
            text=text,
            children=children
        )

    def _split_by_conjunctions(self, text: str) -> List[str]:
        """Split text by conjunctions while preserving nested structures"""
        # First pass: identify which "and"s are arithmetic
        tokens = text.split()
        arithmetic_and_indices = set()

        for i, token in enumerate(tokens):
            if token.lower() == 'and':
                # Build current_tokens up to this point
                current_tokens = tokens[:i]
                if self._is_arithmetic_and(tokens, i, current_tokens):
                    arithmetic_and_indices.add(i)

        # Second pass: split by conjunctions, skipping arithmetic "and"s
        parts = []
        current = []
        i = 0

        while i < len(tokens):
            # Check if this position is a conjunction
            is_conjunction = False
            for conj in self.CONJUNCTIONS:
                conj_words = conj.split()
                if i + len(conj_words) <= len(tokens):
                    window = ' '.join(tokens[i:i+len(conj_words)]).lower()
                    if window == conj:
                        # Special case: skip arithmetic "and"
                        if conj == 'and' and i in arithmetic_and_indices:
                            current.append(tokens[i])
                            i += 1
                            is_conjunction = False
                            break

                        # Found real conjunction - split here
                        if current:
                            parts.append(' '.join(current))
                            current = []
                        i += len(conj_words)
                        is_conjunction = True
                        break

            if not is_conjunction:
                current.append(tokens[i])
                i += 1

        # Add remaining
        if current:
            parts.append(' '.join(current))

        return parts if len(parts) > 1 else [text]

    def _is_arithmetic_and(self, tokens: List[str], and_index: int, current_tokens: List[str]) -> bool:
        """Check if 'and' is used in arithmetic context (e.g., 'add 2 and 3')"""
        # Arithmetic operation verbs
        arithmetic_verbs = ['add', 'sum', 'plus', 'subtract', 'minus', 'multiply', 'times', 'divide', 'by']

        # Check if there's an arithmetic verb in the current part
        has_arithmetic_verb = any(token.lower() in arithmetic_verbs for token in current_tokens)

        # Check if there are numbers before "and"
        has_number_before = and_index > 0 and any(char.isdigit() for char in tokens[and_index - 1])

        # Check if there's a number after "and"
        has_number_after = (and_index + 1 < len(tokens) and
                           any(char.isdigit() for char in tokens[and_index + 1]))

        # If we have arithmetic verb and numbers on both sides, this is arithmetic "and"
        return has_arithmetic_verb and has_number_before and has_number_after


def print_command_tree(node: CommandNode, indent: int = 0) -> None:
    """Debug utility to visualize command tree"""
    prefix = "  " * indent
    print(f"{prefix}{node.type.upper()}: {node.text[:50]}...")
    if node.metadata:
        print(f"{prefix}  metadata: {node.metadata}")
    for child in node.children:
        print_command_tree(child, indent + 1)
