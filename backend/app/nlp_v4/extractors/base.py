"""Base extractor interface for method extraction strategies"""

from abc import ABC, abstractmethod
from typing import List, Any
from ..models import MethodInfo


class BaseExtractor(ABC):
    """Abstract base for method extraction strategies."""

    def __init__(self):
        self._methods: List[MethodInfo] = []

    @property
    def methods(self) -> List[MethodInfo]:
        return self._methods

    @abstractmethod
    def extract(self, source: Any) -> List[MethodInfo]:
        pass

    def get_method_names(self) -> List[str]:
        return [m.name for m in self._methods]

    def get_method_by_name(self, name: str) -> MethodInfo | None:
        name_lower = name.lower()
        for method in self._methods:
            if method.name.lower() == name_lower:
                return method
        return None
