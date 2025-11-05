from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field


@dataclass
class MethodInfo:
    name: str
    class_name: str
    params: Dict[str, type]
    required_params: List[str]
    docstring: Optional[str]
    is_query: bool
    surface_forms: Set[str] = field(default_factory=set)


class DomainCatalog:
    def __init__(self):
        self.classes: Dict[str, type] = {}
        self.methods: Dict[str, List[MethodInfo]] = {}
        self.properties: Dict[str, List[str]] = {}
        self.object_analysis: Dict[str, Any] = {}

    def add_class(self, class_name: str, class_obj: type):
        self.classes[class_name] = class_obj
        self.methods[class_name] = []
        self.properties[class_name] = []

    def add_method(self, class_name: str, method_info: MethodInfo):
        if class_name not in self.methods:
            self.methods[class_name] = []
        self.methods[class_name].append(method_info)

    def get_methods(self, class_name: str) -> List[MethodInfo]:
        return self.methods.get(class_name, [])

    def find_method(self, class_name: str, method_name: str) -> Optional[MethodInfo]:
        for method in self.get_methods(class_name):
            if method.name == method_name:
                return method
        return None

    def get_object_name_for_class(self, class_name: str) -> str:
        if hasattr(self, 'object_analysis') and self.object_analysis.get("has_main_function"):
            for obj in self.object_analysis.get("main_function_objects", []):
                if obj["class_name"] == class_name:
                    return obj["variable_name"]
        
        return class_name.lower()
