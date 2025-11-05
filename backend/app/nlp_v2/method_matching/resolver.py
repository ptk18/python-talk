from typing import Dict, Tuple, Any
from app.nlp_v2.extract_catalog_from_source_code.catalog import MethodInfo
from app.nlp_v2.semantic_parsing.intent_parser import Intent


def resolve_parameters(intent: Intent, method_info: MethodInfo, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Map extracted parameters to method parameter names"""
    resolved = {}
    numbers = parameters.get("numbers", []).copy()
    strings = parameters.get("strings", []).copy()
    boolean = parameters.get("boolean")

    for param_name, param_type in method_info.parameters.items():
        type_name = get_parameter_type_name(param_type)

        if type_name in ["int", "float", "Any"] and numbers:
            resolved[param_name] = numbers.pop(0)
        elif type_name == "str" and strings:
            resolved[param_name] = strings.pop(0)
        elif type_name == "bool" and boolean is not None:
            resolved[param_name] = boolean

    return resolved


def validate_parameters(params: Dict[str, Any], method_info: MethodInfo) -> Tuple[bool, str]:
    """Check all required parameters are present and type-compatible"""
    for required_param in method_info.required_parameters:
        if required_param not in params:
            return False, f"Missing required parameter: {required_param}"

    for param_name, value in params.items():
        if param_name in method_info.parameters:
            expected_type = method_info.parameters[param_name]
            if not is_type_compatible(value, expected_type):
                return False, f"Type mismatch for {param_name}: expected {get_parameter_type_name(expected_type)}"

    return True, ""


def generate_function_call(method_info: MethodInfo, params: Dict[str, Any]) -> str:
    """Format as executable function call string"""
    param_strs = []
    for param_name, value in params.items():
        formatted_value = format_parameter_value(value)
        param_strs.append(f"{param_name}={formatted_value}")

    params_str = ", ".join(param_strs)
    return f"{method_info.name}({params_str})"


def get_parameter_type_name(param_type: type) -> str:
    """Extract clean type name"""
    return param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)


def is_type_compatible(value: Any, expected_type: type) -> bool:
    """Check type compatibility"""
    if expected_type is Any:
        return True

    type_name = get_parameter_type_name(expected_type)

    if type_name == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    elif type_name == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif type_name == "str":
        return isinstance(value, str)
    elif type_name == "bool":
        return isinstance(value, bool)

    return isinstance(value, expected_type)


def format_parameter_value(value: Any) -> str:
    """Format value for function call string"""
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return str(value)
    else:
        return str(value)
