"""
Generic NLP Service - Unified interface for command processing

This service provides a single, generic interface for processing natural language
commands against any set of methods. It works with pluggable extractors and
preprocessors to support different use cases (Codespace, Turtle, future apps).
"""

from typing import List, Any, Optional
from dataclasses import dataclass

from .extractors.base import BaseExtractor
from .preprocessors.base import BasePreprocessor
from .preprocessors.default import DefaultPreprocessor
from .main import NLPPipeline
from .models import MethodInfo, MatchScore


@dataclass
class ProcessResult:
    """Result of processing a command"""
    success: bool
    method_name: str
    parameters: dict
    confidence: float
    executable: str
    action_verb: str
    explanation: str
    breakdown: dict

    @classmethod
    def from_match_score(cls, action_verb: str, match: MatchScore) -> 'ProcessResult':
        """Create ProcessResult from MatchScore"""
        return cls(
            success=True,
            method_name=match.method_name,
            parameters=match.extracted_params,
            confidence=match.total_score * 100,  # Convert to percentage
            executable=match.get_method_call(),
            action_verb=action_verb,
            explanation=match.explain(),
            breakdown={
                'direct_match': match.phrasal_verb_match * 100,
                'synonym_match': match.synonym_boost * 100,
                'entity_match': match.intent_score * 100,
                'semantic_score': match.semantic_score * 100,
                'param_bonus': match.param_relevance * 100,
            }
        )


class NLPService:
    """
    Generic NLP service that works with ANY method source.

    Apps configure it with their specific:
    - Extractor: How to get methods (AST, module introspection, etc.)
    - Preprocessor: How to transform commands before processing

    Example:
        # For Codespace (user-uploaded Python files)
        service = NLPService(
            extractor=ASTExtractor(),
            preprocessor=DefaultPreprocessor()
        )
        service.initialize(user_code)
        results = service.process("add 2 and 3")

        # For Turtle Playground
        service = NLPService(
            extractor=ModuleExtractor(...),
            preprocessor=TurtlePreprocessor()
        )
        service.initialize(turtle.Turtle)
        results = service.process("move forward 50")
    """

    # Default confidence threshold (15%)
    DEFAULT_CONFIDENCE_THRESHOLD = 0.15

    def __init__(
        self,
        extractor: BaseExtractor,
        preprocessor: BasePreprocessor = None,
        confidence_threshold: float = None,
    ):
        """
        Initialize the NLP service.

        Args:
            extractor: Strategy for extracting methods from source
            preprocessor: Strategy for preprocessing commands (optional)
            confidence_threshold: Minimum confidence to return a match (0-1)
        """
        self.extractor = extractor
        self.preprocessor = preprocessor or DefaultPreprocessor()
        self.confidence_threshold = confidence_threshold or self.DEFAULT_CONFIDENCE_THRESHOLD

        self._pipeline: Optional[NLPPipeline] = None
        self._initialized = False

    @property
    def initialized(self) -> bool:
        """Check if the service has been initialized with methods"""
        return self._initialized

    @property
    def methods(self) -> List[MethodInfo]:
        """Get the extracted methods"""
        return self.extractor.methods

    def initialize(self, source: Any) -> List[MethodInfo]:
        """
        Initialize the service with a method source.

        Args:
            source: The source to extract methods from
                   (file path, code string, module, class, etc.)

        Returns:
            List of extracted MethodInfo objects
        """
        # Extract methods using the configured extractor
        methods = self.extractor.extract(source)

        # Initialize the NLP pipeline with extracted methods
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
        """
        Process a natural language command.

        Args:
            command: The raw command from user
            language: Language code ('en', 'th')
            top_k: Maximum number of results to return (None for all)

        Returns:
            List of ProcessResult objects, sorted by confidence

        Raises:
            RuntimeError: If service not initialized
        """
        if not self._initialized:
            raise RuntimeError(
                "NLPService not initialized. Call initialize() first."
            )

        # Preprocess command using configured preprocessor
        processed_command = self.preprocessor.preprocess(command)

        # Process through NLP pipeline
        raw_results = self._pipeline.process_command(
            processed_command,
            self.extractor.methods,
            top_k=top_k,
            language=language
        )

        # Convert to ProcessResult and filter by confidence
        results = []
        for action_verb, match_score in raw_results:
            if match_score.total_score >= self.confidence_threshold:
                results.append(ProcessResult.from_match_score(action_verb, match_score))

        return results

    def process_and_format(
        self,
        command: str,
        language: str = "en",
    ) -> dict:
        """
        Process command and return formatted response dict.

        This is a convenience method that formats the response
        in a standard way suitable for API responses.

        Args:
            command: The raw command
            language: Language code

        Returns:
            Dict with 'success', 'results', and 'result' keys
        """
        results = self.process(command, language)

        if not results:
            return {
                'success': False,
                'results': [],
                'result': {
                    'success': False,
                    'message': f'No confident matches found (threshold: {self.confidence_threshold*100:.0f}%)',
                    'confidence': 0.0,
                },
                'command_count': 0,
            }

        formatted_results = []
        for r in results:
            formatted_results.append({
                'success': r.success,
                'method': r.method_name,
                'parameters': r.parameters,
                'confidence': r.confidence,
                'executable': r.executable,
                'action_verb': r.action_verb,
                'explanation': r.explanation,
                'breakdown': r.breakdown,
            })

        return {
            'success': True,
            'results': formatted_results,
            'result': formatted_results[0],  # Top result for backward compatibility
            'command_count': len(formatted_results),
        }

    def get_method_names(self) -> List[str]:
        """Get list of available method names"""
        return self.extractor.get_method_names()

    def reset(self):
        """Reset the service (clear pipeline, keep extractor config)"""
        self._pipeline = None
        self._initialized = False
