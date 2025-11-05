import re
from dataclasses import dataclass
from typing import Any, List, Optional, Union
from enum import Enum

class ExpressionType(Enum):
    NUMERIC = "numeric"
    COMPARISON = "comparison"
    LOGICAL = "logical"
    ARITHMETIC = "arithmetic"
    STRING = "string"

class Operator(Enum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER = ">"
    LESS = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    AND = "and"
    OR = "or"
    NOT = "not"

@dataclass
class Expression:
    expr_type: ExpressionType
    operator: Optional[Operator]
    left: Any
    right: Any = None
    raw: str = ""

class ExpressionParser:
    def __init__(self):
        self.numeric_pattern = re.compile(r'-?\d+\.?\d*')
        self.comparison_words = {
            "greater than": Operator.GREATER,
            "more than": Operator.GREATER,
            "less than": Operator.LESS,
            "fewer than": Operator.LESS,
            "equal to": Operator.EQUAL,
            "equals": Operator.EQUAL,
            "is": Operator.EQUAL,
            "at least": Operator.GREATER_EQUAL,
            "at most": Operator.LESS_EQUAL
        }
        self.arithmetic_words = {
            "plus": Operator.ADD,
            "add": Operator.ADD,
            "minus": Operator.SUBTRACT,
            "subtract": Operator.SUBTRACT,
            "times": Operator.MULTIPLY,
            "multiply": Operator.MULTIPLY,
            "divided by": Operator.DIVIDE,
            "divide": Operator.DIVIDE
        }

    def parse(self, text: str) -> List[Expression]:
        text = text.lower().strip()
        expressions = []

        numeric_expr = self._parse_numeric(text)
        if numeric_expr:
            expressions.append(numeric_expr)

        comparison_expr = self._parse_comparison(text)
        if comparison_expr:
            expressions.append(comparison_expr)

        arithmetic_expr = self._parse_arithmetic(text)
        if arithmetic_expr:
            expressions.append(arithmetic_expr)

        logical_expr = self._parse_logical(text)
        if logical_expr:
            expressions.append(logical_expr)

        return expressions

    def _parse_numeric(self, text: str) -> Optional[Expression]:
        numbers = self.numeric_pattern.findall(text)
        if numbers:
            value = float(numbers[0]) if '.' in numbers[0] else int(numbers[0])
            return Expression(
                expr_type=ExpressionType.NUMERIC,
                operator=None,
                left=value,
                raw=numbers[0]
            )
        return None

    def _parse_comparison(self, text: str) -> Optional[Expression]:
        for phrase, operator in self.comparison_words.items():
            if phrase in text:
                parts = text.split(phrase)
                if len(parts) == 2:
                    left = self._extract_value(parts[0])
                    right = self._extract_value(parts[1])
                    if left is not None and right is not None:
                        return Expression(
                            expr_type=ExpressionType.COMPARISON,
                            operator=operator,
                            left=left,
                            right=right,
                            raw=text
                        )
        return None

    def _parse_arithmetic(self, text: str) -> Optional[Expression]:
        for phrase, operator in self.arithmetic_words.items():
            if phrase in text:
                parts = text.split(phrase)
                if len(parts) == 2:
                    left = self._extract_numeric(parts[0])
                    right = self._extract_numeric(parts[1])
                    if left is not None and right is not None:
                        return Expression(
                            expr_type=ExpressionType.ARITHMETIC,
                            operator=operator,
                            left=left,
                            right=right,
                            raw=text
                        )
        return None

    def _parse_logical(self, text: str) -> Optional[Expression]:
        if " and " in text:
            parts = text.split(" and ")
            return Expression(
                expr_type=ExpressionType.LOGICAL,
                operator=Operator.AND,
                left=parts[0].strip(),
                right=parts[1].strip(),
                raw=text
            )
        elif " or " in text:
            parts = text.split(" or ")
            return Expression(
                expr_type=ExpressionType.LOGICAL,
                operator=Operator.OR,
                left=parts[0].strip(),
                right=parts[1].strip(),
                raw=text
            )
        return None

    def _extract_value(self, text: str) -> Optional[Union[int, float, str]]:
        text = text.strip()
        numeric = self._extract_numeric(text)
        if numeric is not None:
            return numeric
        words = text.split()
        return words[-1] if words else None

    def _extract_numeric(self, text: str) -> Optional[Union[int, float]]:
        numbers = self.numeric_pattern.findall(text)
        if numbers:
            num_str = numbers[0]
            return float(num_str) if '.' in num_str else int(num_str)
        return None

    def evaluate_arithmetic(self, expr: Expression) -> Optional[Union[int, float]]:
        if expr.expr_type != ExpressionType.ARITHMETIC:
            return None

        left = expr.left
        right = expr.right

        if expr.operator == Operator.ADD:
            return left + right
        elif expr.operator == Operator.SUBTRACT:
            return left - right
        elif expr.operator == Operator.MULTIPLY:
            return left * right
        elif expr.operator == Operator.DIVIDE:
            return left / right if right != 0 else None
        elif expr.operator == Operator.MODULO:
            return left % right if right != 0 else None

        return None

    def evaluate_comparison(self, expr: Expression) -> Optional[bool]:
        if expr.expr_type != ExpressionType.COMPARISON:
            return None

        left = expr.left
        right = expr.right

        if expr.operator == Operator.EQUAL:
            return left == right
        elif expr.operator == Operator.NOT_EQUAL:
            return left != right
        elif expr.operator == Operator.GREATER:
            return left > right
        elif expr.operator == Operator.LESS:
            return left < right
        elif expr.operator == Operator.GREATER_EQUAL:
            return left >= right
        elif expr.operator == Operator.LESS_EQUAL:
            return left <= right

        return None
