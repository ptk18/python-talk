import ast
import importlib.util
from typing import Dict, List, Any


class ObjectAnalyzer:    
    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, Any]:
 
        with open(file_path, 'r') as file:
            source_code = file.read()
        
        tree = ast.parse(source_code)
        analyzer = ObjectAnalyzer()
        return analyzer._analyze_ast(tree)
    
    def _analyze_ast(self, tree: ast.AST) -> Dict[str, Any]:
        result = {
            "has_main_function": False,
            "object_instances": [],
            "main_function_objects": []
        }
        
        main_function = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                result["has_main_function"] = True
                main_function = node
                break
        
        if main_function:
            result["main_function_objects"] = self._analyze_main_function(main_function)
            result["object_instances"] = result["main_function_objects"] 
        
        return result
    
    def _analyze_main_function(self, main_func: ast.FunctionDef) -> List[Dict[str, str]]:
        objects = []
        
        for node in ast.walk(main_func):
            if isinstance(node, ast.Assign):
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    if isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Name):
                            variable_name = node.targets[0].id
                            class_name = node.value.func.id
                            objects.append({
                                "variable_name": variable_name,
                                "class_name": class_name,
                                "instantiation_type": "direct"
                            })
                        elif isinstance(node.value.func, ast.Attribute):
                            variable_name = node.targets[0].id
                            class_name = node.value.func.attr
                            objects.append({
                                "variable_name": variable_name,
                                "class_name": class_name,
                                "instantiation_type": "attribute"
                            })
        
        return objects
    
    @staticmethod
    def get_object_name_for_class(file_path: str, class_name: str) -> str:

        analysis = ObjectAnalyzer.analyze_file(file_path)
        
        if analysis["has_main_function"]:
            for obj in analysis["main_function_objects"]:
                if obj["class_name"] == class_name:
                    return obj["variable_name"]
        
        return class_name.lower()
