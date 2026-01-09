import inspect
import turtle
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass

from .models import MethodInfo


@dataclass
class TurtleMethodDetail:
    name: str
    params: List[str]
    docstring: str
    aliases: List[str]
    category: str
    description: str


class TurtleIntrospector:
    EXCLUDED_METHODS: Set[str] = {
        'setup', 'done', 'bye', 'exitonclick', 'mainloop', 'textinput', 'numinput',
        'listen', 'onkey', 'onkeypress', 'onkeyrelease', 'onclick', 'onrelease',
        'ondrag', 'onscreenclick', 'ontimer', 'mode', 'colormode', 'delay',
        'tracer', 'update', 'window_width', 'window_height', 'getcanvas',
        'getshapes', 'register_shape', 'addshape', 'screensize', 'setworldcoordinates',
        'title', 'turtles', 'bgpic', 'clearscreen', 'resetscreen',
        'getpen', 'getscreen', 'getturtle', 'setundobuffer', 'undobufferentries',
        'begin_poly', 'end_poly', 'get_poly', 'clone', 'shape', 'resizemode',
        'shapesize', 'turtlesize', 'shearfactor', 'settiltangle', 'tiltangle', 'tilt',
        'shapetransform', 'get_shapepoly',
    }

    CATEGORY_PATTERNS = {
        'movement': ['forward', 'backward', 'move', 'fd', 'bk', 'back'],
        'turning': ['turn', 'left', 'right', 'lt', 'rt', 'heading', 'setheading', 'seth'],
        'position': ['goto', 'setpos', 'setposition', 'setx', 'sety', 'home', 'teleport', 'position', 'pos', 'xcor', 'ycor'],
        'pen_control': ['pen', 'penup', 'pendown', 'pu', 'pd', 'up', 'down', 'width', 'pensize'],
        'color': ['color', 'pencolor', 'fillcolor', 'bgcolor'],
        'fill': ['fill', 'begin_fill', 'end_fill', 'filling'],
        'drawing': ['circle', 'dot', 'stamp', 'write', 'clearstamp'],
        'visibility': ['show', 'hide', 'showturtle', 'hideturtle', 'st', 'ht', 'isvisible'],
        'state': ['distance', 'towards', 'isdown'],
        'control': ['speed', 'clear', 'reset', 'undo', 'degrees', 'radians'],
    }

    def __init__(self):
        self._methods: Optional[List[MethodInfo]] = None
        self._detailed_methods: Optional[Dict[str, TurtleMethodDetail]] = None
        self._alias_map: Dict[str, str] = {}

    def _get_param_names(self, func) -> List[str]:
        try:
            sig = inspect.signature(func)
            return [
                name for name, param in sig.parameters.items()
                if name != 'self' and param.kind not in (
                    inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD
                )
            ]
        except (ValueError, TypeError):
            return []

    def _parse_docstring(self, docstring: str) -> Tuple[str, List[str]]:
        if not docstring:
            return ("", [])

        lines = docstring.strip().split('\n')
        description = lines[0].strip() if lines else ""

        aliases = []
        for line in lines:
            if line.strip().startswith('Aliases:') or line.strip().startswith('Alias:'):
                alias_part = line.split(':', 1)[1].strip()
                aliases = [a.strip() for a in alias_part.split('|')]
                break

        return (description, aliases)

    def _determine_category(self, method_name: str, docstring: str = "") -> str:
        name_lower = method_name.lower()
        doc_lower = docstring.lower() if docstring else ""

        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in name_lower or pattern in doc_lower:
                    return category

        return 'other'

    def introspect(self, force_refresh: bool = False) -> List[MethodInfo]:
        if self._methods is not None and not force_refresh:
            return self._methods

        turtle_class = turtle.Turtle
        self._detailed_methods = {}
        self._alias_map = {}
        self._canonical_methods: Set[str] = set()

        for name, member in inspect.getmembers(turtle_class):
            if name.startswith('_') or name in self.EXCLUDED_METHODS or not callable(member):
                continue

            params = self._get_param_names(member)
            full_docstring = inspect.getdoc(member) or ""
            description, aliases = self._parse_docstring(full_docstring)
            category = self._determine_category(name, full_docstring)

            self._detailed_methods[name] = TurtleMethodDetail(
                name=name, params=params, docstring=full_docstring,
                aliases=aliases, category=category, description=description
            )

            if aliases:
                canonical = aliases[0]
                self._canonical_methods.add(canonical)
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
        """Return only canonical methods (no aliases like fd, bk, lt, rt)."""
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
            category = detail.category if detail else 'other'
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
        return detail.category if detail else 'other'

    def clear_cache(self):
        self._methods = None
        self._detailed_methods = None
        self._alias_map = {}


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
