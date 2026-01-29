"""
Method Description Builder

Transforms MethodInfo into rich natural language descriptions
for embedding with SentenceTransformer.

Examples:
  MethodInfo("turn_light_on", [], "Turn on the light")
  -> "turn light on. Turn on the light"

  MethodInfo("add", ["a", "b"], "Add two numbers together")
  -> "add a and b. Add two numbers together"

  MethodInfo("set_temperature", ["temp"], None)
  -> "set temperature with temp"
"""

from typing import List, Optional

from .models import MethodInfo


def describe_method(method: MethodInfo, class_name: Optional[str] = None) -> str:
    """Build a natural language description from a MethodInfo."""
    parts = []

    # 1. Expand method name: snake_case -> spaces
    name_expanded = method.name.replace("_", " ")

    # 2. Append parameters naturally
    params = [p for p in method.params if p != "self"]
    if params:
        if len(params) == 1:
            name_expanded += f" with {params[0]}"
        elif len(params) == 2:
            name_expanded += f" {params[0]} and {params[1]}"
        else:
            name_expanded += " " + ", ".join(params[:-1]) + f", and {params[-1]}"

    parts.append(name_expanded)

    # 3. Append docstring if available
    if method.docstring:
        doc = method.docstring.strip().split("\n")[0]  # First line only
        parts.append(doc)

    return ". ".join(parts)


def describe_methods(
    methods: List[MethodInfo], class_name: Optional[str] = None
) -> List[str]:
    """Build descriptions for a list of methods."""
    return [describe_method(m, class_name) for m in methods]
