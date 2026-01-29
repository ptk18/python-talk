"""Turtle-specific extractor using TurtleIntrospector"""

from typing import List, Any, Dict, Optional
from .base import BaseExtractor
from ..models import MethodInfo
from ..turtle_introspector import get_introspector, TurtleIntrospector


class TurtleExtractor(BaseExtractor):
    """
    Extract methods from turtle module using TurtleIntrospector.

    Wraps TurtleIntrospector to provide the BaseExtractor interface.
    """

    def __init__(self, canonical_only: bool = True):
        super().__init__()
        self.canonical_only = canonical_only
        self._introspector: Optional[TurtleIntrospector] = None

    @property
    def introspector(self) -> TurtleIntrospector:
        if self._introspector is None:
            self._introspector = get_introspector()
        return self._introspector

    def extract(self, source: Any = None) -> List[MethodInfo]:
        if self.canonical_only:
            self._methods = self.introspector.get_canonical_methods_only()
        else:
            self._methods = self.introspector.introspect()
        return self._methods

    def get_canonical_name(self, name: str) -> str:
        return self.introspector.get_canonical_name(name)

    def get_aliases(self, canonical_name: str) -> List[str]:
        return self.introspector.get_aliases(canonical_name)

    def get_method_category(self, method_name: str) -> str:
        return self.introspector._get_method_category(method_name)

    def get_methods_by_category(self) -> Dict[str, List[MethodInfo]]:
        return self.introspector.get_methods_by_category()

    def get_detailed_method(self, name: str):
        return self.introspector.get_detailed_method(name)

    def get_excluded_methods(self) -> Dict[str, Dict]:
        return self.introspector.get_excluded_methods()

    def get_exclusion_stats(self) -> Dict:
        return self.introspector.get_exclusion_stats()

    def refresh(self) -> List[MethodInfo]:
        self.introspector.clear_cache()
        return self.extract()
