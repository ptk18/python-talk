"""Turtle-specific extractor using existing TurtleIntrospector"""

from typing import List, Any, Dict, Optional
from .base import BaseExtractor
from ..models import MethodInfo
from ..turtle_introspector import get_introspector, TurtleIntrospector


class TurtleExtractor(BaseExtractor):
    """
    Extract methods from turtle module using TurtleIntrospector.

    This extractor wraps the existing TurtleIntrospector to provide
    backward compatibility while conforming to the BaseExtractor interface.
    It preserves all turtle-specific features like:
    - Exclusion rules for unsuitable methods
    - Category classification
    - Alias handling (fd -> forward, etc.)
    """

    def __init__(self, canonical_only: bool = True):
        """
        Args:
            canonical_only: If True, only return canonical methods (not aliases)
        """
        super().__init__()
        self.canonical_only = canonical_only
        self._introspector: Optional[TurtleIntrospector] = None

    @property
    def introspector(self) -> TurtleIntrospector:
        """Get the underlying introspector"""
        if self._introspector is None:
            self._introspector = get_introspector()
        return self._introspector

    def extract(self, source: Any = None) -> List[MethodInfo]:
        """
        Extract methods from turtle module.

        Args:
            source: Ignored for turtle (uses turtle.Turtle automatically)

        Returns:
            List of MethodInfo objects for turtle methods
        """
        if self.canonical_only:
            self._methods = self.introspector.get_canonical_methods_only()
        else:
            self._methods = self.introspector.introspect()
        return self._methods

    def get_canonical_name(self, name: str) -> str:
        """Get the canonical name for an alias"""
        return self.introspector.get_canonical_name(name)

    def get_aliases(self, canonical_name: str) -> List[str]:
        """Get aliases for a canonical method name"""
        return self.introspector.get_aliases(canonical_name)

    def get_method_category(self, method_name: str) -> str:
        """Get the category of a method"""
        return self.introspector._get_method_category(method_name)

    def get_methods_by_category(self) -> Dict[str, List[MethodInfo]]:
        """Get methods grouped by category"""
        return self.introspector.get_methods_by_category()

    def get_detailed_method(self, name: str):
        """Get detailed info for a method"""
        return self.introspector.get_detailed_method(name)

    def get_excluded_methods(self) -> Dict[str, Dict]:
        """Get all excluded methods with reasons"""
        return self.introspector.get_excluded_methods()

    def get_exclusion_stats(self) -> Dict:
        """Get statistics about excluded methods"""
        return self.introspector.get_exclusion_stats()

    def refresh(self) -> List[MethodInfo]:
        """Force refresh the method list"""
        self.introspector.clear_cache()
        return self.extract()
