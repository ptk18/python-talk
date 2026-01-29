"""Turtle method introspection for NLP v4 pipeline"""

import inspect
import re
import turtle
from enum import Enum
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass

from .models import MethodInfo


class ExclusionReason(Enum):
    EVENT_HANDLER = "event_handler"
    UI_DIALOG = "ui_dialog"
    SCREEN_LEVEL = "screen_level"
    GETTER = "getter"
    LIFECYCLE = "lifecycle"
    ANIMATION = "animation"
    ADVANCED = "advanced"


EXCLUSION_RULES = {
    ExclusionReason.EVENT_HANDLER: {
        "name_patterns": [r"^on"],
        "param_contains": ["fun"],
        "doc_patterns": ["bind.*to", "event"],
    },
    ExclusionReason.UI_DIALOG: {
        "names": {"textinput", "numinput"},
        "doc_patterns": ["dialog", "popup"],
    },
    ExclusionReason.SCREEN_LEVEL: {
        "names": {
            "setup", "title", "bgpic", "screensize", "setworldcoordinates",
            "window_width", "window_height", "getcanvas", "getshapes",
            "register_shape", "addshape", "clearscreen", "resetscreen",
            "turtles", "mode", "colormode",
        },
        "doc_patterns": ["set up.*screen", "return.*screen", "screen size"],
    },
    ExclusionReason.GETTER: {
        "names": {"getpen", "getscreen", "getturtle"},
        "name_patterns": [r"^get(?!heading)"],
        "doc_patterns": ["return.*screen object", "return.*turtle object"],
    },
    ExclusionReason.LIFECYCLE: {
        "names": {"done", "bye", "exitonclick", "mainloop", "listen"},
        "doc_patterns": ["terminate", "shut.*event loop", "exit"],
    },
    ExclusionReason.ANIMATION: {
        "names": {"tracer", "update", "delay"},
        "doc_patterns": ["turn.*animation", "screen update"],
    },
    ExclusionReason.ADVANCED: {
        "names": {
            "begin_poly", "end_poly", "get_poly", "get_shapepoly",
            "clone", "shape", "resizemode", "shapesize", "turtlesize",
            "shearfactor", "settiltangle", "tiltangle", "tilt", "shapetransform",
            "setundobuffer", "undobufferentries",
        },
        "doc_patterns": ["polygon", "clone.*turtle", "shear"],
    },
}

FORCE_EXCLUDE: Set[str] = set()
FORCE_INCLUDE: Set[str] = set()


@dataclass
class TurtleMethodDetail:
    name: str
    params: List[str]
    docstring: str
    aliases: List[str]
    category: str
    description: str


@dataclass
class ExcludedMethod:
    name: str
    reason: ExclusionReason
    matched_rule: str


class TurtleIntrospector:
    CATEGORY_PATTERNS = {
        "movement": ["forward", "backward", "move", "fd", "bk", "back"],
        "turning": ["turn", "left", "right", "lt", "rt", "heading", "setheading", "seth"],
        "position": ["goto", "setpos", "setposition", "setx", "sety", "home", "teleport", "position", "pos", "xcor", "ycor"],
        "pen_control": ["pen", "penup", "pendown", "pu", "pd", "up", "down", "width", "pensize"],
        "color": ["color", "pencolor", "fillcolor", "bgcolor"],
        "fill": ["fill", "begin_fill", "end_fill", "filling"],
        "drawing": ["circle", "dot", "stamp", "write", "clearstamp"],
        "visibility": ["show", "hide", "showturtle", "hideturtle", "st", "ht", "isvisible"],
        "state": ["distance", "towards", "isdown"],
        "control": ["speed", "clear", "reset", "undo", "degrees", "radians"],
    }

    def __init__(self):
        self._methods: Optional[List[MethodInfo]] = None
        self._detailed_methods: Optional[Dict[str, TurtleMethodDetail]] = None
        self._alias_map: Dict[str, str] = {}
        self._excluded_methods: Dict[str, ExcludedMethod] = {}

    def _get_param_names(self, func) -> List[str]:
        try:
            sig = inspect.signature(func)
            return [
                name for name, param in sig.parameters.items()
                if name != "self" and param.kind not in (
                    inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD
                )
            ]
        except (ValueError, TypeError):
            return []

    def _parse_docstring(self, docstring: str) -> Tuple[str, List[str]]:
        if not docstring:
            return ("", [])
        lines = docstring.strip().split("\n")
        description = lines[0].strip() if lines else ""
        aliases = []
        for line in lines:
            if line.strip().startswith("Aliases:") or line.strip().startswith("Alias:"):
                alias_part = line.split(":", 1)[1].strip()
                aliases = [a.strip() for a in alias_part.split("|")]
                break
        return (description, aliases)

    def _determine_category(self, method_name: str, docstring: str = "") -> str:
        name_lower = method_name.lower()
        doc_lower = docstring.lower() if docstring else ""
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_lower or pattern in doc_lower:
                    return category
        return "other"

    def _should_exclude(
        self, name: str, params: List[str], docstring: str
    ) -> Tuple[bool, Optional[ExclusionReason], str]:
        if name in FORCE_INCLUDE:
            return False, None, ""
        if name in FORCE_EXCLUDE:
            return True, ExclusionReason.ADVANCED, "force_exclude"

        doc_lower = docstring.lower() if docstring else ""

        for reason, rules in EXCLUSION_RULES.items():
            if "names" in rules and name in rules["names"]:
                return True, reason, f"name in {rules['names']}"
            if "name_patterns" in rules:
                for pattern in rules["name_patterns"]:
                    if re.match(pattern, name):
                        return True, reason, f"name matches {pattern}"
            if "param_contains" in rules:
                for param_pattern in rules["param_contains"]:
                    for param in params:
                        if param_pattern in param.lower():
                            return True, reason, f"param '{param}' contains '{param_pattern}'"
            if "doc_patterns" in rules:
                for doc_pattern in rules["doc_patterns"]:
                    if re.search(doc_pattern, doc_lower):
                        return True, reason, f"docstring matches '{doc_pattern}'"

        return False, None, ""

    def introspect(self, force_refresh: bool = False) -> List[MethodInfo]:
        if self._methods is not None and not force_refresh:
            return self._methods

        turtle_class = turtle.Turtle
        self._detailed_methods = {}
        self._alias_map = {}
        self._excluded_methods = {}

        for name, member in inspect.getmembers(turtle_class):
            if name.startswith("_") or not callable(member):
                continue

            params = self._get_param_names(member)
            full_docstring = inspect.getdoc(member) or ""

            should_exclude, reason, matched_rule = self._should_exclude(
                name, params, full_docstring
            )
            if should_exclude:
                self._excluded_methods[name] = ExcludedMethod(
                    name=name, reason=reason, matched_rule=matched_rule
                )
                continue

            description, aliases = self._parse_docstring(full_docstring)
            category = self._determine_category(name, full_docstring)

            self._detailed_methods[name] = TurtleMethodDetail(
                name=name, params=params, docstring=full_docstring,
                aliases=aliases, category=category, description=description
            )

            if aliases:
                canonical = aliases[0]
                for alias in aliases:
                    if alias != canonical:
                        self._alias_map[alias] = canonical

        self._methods = []
        for name, detail in self._detailed_methods.items():
            docstring_for_nlp = detail.description
            if detail.aliases:
                docstring_for_nlp += f" aliases {' '.join(detail.aliases)}"

            self._methods.append(MethodInfo(
                name=name, params=detail.params, docstring=docstring_for_nlp
            ))

        self._methods.sort(key=lambda x: x.name)
        return self._methods

    def get_canonical_methods_only(self) -> List[MethodInfo]:
        self.introspect()
        canonical_methods = []
        seen_canonicals = set()

        for method in self._methods:
            name = method.name
            if name in self._alias_map:
                continue

            detail = self._detailed_methods.get(name)
            if detail and detail.aliases:
                canonical = detail.aliases[0]
                if canonical in seen_canonicals:
                    continue
                seen_canonicals.add(canonical)

                alias_list = [a for a in detail.aliases if a != canonical]
                docstring_with_aliases = detail.description
                if alias_list:
                    docstring_with_aliases += f" (aliases: {', '.join(alias_list)})"

                canonical_methods.append(MethodInfo(
                    name=canonical, params=detail.params, docstring=docstring_with_aliases
                ))
            else:
                if name not in seen_canonicals:
                    seen_canonicals.add(name)
                    canonical_methods.append(method)

        canonical_methods.sort(key=lambda x: x.name)
        return canonical_methods

    def get_methods_by_category(self) -> Dict[str, List[MethodInfo]]:
        self.introspect()
        categorized: Dict[str, List[MethodInfo]] = {}
        for method in self._methods:
            detail = self._detailed_methods.get(method.name)
            category = detail.category if detail else "other"
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(method)
        return categorized

    def get_detailed_method(self, name: str) -> Optional[TurtleMethodDetail]:
        self.introspect()
        return self._detailed_methods.get(name)

    def get_canonical_name(self, name: str) -> str:
        self.introspect()
        return self._alias_map.get(name, name)

    def get_aliases(self, canonical_name: str) -> List[str]:
        self.introspect()
        detail = self._detailed_methods.get(canonical_name)
        return detail.aliases if detail else []

    def _get_method_category(self, method_name: str) -> str:
        self.introspect()
        detail = self._detailed_methods.get(method_name)
        return detail.category if detail else "other"

    def get_excluded_methods(self) -> Dict[str, Dict]:
        self.introspect()
        return {
            name: {
                "reason": excluded.reason.value,
                "matched_rule": excluded.matched_rule,
            }
            for name, excluded in self._excluded_methods.items()
        }

    def get_exclusion_stats(self) -> Dict:
        self.introspect()
        stats = {reason.value: [] for reason in ExclusionReason}
        for name, excluded in self._excluded_methods.items():
            stats[excluded.reason.value].append(name)
        return {
            "total_excluded": len(self._excluded_methods),
            "total_included": len(self._methods),
            "by_reason": {
                reason: {"count": len(methods), "methods": sorted(methods)}
                for reason, methods in stats.items()
                if methods
            },
        }

    def clear_cache(self):
        self._methods = None
        self._detailed_methods = None
        self._alias_map = {}
        self._excluded_methods = {}


_introspector: Optional[TurtleIntrospector] = None


def get_introspector() -> TurtleIntrospector:
    global _introspector
    if _introspector is None:
        _introspector = TurtleIntrospector()
    return _introspector


def get_turtle_methods() -> List[MethodInfo]:
    return get_introspector().introspect()


def get_turtle_method_names() -> List[str]:
    return [m.name for m in get_turtle_methods()]


def refresh_turtle_methods() -> List[MethodInfo]:
    return get_introspector().introspect(force_refresh=True)


def get_excluded_turtle_methods() -> Dict[str, Dict]:
    return get_introspector().get_excluded_methods()


def get_exclusion_stats() -> Dict:
    return get_introspector().get_exclusion_stats()
