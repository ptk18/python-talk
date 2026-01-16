"""Base extractor interface for method extraction strategies"""

from abc import ABC, abstractmethod
from typing import List, Any
from ..models import MethodInfo


class BaseExtractor(ABC):
    """
    Abstract base for method extraction strategies.

    Each extractor knows how to extract MethodInfo objects from a specific
    source type (Python file, module, class, etc.).
    """

    def __init__(self):
        self._methods: List[MethodInfo] = []

    @property
    def methods(self) -> List[MethodInfo]:
        """Get the extracted methods"""
        return self._methods

    @abstractmethod
    def extract(self, source: Any) -> List[MethodInfo]:
        """
        Extract methods from source.

        Args:
            source: The source to extract methods from.
                   Could be file path, source code string, module, class, etc.
                   Specific type depends on the extractor implementation.

        Returns:
            List of MethodInfo objects representing the extracted methods.
        """
        pass

    def get_method_names(self) -> List[str]:
        """Get just the method names (convenience method)"""
        return [m.name for m in self._methods]

    def get_method_by_name(self, name: str) -> MethodInfo | None:
        """Find a method by name (case-insensitive)"""
        name_lower = name.lower()
        for method in self._methods:
            if method.name.lower() == name_lower:
                return method
        return None
