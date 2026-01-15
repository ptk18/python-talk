"""
AST-based security validator for user code execution.

This module provides security validation for Python code before execution,
preventing dangerous operations like system access, network operations,
and code injection attacks.
"""

import ast
import os
from typing import Set, List, Tuple

# Feature flag - can be disabled via environment variable
FEATURE_CODE_SANDBOXING = os.getenv("FEATURE_CODE_SANDBOXING", "true").lower() == "true"


class CodeSecurityValidator:
    """AST-based security validator for user code execution."""

    # Modules that are completely forbidden - can access system, network, or bypass security
    FORBIDDEN_MODULES: Set[str] = {
        # System access
        'os', 'subprocess', 'sys', 'shutil', 'pathlib',
        'glob', 'fnmatch', 'tempfile', 'io',
        # Network access
        'socket', 'http', 'urllib', 'requests', 'httpx',
        'ftplib', 'smtplib', 'poplib', 'imaplib', 'telnetlib',
        'asyncio', 'aiohttp', 'websocket', 'ssl',
        # Serialization (can be used for RCE)
        'pickle', 'marshal', 'shelve', 'dill',
        # Code execution and introspection
        'ctypes', 'cffi', 'importlib', 'runpy',
        'code', 'codeop', 'compile', 'dis', 'inspect',
        # Process/thread control
        'multiprocessing', 'threading', 'concurrent',
        'signal', 'atexit',
        # Dangerous builtins access
        'builtins', '__builtin__',
    }

    # Built-in functions that are forbidden
    FORBIDDEN_BUILTINS: Set[str] = {
        'exec', 'eval', 'compile', '__import__',
        'open', 'input', 'breakpoint',
        'globals', 'locals', 'vars', 'dir',
        'getattr', 'setattr', 'delattr', 'hasattr',
        'memoryview', 'bytearray',
    }

    # Allowed modules whitelist (educational context)
    ALLOWED_MODULES: Set[str] = {
        # Math and science
        'math', 'cmath', 'decimal', 'fractions', 'statistics',
        # Data structures
        'collections', 'heapq', 'bisect', 'array',
        # Functional programming
        'itertools', 'functools', 'operator',
        # String and text
        'string', 're', 'textwrap', 'unicodedata',
        # Date and time (read-only)
        'datetime', 'calendar',
        # Type hints
        'typing', 'types',
        # Data classes
        'dataclasses', 'enum', 'abc',
        # JSON (safe serialization)
        'json',
        # Random (for simulations)
        'random',
        # Turtle graphics
        'turtle',
        # Copy operations
        'copy',
        # Pretty printing
        'pprint',
    }

    # Dangerous attribute access patterns (can be used to escape sandbox)
    FORBIDDEN_ATTRIBUTES: Set[str] = {
        '__class__', '__bases__', '__subclasses__', '__mro__',
        '__globals__', '__code__', '__closure__', '__dict__',
        '__reduce__', '__reduce_ex__', '__getstate__', '__setstate__',
        '__init_subclass__', '__set_name__',
        'gi_frame', 'gi_code', 'f_globals', 'f_locals', 'f_builtins',
        'co_code', 'func_globals', 'func_code',
    }

    def __init__(self, strict_mode: bool = True):
        """
        Initialize the validator.

        Args:
            strict_mode: If True, only allow whitelisted modules.
                        If False, only block forbidden modules.
        """
        self.strict_mode = strict_mode
        self.violations: List[str] = []

    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate code and return (is_safe, violations).

        Args:
            code: Python source code to validate

        Returns:
            Tuple of (is_safe: bool, violations: List[str])
        """
        self.violations = []

        # Check if feature is enabled
        if not FEATURE_CODE_SANDBOXING:
            return True, []

        # Try to parse the code
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error at line {e.lineno}: {e.msg}"]

        # Run all security checks
        self._check_imports(tree)
        self._check_calls(tree)
        self._check_attributes(tree)
        self._check_string_patterns(code)

        return len(self.violations) == 0, self.violations

    def _check_imports(self, tree: ast.AST):
        """Check for forbidden imports."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    self._validate_module(module_name, alias.name, node.lineno)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    self._validate_module(module_name, node.module, node.lineno)

                    # Also check imported names for dangerous patterns
                    for alias in node.names:
                        if alias.name in self.FORBIDDEN_BUILTINS:
                            self.violations.append(
                                f"Forbidden import: '{alias.name}' from '{node.module}' (line {node.lineno})"
                            )

    def _validate_module(self, base_module: str, full_module: str, lineno: int):
        """Validate a module import."""
        if base_module in self.FORBIDDEN_MODULES:
            self.violations.append(
                f"Forbidden module: '{full_module}' - system/network access not allowed (line {lineno})"
            )
        elif self.strict_mode and base_module not in self.ALLOWED_MODULES:
            self.violations.append(
                f"Module not whitelisted: '{full_module}' - only educational modules allowed (line {lineno})"
            )

    def _check_calls(self, tree: ast.AST):
        """Check for forbidden function calls."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Direct function calls: exec(), eval(), etc.
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_BUILTINS:
                        self.violations.append(
                            f"Forbidden builtin: '{node.func.id}()' - dangerous operation (line {node.lineno})"
                        )

                # Method calls that might be dangerous
                elif isinstance(node.func, ast.Attribute):
                    # Check for dangerous method names
                    if node.func.attr in ('system', 'popen', 'spawn', 'fork', 'exec'):
                        self.violations.append(
                            f"Forbidden method: '.{node.func.attr}()' - system execution not allowed (line {node.lineno})"
                        )

    def _check_attributes(self, tree: ast.AST):
        """Check for dangerous attribute access patterns."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                if node.attr in self.FORBIDDEN_ATTRIBUTES:
                    self.violations.append(
                        f"Forbidden attribute: '.{node.attr}' - introspection/escape not allowed (line {node.lineno})"
                    )

            # Check for string-based attribute access in Subscript
            elif isinstance(node, ast.Subscript):
                if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                    if node.slice.value in self.FORBIDDEN_ATTRIBUTES:
                        self.violations.append(
                            f"Forbidden attribute access: ['{node.slice.value}'] (line {node.lineno})"
                        )

    def _check_string_patterns(self, code: str):
        """Check for dangerous patterns that might bypass AST checks."""
        dangerous_patterns = [
            ('__import__', 'Dynamic import'),
            ('__builtins__', 'Builtins access'),
            ('__loader__', 'Loader access'),
            ('__spec__', 'Spec access'),
        ]

        for pattern, description in dangerous_patterns:
            if pattern in code:
                # Find approximate line number
                lines = code.split('\n')
                for i, line in enumerate(lines, 1):
                    if pattern in line:
                        self.violations.append(
                            f"Forbidden pattern: '{pattern}' - {description} not allowed (line {i})"
                        )
                        break


def validate_code(code: str, strict_mode: bool = True) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate code.

    Args:
        code: Python source code to validate
        strict_mode: If True, only allow whitelisted modules

    Returns:
        Tuple of (is_safe: bool, violations: List[str])
    """
    validator = CodeSecurityValidator(strict_mode=strict_mode)
    return validator.validate(code)


# Example usage for testing
if __name__ == "__main__":
    # Test cases
    test_cases = [
        # Safe code
        ("import math\nprint(math.sqrt(16))", True, "Safe math import"),
        ("import turtle\nt = turtle.Turtle()", True, "Safe turtle import"),
        ("x = [1, 2, 3]\nprint(sum(x))", True, "Safe list operations"),

        # Dangerous code
        ("import os\nos.system('ls')", False, "OS system call"),
        ("import subprocess\nsubprocess.run(['ls'])", False, "Subprocess call"),
        ("eval('1+1')", False, "Eval call"),
        ("exec('print(1)')", False, "Exec call"),
        ("open('file.txt')", False, "Open call"),
        ("import socket", False, "Socket import"),
        ("x.__class__.__bases__", False, "Class escape attempt"),
        ("__import__('os')", False, "Dynamic import"),
    ]

    print("Code Security Validator Tests")
    print("=" * 50)

    for code, expected_safe, description in test_cases:
        is_safe, violations = validate_code(code)
        status = "PASS" if is_safe == expected_safe else "FAIL"
        print(f"\n[{status}] {description}")
        print(f"  Code: {code[:50]}...")
        print(f"  Expected safe: {expected_safe}, Got: {is_safe}")
        if violations:
            for v in violations:
                print(f"  - {v}")
