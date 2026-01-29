"""
Catalog utility for nlp_v4 — extracts class/method info from Python files via AST.
Standalone copy (no nlp_v3 dependency).
"""

import ast
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MethodCatalog:
    """Simple method info compatible with nlp_v2 structure"""
    name: str
    parameters: Dict[str, str]  
    required_parameters: List[str]
    return_type: Optional[str]
    docstring: Optional[str]


@dataclass
class ClassCatalog:
    """Class info compatible with nlp_v2 structure"""
    name: str
    methods: List[MethodCatalog]
    docstring: Optional[str]


@dataclass
class FileCatalog:
    """File catalog compatible with nlp_v2 structure"""
    classes: Dict[str, ClassCatalog]


def extract_from_file(filepath: str) -> FileCatalog:
    """
    Extract catalog from a Python file (compatible with nlp_v2 interface)
    Returns a FileCatalog with classes dict
    """
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())

    classes = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            class_docstring = ast.get_docstring(node)
            methods = []

            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if item.name.startswith('_') and item.name != '__init__':
                        continue

                    params = {}
                    required_params = []

                    for i, arg in enumerate(item.args.args):
                        if arg.arg == 'self':
                            continue

                        param_type = 'Any'
                        if arg.annotation:
                            param_type = ast.unparse(arg.annotation)

                        params[arg.arg] = param_type

                        defaults_start_idx = len(item.args.args) - len(item.args.defaults)
                        if i < defaults_start_idx:
                            required_params.append(arg.arg)

                    return_type = None
                    if item.returns:
                        return_type = ast.unparse(item.returns)

                    docstring = ast.get_docstring(item)

                    methods.append(MethodCatalog(
                        name=item.name,
                        parameters=params,
                        required_parameters=required_params,
                        return_type=return_type,
                        docstring=docstring
                    ))

            classes[class_name] = ClassCatalog(
                name=class_name,
                methods=methods,
                docstring=class_docstring
            )

    return FileCatalog(classes=classes)
