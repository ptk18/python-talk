"""Module introspection-based extractor for built-in Python modules"""

import inspect
import re
from typing import List, Any, Set, Dict, Optional, Callable
from dataclasses import dataclass
from .base import BaseExtractor
from ..models import MethodInfo


@dataclass
class ExclusionRule:
    """Rule for excluding methods from extraction"""
    name_patterns: List[str] = None
    exact_names: Set[str] = None
    param_contains: List[str] = None
    doc_patterns: List[str] = None

    def __post_init__(self):
        self.name_patterns = self.name_patterns or []
        self.exact_names = self.exact_names or set()
        self.param_contains = self.param_contains or []
        self.doc_patterns = self.doc_patterns or []


class ModuleExtractor(BaseExtractor):
    """
    Extract methods from Python modules/classes via introspection.

    Supports configurable exclusion rules to filter out methods not suitable
    for NLP command processing.
    """

    def __init__(
        self,
        exclusion_rules: List[ExclusionRule] = None,
        force_include: Set[str] = None,
        force_exclude: Set[str] = None,
        include_private: bool = False,
        alias_parser: Callable[[str], List[str]] = None,
    ):
        super().__init__()
        self.exclusion_rules = exclusion_rules or []
        self.force_include = force_include or set()
        self.force_exclude = force_exclude or set()
        self.include_private = include_private
        self.alias_parser = alias_parser or self._default_alias_parser

        self._alias_map: Dict[str, str] = {}
        self._method_details: Dict[str, Dict] = {}

    def extract(self, source: Any) -> List[MethodInfo]:
        self._methods = []
        self._alias_map = {}
        self._method_details = {}

        for name, member in inspect.getmembers(source):
            if name.startswith("_") and not self.include_private:
                continue
            if not callable(member):
                continue

            params = self._get_param_names(member)
            docstring = inspect.getdoc(member) or ""
            description = self._get_description(docstring)
            aliases = self.alias_parser(docstring)

            should_exclude, reason = self._should_exclude(name, params, docstring)
            if should_exclude:
                continue

            self._method_details[name] = {
                "params": params,
                "docstring": docstring,
                "description": description,
                "aliases": aliases,
            }

            if aliases:
                canonical = aliases[0]
                for alias in aliases[1:]:
                    self._alias_map[alias] = canonical

            docstring_for_nlp = description
            if aliases:
                alias_str = ", ".join(aliases)
                docstring_for_nlp += f" (aliases: {alias_str})"

            self._methods.append(
                MethodInfo(name=name, params=params, docstring=docstring_for_nlp)
            )

        self._methods.sort(key=lambda x: x.name)
        return self._methods

    def get_canonical_methods_only(self) -> List[MethodInfo]:
        if not self._methods:
            return []

        canonical_methods = []
        seen = set()

        for method in self._methods:
            if method.name in self._alias_map:
                continue

            detail = self._method_details.get(method.name, {})
            aliases = detail.get("aliases", [])
            if aliases:
                canonical = aliases[0]
                if canonical in seen:
                    continue
                seen.add(canonical)
            else:
                if method.name in seen:
                    continue
                seen.add(method.name)

            canonical_methods.append(method)

        return canonical_methods

    def get_canonical_name(self, name: str) -> str:
        return self._alias_map.get(name, name)

    def _get_param_names(self, func) -> List[str]:
        try:
            sig = inspect.signature(func)
            return [
                name
                for name, param in sig.parameters.items()
                if name != "self"
                and param.kind
                not in (
                    inspect.Parameter.VAR_POSITIONAL,
                    inspect.Parameter.VAR_KEYWORD,
                )
            ]
        except (ValueError, TypeError):
            return []

    def _get_description(self, docstring: str) -> str:
        if not docstring:
            return ""
        return docstring.strip().split("\n")[0].strip()

    def _default_alias_parser(self, docstring: str) -> List[str]:
        if not docstring:
            return []
        for line in docstring.split("\n"):
            line = line.strip()
            if line.startswith("Aliases:") or line.startswith("Alias:"):
                alias_part = line.split(":", 1)[1].strip()
                return [a.strip() for a in alias_part.split("|") if a.strip()]
        return []

    def _should_exclude(
        self, name: str, params: List[str], docstring: str
    ) -> tuple[bool, Optional[str]]:
        if name in self.force_include:
            return False, None
        if name in self.force_exclude:
            return True, "force_exclude"

        doc_lower = docstring.lower() if docstring else ""

        for rule in self.exclusion_rules:
            if rule.exact_names and name in rule.exact_names:
                return True, f"exact_name: {name}"
            for pattern in rule.name_patterns:
                if re.match(pattern, name):
                    return True, f"name_pattern: {pattern}"
            for param_pattern in rule.param_contains:
                for param in params:
                    if param_pattern.lower() in param.lower():
                        return True, f"param_contains: {param_pattern}"
            for doc_pattern in rule.doc_patterns:
                if re.search(doc_pattern, doc_lower):
                    return True, f"doc_pattern: {doc_pattern}"

        return False, None


def create_turtle_extractor() -> ModuleExtractor:
    """Create a ModuleExtractor pre-configured for turtle module."""
    import turtle

    exclusion_rules = [
        ExclusionRule(
            name_patterns=[r"^on"],
            param_contains=["fun"],
            doc_patterns=["bind.*to", "event"],
        ),
        ExclusionRule(
            exact_names={"textinput", "numinput"},
            doc_patterns=["dialog", "popup"],
        ),
        ExclusionRule(
            exact_names={
                "setup", "title", "bgpic", "screensize", "setworldcoordinates",
                "window_width", "window_height", "getcanvas", "getshapes",
                "register_shape", "addshape", "clearscreen", "resetscreen",
                "turtles", "mode", "colormode",
            },
            doc_patterns=["set up.*screen", "return.*screen", "screen size"],
        ),
        ExclusionRule(
            exact_names={"getpen", "getscreen", "getturtle"},
            name_patterns=[r"^get(?!heading)"],
            doc_patterns=["return.*screen object", "return.*turtle object"],
        ),
        ExclusionRule(
            exact_names={"done", "bye", "exitonclick", "mainloop", "listen"},
            doc_patterns=["terminate", "shut.*event loop", "exit"],
        ),
        ExclusionRule(
            exact_names={"tracer", "update", "delay"},
            doc_patterns=["turn.*animation", "screen update"],
        ),
        ExclusionRule(
            exact_names={
                "begin_poly", "end_poly", "get_poly", "get_shapepoly",
                "clone", "shape", "resizemode", "shapesize", "turtlesize",
                "shearfactor", "settiltangle", "tiltangle", "tilt", "shapetransform",
                "setundobuffer", "undobufferentries",
            },
            doc_patterns=["polygon", "clone.*turtle", "shear"],
        ),
    ]

    extractor = ModuleExtractor(exclusion_rules=exclusion_rules)
    extractor.extract(turtle.Turtle)
    return extractor
