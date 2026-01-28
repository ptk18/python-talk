"""Utility functions for extracting methods from Python files"""

import ast
from typing import List
from .models import MethodInfo


def extract_methods_from_file(filepath: str) -> List[MethodInfo]:
    """Extract all public methods from the first class in a Python file"""
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())

    methods = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if item.name.startswith('_'):
                        continue

                    params = [arg.arg for arg in item.args.args if arg.arg != 'self']
                    docstring = ast.get_docstring(item)

                    methods.append(MethodInfo(
                        name=item.name,
                        params=params,
                        docstring=docstring
                    ))

            break

    return methods
