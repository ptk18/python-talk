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

    name_expanded = method.name.replace("_", " ")
    parts.append(name_expanded)

    if method.docstring:
        doc = method.docstring.strip().split("\n")[0]  
        parts.append(doc)

    return ". ".join(parts)


def describe_methods(
    methods: List[MethodInfo], class_name: Optional[str] = None
) -> List[str]:
    """Build descriptions for a list of methods."""
    return [describe_method(m, class_name) for m in methods]
