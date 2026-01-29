"""
NLP v4 Pipeline - Semantic-First Command Processing

Simple 3-step pipeline:
  1. Embed query & rank methods by cosine similarity
  2. Extract parameters from the command
  3. Return ranked MatchResult list
"""

from typing import List, Optional

from .models import MethodInfo
from .models import MatchResult
from .embedding_matcher import EmbeddingMatcher
from .param_extractor import ParamExtractor


class NLPPipeline:
    def __init__(self):
        self.matcher = EmbeddingMatcher()
        self.param_extractor = ParamExtractor()
        self._methods = {}
        self._initialized = False

    def initialize(
        self,
        methods: List[MethodInfo],
        class_name: Optional[str] = None,
    ) -> None:
        """Initialize pipeline: embed all method descriptions."""
        self.matcher.initialize(methods, class_name)
        self._methods = {m.name: m for m in methods}
        self._initialized = True

    def process_command(
        self,
        command: str,
        top_k: int = 5,
    ) -> List[MatchResult]:
        """
        Process a natural language command.

        Returns:
            List of MatchResult sorted by descending similarity.
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized. Call initialize() first.")

        matches = self.matcher.match(command, top_k=top_k)

        results = []
        for method_name, similarity, description in matches:
            method_info = self._methods[method_name]
            params = self.param_extractor.extract(command, method_info)

            results.append(MatchResult(
                method_name=method_name,
                similarity=similarity,
                extracted_params=params,
                method_description=description,
            ))

        return results
