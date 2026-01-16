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
        """
        Args:
            include_private: If True, include methods starting with '_'
        """
        super().__init__()
        self.include_private = include_private
        self._class_name: str | None = None

    @property
    def class_name(self) -> str | None:
        """Get the name of the class that methods were extracted from"""
        return self._class_name

    def extract(self, source: Union[str, bytes]) -> List[MethodInfo]:
        """
        Extract methods from Python source.

        Args:
            source: Can be:
                - File path (str) to a .py file
                - Python source code as string
                - Python source code as bytes

        Returns:
            List of MethodInfo objects for public methods in the first class
        """
        # Determine if source is a file path or source code
        if isinstance(source, str) and os.path.isfile(source):
            with open(source, 'r') as f:
                code = f.read()
        elif isinstance(source, bytes):
            code = source.decode('utf-8')
        else:
            code = source

        # Parse the source code
        tree = ast.parse(code)

        self._methods = []
        self._class_name = None

        # Find the first class and extract its methods
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._class_name = node.name
                self._extract_methods_from_class(node)
                break  # Only process first class

        return self._methods

    def _extract_methods_from_class(self, class_node: ast.ClassDef) -> None:
        """Extract methods from a class definition"""
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                # Skip private methods unless explicitly included
                if item.name.startswith('_') and not self.include_private:
                    continue

                # Extract parameter names (excluding 'self')
                params = [
                    arg.arg for arg in item.args.args
                    if arg.arg != 'self'
                ]

                # Get docstring if present
                docstring = ast.get_docstring(item)

                self._methods.append(MethodInfo(
                    name=item.name,
                    params=params,
                    docstring=docstring
                ))

    def extract_all_functions(self, source: Union[str, bytes]) -> List[MethodInfo]:
        """
        Extract ALL functions from source (not just class methods).

        Useful for files that contain standalone functions without a class.

        Args:
            source: File path or source code

        Returns:
            List of MethodInfo for all top-level functions
        """
        if isinstance(source, str) and os.path.isfile(source):
            with open(source, 'r') as f:
                code = f.read()
        elif isinstance(source, bytes):
            code = source.decode('utf-8')
        else:
            code = source

        tree = ast.parse(code)

        functions = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('_') and not self.include_private:
                    continue

                params = [
                    arg.arg for arg in node.args.args
                    if arg.arg != 'self'
                ]
                docstring = ast.get_docstring(node)

                functions.append(MethodInfo(
                    name=node.name,
                    params=params,
                    docstring=docstring
                ))

        return functions
