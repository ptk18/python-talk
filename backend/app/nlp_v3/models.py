"""Data models for NLP v3 pipeline"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class MethodInfo:
    name: str
    params: List[str]
    docstring: Optional[str]

    def to_searchable_text(self) -> str:
        text = self.name.replace('_', ' ')
        if self.docstring:
            text += f" {self.docstring}"
        return text


@dataclass
class MatchScore:
    method_name: str
    total_score: float
    semantic_score: float
    intent_score: float
    synonym_boost: float
    param_relevance: float
    phrasal_verb_match: float
    extracted_params: Dict[str, str]

    def get_method_call(self) -> str:
        if not self.extracted_params:
            return f"{self.method_name}()"
        params_str = ", ".join(f"{k}={repr(v)}" for k, v in self.extracted_params.items())
        return f"{self.method_name}({params_str})"

    def explain(self) -> str:
        explanation = [
            f"Method: {self.get_method_call()}",
            f"Total Confidence: {self.total_score:.1%}",
            "",
            "Breakdown:",
            f"  Semantic similarity: {self.semantic_score:.1%}",
            f"  Intent classification: {self.intent_score:.1%}",
            f"  Synonym boost: {self.synonym_boost:.1%}",
            f"  Parameter relevance: {self.param_relevance:.1%}",
            f"  Phrasal verb match: {self.phrasal_verb_match:.1%}",
        ]
        return "\n".join(explanation)
