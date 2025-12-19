"""
Command executor for complex command trees
Handles loops, conditionals, and sequences
"""
from typing import Dict, Any, List, Optional, Callable
from .complex_sentence_parser import CommandNode
import re


class ExecutionContext:
    """Context for tracking execution state"""

    def __init__(self, target_object: Any = None):
        self.target_object = target_object
        self.variables = {}
        self.execution_log = []

    def log(self, message: str):
        """Log execution step"""
        self.execution_log.append(message)


class CommandExecutor:
    """Execute command trees against target objects"""

    def __init__(self, command_processor: Callable[[str, Any], Dict[str, Any]]):
        """
        Args:
            command_processor: Function that takes (text, catalog, class_name) and returns
                             {'executable': str, 'method': str, 'parameters': dict, ...}
        """
        self.command_processor = command_processor

    def execute(self, node: CommandNode, context: ExecutionContext, catalog: Any, class_name: str) -> List[str]:
        """
        Execute a command tree and return list of executable Python code

        Returns:
            List of Python statements to execute
        """
        if node.type == 'action':
            return self._execute_action(node, context, catalog, class_name)
        elif node.type == 'sequence':
            return self._execute_sequence(node, context, catalog, class_name)
        elif node.type == 'loop':
            return self._execute_loop(node, context, catalog, class_name)
        elif node.type == 'conditional':
            return self._execute_conditional(node, context, catalog, class_name)
        else:
            context.log(f"Unknown node type: {node.type}")
            return []

    def _execute_action(self, node: CommandNode, context: ExecutionContext, catalog: Any, class_name: str) -> List[str]:
        """Execute a single action"""
        result = self.command_processor(node.text, catalog, class_name)

        if 'error' in result:
            context.log(f"Error processing '{node.text}': {result['error']}")
            return [f"# Error: {result['error']}"]

        executable = result.get('executable', '')
        context.log(f"Action: {node.text} -> {executable}")
        return [executable]

    def _execute_sequence(self, node: CommandNode, context: ExecutionContext, catalog: Any, class_name: str) -> List[str]:
        """Execute a sequence of commands"""
        executables = []
        context.log(f"Sequence start: {len(node.children)} commands")

        for i, child in enumerate(node.children, 1):
            context.log(f"  Step {i}/{len(node.children)}")
            child_executables = self.execute(child, context, catalog, class_name)
            executables.extend(child_executables)

        return executables

    def _execute_loop(self, node: CommandNode, context: ExecutionContext, catalog: Any, class_name: str) -> List[str]:
        """Execute loop construct"""
        iterations = node.metadata.get('iterations', 1)
        context.log(f"Loop: {iterations} iterations")

        executables = []
        executables.append(f"# Loop: {iterations} times")
        executables.append(f"for _loop_var_{id(node)} in range({iterations}):")

        # Execute body once to get commands
        if node.children:
            body_executables = self.execute(node.children[0], context, catalog, class_name)
            # Indent all body commands
            for cmd in body_executables:
                if not cmd.startswith('#'):
                    executables.append(f"    {cmd}")
                else:
                    executables.append(cmd)

        return executables

    def _execute_conditional(self, node: CommandNode, context: ExecutionContext, catalog: Any, class_name: str) -> List[str]:
        """Execute conditional construct"""
        condition = node.metadata.get('condition', {})
        condition_text = node.metadata.get('condition_text', '')
        context.log(f"Conditional: if {condition_text}")

        executables = []
        executables.append(f"# Conditional: if {condition_text}")

        # Build Python condition
        py_condition = self._build_python_condition(condition, catalog, class_name, context)

        if py_condition:
            executables.append(f"if {py_condition}:")

            # Execute body
            if node.children:
                body_executables = self.execute(node.children[0], context, catalog, class_name)
                # Indent all body commands
                for cmd in body_executables:
                    if not cmd.startswith('#'):
                        executables.append(f"    {cmd}")
                    else:
                        executables.append(cmd)
        else:
            executables.append(f"# Warning: Could not parse condition '{condition_text}'")

        return executables

    def _build_python_condition(self, condition: Dict[str, Any], catalog: Any, class_name: str, context: ExecutionContext) -> Optional[str]:
        """Build Python condition from parsed condition"""

        # Boolean check type (e.g., "pen is down")
        if condition.get('type') == 'boolean_check':
            expression = condition.get('expression', '')

            # Try to process it as a query command
            result = self.command_processor(expression, catalog, class_name)

            if 'error' not in result:
                method_name = result.get('method', '')
                params = result.get('parameters', {})

                # Build method call
                if params:
                    param_str = ', '.join(f"{k}={repr(v)}" for k, v in params.items())
                    return f"obj.{method_name}({param_str})"
                else:
                    return f"obj.{method_name}()"

            # Fallback: look for known query methods
            return self._infer_boolean_method(expression, catalog, class_name)

        # Comparison type (e.g., "x > 50")
        left = condition.get('left', '')
        operator = condition.get('operator', '')
        right = condition.get('right', '')

        if left and operator:
            # Try to process left side as a query
            result = self.command_processor(left, catalog, class_name)

            if 'error' not in result:
                method_name = result.get('method', '')
                params = result.get('parameters', {})

                if params:
                    param_str = ', '.join(f"{k}={repr(v)}" for k, v in params.items())
                    left_expr = f"obj.{method_name}({param_str})"
                else:
                    left_expr = f"obj.{method_name}()"

                # Build comparison
                if isinstance(right, (int, float)):
                    return f"{left_expr} {operator} {right}"
                else:
                    return f"{left_expr} {operator} {repr(right)}"

        return None

    def _infer_boolean_method(self, expression: str, catalog: Any, class_name: str) -> Optional[str]:
        """Infer boolean method from natural language"""
        # Get all methods from catalog
        methods = catalog.get_methods(class_name)

        # Look for methods that start with "is_" or "has_" or "get_"
        expression_lower = expression.lower()

        # Common patterns
        if 'pen' in expression_lower and 'down' in expression_lower:
            return "obj.is_pen_down()"
        if 'pen' in expression_lower and 'up' in expression_lower:
            return "not obj.is_pen_down()"
        if 'visible' in expression_lower:
            return "obj.is_visible()"
        if 'origin' in expression_lower:
            return "obj.is_at_origin()"
        if 'north' in expression_lower:
            return "obj.is_facing_north()"
        if 'south' in expression_lower:
            return "obj.is_facing_south()"
        if 'east' in expression_lower:
            return "obj.is_facing_east()"
        if 'west' in expression_lower:
            return "obj.is_facing_west()"

        # Try to find matching method
        for method in methods:
            method_name_lower = method.name.lower()
            if method_name_lower.startswith('is_') or method_name_lower.startswith('has_'):
                # Check if method name words appear in expression
                method_words = method_name_lower.replace('is_', '').replace('has_', '').split('_')
                if all(word in expression_lower for word in method_words):
                    return f"obj.{method.name}()"

        return None


def format_executable_code(executables: List[str], object_name: str = "turtle_bot") -> str:
    """Format list of executables into complete Python code"""
    lines = []
    lines.append(f"# Generated code")
    lines.append("")

    for executable in executables:
        # Replace 'obj.' with actual object name
        line = executable.replace('obj.', f'{object_name}.')
        lines.append(line)

    return '\n'.join(lines)
