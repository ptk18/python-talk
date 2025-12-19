import importlib.util
import inspect
from typing import Dict, List, Tuple, Any
from .catalog import Catalog, ClassInfo, MethodInfo


def extract_from_file(filepath: str) -> Catalog:
    """Load Python source file and extract class and method metadata"""
    spec = importlib.util.spec_from_file_location("module", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    catalog = Catalog()

    classes = inspect.getmembers(module, inspect.isclass)
    for class_name, class_obj in classes:
        if class_obj.__module__ != module.__name__:
            continue

        class_docstring = inspect.getdoc(class_obj)
        methods = []

        members = inspect.getmembers(class_obj, inspect.isfunction)
        for method_name, method_obj in members:
            if method_name.startswith('_'):
                continue

            method_info = extract_method_info(method_obj, class_name)
            methods.append(method_info)

        class_info = ClassInfo(
            name=class_name,
            docstring=class_docstring,
            methods=methods
        )
        catalog.add_class(class_name, class_info)

    return catalog


def extract_method_info(method, class_name: str) -> MethodInfo:
    """Extract metadata from a method"""
    signature = inspect.signature(method)
    params, required = extract_parameter_info(signature)

    return MethodInfo(
        name=method.__name__,
        class_name=class_name,
        parameters=params,
        required_parameters=required,
        return_type=signature.return_annotation if signature.return_annotation != inspect.Signature.empty else None,
        docstring=inspect.getdoc(method)
    )


def extract_parameter_info(signature) -> Tuple[Dict[str, type], List[str]]:
    """Extract parameter types and identify required parameters"""
    params = {}
    required = []

    for param_name, param in signature.parameters.items():
        if param_name == 'self':
            continue

        param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
        params[param_name] = param_type

        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return params, required
