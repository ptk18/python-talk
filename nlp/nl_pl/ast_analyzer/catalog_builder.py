import inspect
import importlib.util
from typing import Any
from .catalog import DomainCatalog, MethodInfo
from .object_analyzer import ObjectAnalyzer
from ..parsers.surface_form_generator import SurfaceFormGenerator
from ..dynamic_config import DynamicConfig


class DomainCatalogBuilder:
    @staticmethod
    def build_from_file(file_path: str) -> DomainCatalog:
        catalog = DomainCatalog()
        config = DynamicConfig(file_path)
        unique_module_name = config.generate_unique_module_name()
        module = DomainCatalogBuilder._load_module(file_path, unique_module_name)

        # Analyze object instances in the file
        object_analysis = ObjectAnalyzer.analyze_file(file_path)
        catalog.object_analysis = object_analysis

        for class_name, class_obj in inspect.getmembers(module, inspect.isclass):
            if class_obj.__module__ == unique_module_name:
                catalog.add_class(class_name, class_obj)

                for method_name, method in inspect.getmembers(class_obj, inspect.isfunction):
                    if not method_name.startswith('_'):
                        method_info = DomainCatalogBuilder._extract_method_info(method, class_name, config)
                        catalog.add_method(class_name, method_info)

        return catalog

    @staticmethod
    def _load_module(file_path: str, module_name: str = None):
        if module_name is None:
            config = DynamicConfig()
            module_name = config.generate_unique_module_name()
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _extract_method_info(func, class_name: str, config: DynamicConfig = None) -> MethodInfo:
        sig = inspect.signature(func)
        params = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
            params[param_name] = param_type
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        docstring = inspect.getdoc(func)
        
        # Use dynamic config to determine if method is a query
        if config:
            query_prefixes = config.get_query_method_prefixes()
        else:
            query_prefixes = ('get_', 'is_', 'has_', 'are_', 'count_')
        
        is_query = func.__name__.startswith(query_prefixes)

        method_info = MethodInfo(
            name=func.__name__,
            class_name=class_name,
            params=params,
            required_params=required,
            docstring=docstring,
            is_query=is_query,
            surface_forms=set()
        )

        method_info.surface_forms = SurfaceFormGenerator.generate_forms(method_info, config)
        return method_info
