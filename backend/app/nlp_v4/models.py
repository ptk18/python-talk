"""Data models for NLP v4 pipeline"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class MethodInfo:
    """Information about an extracted method."""
    name: str
    params: List[str]
    docstring: Optional[str]
    param_types: Optional[Dict[str, str]] = None

    def to_searchable_text(self) -> str:
        text = self.name.replace("_", " ")
        if self.docstring:
            text += f" {self.docstring}"
        return text


@dataclass
class MatchResult:
    """Result of matching a command to a method."""
    method_name: str
    similarity: float
    extracted_params: Dict[str, str] = field(default_factory=dict)
    method_description: str = ""

    def get_method_call(self) -> str:
        if not self.extracted_params:
            return f"{self.method_name}()"
        params_str = ", ".join(
            f"{k}={repr(v)}" for k, v in self.extracted_params.items()
        )
        return f"{self.method_name}({params_str})"

    def explain(self) -> str:
        return "\n".join([
            f"Method: {self.get_method_call()}",
            f"Similarity: {self.similarity:.1%}",
            f"Description: {self.method_description}",
        ])
