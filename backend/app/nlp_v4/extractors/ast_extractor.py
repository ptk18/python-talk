"""AST-based extractor for user-uploaded Python files"""

import ast
import os
from typing import List, Union
from .base import BaseExtractor
from ..models import MethodInfo


class ASTExtractor(BaseExtractor):
    """
    Extract methods from Python source using AST parsing.

    Used for Codespace app where users upload their own Python files.
    Extracts public methods from the first class found in the source.
    """

    def __init__(self, include_private: bool = False):
        super().__init__()
        self.include_private = include_private
        self._class_name: str | None = None

    @property
    def class_name(self) -> str | None:
        return self._class_name

    def extract(self, source: Union[str, bytes]) -> List[MethodInfo]:
        """
        Extract methods from Python source.

        Args:
            source: File path (.py), Python source code string, or bytes.
        """
        if isinstance(source, str) and os.path.isfile(source):
            with open(source, "r") as f:
                code = f.read()
        elif isinstance(source, bytes):
            code = source.decode("utf-8")
        else:
            code = source

        tree = ast.parse(code)

        self._methods = []
        self._class_name = None

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._class_name = node.name
                self._extract_methods_from_class(node)
                break

        return self._methods

    def _extract_methods_from_class(self, class_node: ast.ClassDef) -> None:
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name.startswith("_") and not self.include_private:
                    continue

                params = []
                param_types = {}
                for arg in item.args.args:
                    if arg.arg == "self":
                        continue
                    params.append(arg.arg)
                    if arg.annotation:
                        param_types[arg.arg] = ast.unparse(arg.annotation)
                    else:
                        param_types[arg.arg] = "Any"

                docstring = ast.get_docstring(item)

                self._methods.append(
                    MethodInfo(
                        name=item.name,
                        params=params,
                        docstring=docstring,
                        param_types=param_types,
                    )
                )

    def extract_all_functions(self, source: Union[str, bytes]) -> List[MethodInfo]:
        """Extract ALL top-level functions (not just class methods)."""
        if isinstance(source, str) and os.path.isfile(source):
            with open(source, "r") as f:
                code = f.read()
        elif isinstance(source, bytes):
            code = source.decode("utf-8")
        else:
            code = source

        tree = ast.parse(code)

        functions = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("_") and not self.include_private:
                    continue
                params = []
                param_types = {}
                for arg in node.args.args:
                    if arg.arg == "self":
                        continue
                    params.append(arg.arg)
                    if arg.annotation:
                        param_types[arg.arg] = ast.unparse(arg.annotation)
                    else:
                        param_types[arg.arg] = "Any"
                docstring = ast.get_docstring(node)
                functions.append(
                    MethodInfo(
                        name=node.name,
                        params=params,
                        docstring=docstring,
                        param_types=param_types,
                    )
                )

        return functions
