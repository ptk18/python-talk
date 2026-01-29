"""
NLP v4 Service - Unified interface for command processing

Same public API as v3 NLPService so routers can swap with minimal changes.
"""

from typing import List, Any, Optional
from dataclasses import dataclass

from .extractors.base import BaseExtractor
from .preprocessors.base import BasePreprocessor
from .preprocessors.default import DefaultPreprocessor
from .models import MethodInfo

from .pipeline import NLPPipeline
from .models import MatchResult


SUGGESTION_THRESHOLD = 0.40  # Below this confidence = "suggestion" instead of "matched"


@dataclass
class ProcessResult:
    """Result of processing a command (v3-compatible interface)."""
    success: bool
    method_name: str
    parameters: dict
    confidence: float
    executable: str
    explanation: str
    breakdown: dict
    action_verb: str = ""
    status: str = "matched"  # "matched" | "suggestion" | "no_match"

    @classmethod
    def from_match_result(cls, match: MatchResult) -> "ProcessResult":
        confidence_pct = match.similarity * 100
        status = "matched" if match.similarity >= SUGGESTION_THRESHOLD else "suggestion"
        return cls(
            success=True,
            method_name=match.method_name,
            parameters=match.extracted_params,
            confidence=confidence_pct,
            executable=match.get_method_call(),
            explanation=match.explain(),
            breakdown={
                "semantic_similarity": confidence_pct,
            },
            action_verb=match.method_name,
            status=status,
        )


class NLPService:
    """
    Semantic-first NLP service using all-mpnet-base-v2.

    Drop-in replacement for nlp_v3.NLPService with the same public API.

    Example:
        service = NLPService(extractor=ASTExtractor())
        service.initialize(user_code)
        results = service.process("add 2 and 3")
    """

    DEFAULT_CONFIDENCE_THRESHOLD = 0.15

    def __init__(
        self,
        extractor: BaseExtractor,
        preprocessor: BasePreprocessor = None,
        confidence_threshold: float = None,
    ):
        self.extractor = extractor
        self.preprocessor = preprocessor or DefaultPreprocessor()
        self.confidence_threshold = confidence_threshold or self.DEFAULT_CONFIDENCE_THRESHOLD

        self._pipeline: Optional[NLPPipeline] = None
        self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def methods(self) -> List[MethodInfo]:
        return self.extractor.methods

    def initialize(self, source: Any) -> List[MethodInfo]:
        """Initialize the service with a method source."""
        methods = self.extractor.extract(source)

        self._pipeline = NLPPipeline()
        self._pipeline.initialize(methods)

        self._initialized = True
        return methods

    def process(
        self,
        command: str,
        language: str = "en",
        top_k: int = None,
    ) -> List[ProcessResult]:
        """Process a natural language command."""
        if not self._initialized:
            raise RuntimeError("NLPService not initialized. Call initialize() first.")

        processed_command = self.preprocessor.preprocess(command)

        raw_results = self._pipeline.process_command(
            processed_command,
            top_k=top_k or 5,
        )

        results = []
        for match in raw_results:
            if match.similarity >= self.confidence_threshold:
                results.append(ProcessResult.from_match_result(match))

        return results

    def process_and_format(
        self,
        command: str,
        language: str = "en",
    ) -> dict:
        """Process command and return formatted response dict."""
        results = self.process(command, language)

        if not results:
            return {
                "success": False,
                "results": [],
                "result": {
                    "success": False,
                    "message": f"No confident matches found (threshold: {self.confidence_threshold*100:.0f}%)",
                    "confidence": 0.0,
                },
                "command_count": 0,
            }

        formatted_results = []
        for r in results:
            formatted_results.append({
                "success": r.success,
                "method": r.method_name,
                "parameters": r.parameters,
                "confidence": r.confidence,
                "executable": r.executable,
                "explanation": r.explanation,
                "breakdown": r.breakdown,
            })

        return {
            "success": True,
            "results": formatted_results,
            "result": formatted_results[0],
            "command_count": len(formatted_results),
        }

    def get_method_names(self) -> List[str]:
        return self.extractor.get_method_names()

    def reset(self):
        self._pipeline = None
        self._initialized = False
