from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class MethodInfo:
    """Information about a single method"""
    name: str
    class_name: str
    parameters: Dict[str, type]
    required_parameters: List[str]
    return_type: Optional[type]
    docstring: Optional[str]


@dataclass
class ClassInfo:
    """Information about a class"""
    name: str
    docstring: Optional[str]
    methods: List[MethodInfo] = field(default_factory=list)


class Catalog:
    """Catalog of classes and methods extracted from source code"""

    def __init__(self):
        self.classes: Dict[str, ClassInfo] = {}
        self.methods: Dict[str, List[MethodInfo]] = {}

    def add_class(self, name: str, class_info: ClassInfo) -> None:
        """Add a class to catalog"""
        self.classes[name] = class_info
        self.methods[name] = class_info.methods

    def get_class(self, name: str) -> ClassInfo:
        """Retrieve class information"""
        return self.classes.get(name)

    def get_methods(self, class_name: str) -> List[MethodInfo]:
        """Get all methods for a class"""
        return self.methods.get(class_name, [])

    def find_method(self, class_name: str, method_name: str) -> Optional[MethodInfo]:
        """Find specific method"""
        methods = self.get_methods(class_name)
        for method in methods:
            if method.name == method_name:
                return method
        return None
