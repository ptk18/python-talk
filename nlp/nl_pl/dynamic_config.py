import ast
import inspect
import importlib.util
from typing import Set, List, Dict, Any, Tuple, Optional
import uuid
from datetime import datetime
from collections import defaultdict, Counter
import re


class DynamicConfig:
    def __init__(self, python_file: str = None):
        self.python_file = python_file
        self._ast_tree = None
        self._methods_info = {}
        self._discovered_patterns = {}
        
        if python_file:
            self._analyze_file(python_file)
    
    def _analyze_file(self, file_path: str):
        with open(file_path, 'r') as f:
            source_code = f.read()
        
        self._ast_tree = ast.parse(source_code)
        self._extract_methods_info()
        self._discover_patterns()
    
    def _extract_methods_info(self):
        for node in ast.walk(self._ast_tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                self._methods_info[class_name] = {}
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_name = item.name
                        if not method_name.startswith('_'):
                            self._methods_info[class_name][method_name] = {
                                'params': [arg.arg for arg in item.args.args if arg.arg != 'self'],
                                'docstring': ast.get_docstring(item),
                                'returns': self._analyze_return_type(item),
                                'calls': self._extract_method_calls(item)
                            }
    
    def _analyze_return_type(self, func_node: ast.FunctionDef) -> str:
        return_types = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.Return) and node.value:
                if isinstance(node.value, ast.Constant):
                    return_types.append(type(node.value.value).__name__)
                elif isinstance(node.value, ast.Name):
                    return_types.append('variable')
        return 'query' if return_types else 'action'
    
    def _extract_method_calls(self, func_node: ast.FunctionDef) -> List[str]:
        calls = []
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        return calls
    
    def _discover_patterns(self):
        self._discover_query_prefixes()
        self._discover_parameter_patterns()
        self._discover_semantic_patterns()
    
    def _discover_query_prefixes(self) -> Tuple[str, ...]:
        query_prefixes = set()

        for class_name, methods in self._methods_info.items():
            for method_name, info in methods.items():
                if info['returns'] == 'query' or any(ret_call in ['return', 'get'] for ret_call in info['calls']):
                    if '_' in method_name:
                        prefix = method_name.split('_')[0]
                        query_prefixes.add(prefix)
                    else:
                        for i in range(2, min(len(method_name), 6)):
                            query_prefixes.add(method_name[:i])

        self._discovered_patterns['query_prefixes'] = tuple(query_prefixes)
        return self._discovered_patterns['query_prefixes']
    
    def _discover_parameter_patterns(self) -> Dict[str, List[str]]:
        param_patterns = defaultdict(set)
        
        for class_name, methods in self._methods_info.items():
            for method_name, info in methods.items():
                for param in info['params']:
                    param_lower = param.lower()
                    
                    if any(spatial in param_lower for spatial in ['x', 'y', 'pos', 'coord', 'location']):
                        param_patterns['position'].add(param)
                        if 'x' in param_lower:
                            param_patterns['x'].update([param, 'x_pos', 'x_coordinate', 'horizontal'])
                        if 'y' in param_lower:
                            param_patterns['y'].update([param, 'y_pos', 'y_coordinate', 'vertical'])
                    
                    elif any(qty in param_lower for qty in ['amount', 'value', 'sum', 'count', 'num', 'quantity']):
                        param_patterns['amount'].update([param, 'value', 'sum', 'quantity', 'number'])
                    
                    elif any(name in param_lower for name in ['name', 'id', 'title', 'label']):
                        param_patterns['name'].update([param, 'name', 'title', 'identifier', 'label'])
                    
                    elif any(color in param_lower for color in ['color', 'colour', 'hue', 'shade']):
                        param_patterns['color'].update([param, 'color', 'colour', 'hue', 'shade'])
                    
                    elif any(size in param_lower for size in ['size', 'width', 'height', 'length', 'dimension']):
                        param_patterns['size'].update([param, 'size', 'dimension', 'width', 'height', 'length'])
        
        self._discovered_patterns['parameter_mappings'] = {k: list(v) for k, v in param_patterns.items()}
        return self._discovered_patterns['parameter_mappings']
    
    def _discover_semantic_patterns(self):
        query_verbs = set()
        action_verbs = set()
        query_indicators = set()
        action_indicators = set()

        for class_name, methods in self._methods_info.items():
            for method_name, info in methods.items():
                method_words = re.findall(r'[a-z]+', method_name.lower())

                if info['returns'] == 'query':
                    for word in method_words:
                        if len(word) > 2:
                            query_verbs.add(word)
                            query_indicators.add(word)

                    if info['docstring']:
                        doc_words = re.findall(r'\b[a-z]{3,}\b', info['docstring'].lower())
                        for word in doc_words[:5]:
                            query_indicators.add(word)
                else:
                    for word in method_words:
                        if len(word) > 2:
                            action_verbs.add(word)
                            action_indicators.add(word)

                    if info['docstring']:
                        doc_words = re.findall(r'\b[a-z]{3,}\b', info['docstring'].lower())
                        for word in doc_words[:5]:
                            action_indicators.add(word)

        self._discovered_patterns['query_verbs'] = list(query_verbs)
        self._discovered_patterns['action_verbs'] = list(action_verbs)
        self._discovered_patterns['query_indicators'] = list(query_indicators)
        self._discovered_patterns['action_indicators'] = list(action_indicators)
    
    def _discover_noise_words_from_context(self, text_samples: List[str] = None) -> Set[str]:
        if not text_samples:
            text_samples = []
            for class_name, methods in self._methods_info.items():
                for method_name, info in methods.items():
                    if info['docstring']:
                        text_samples.append(info['docstring'].lower())

        noise_words = set()

        if text_samples:
            word_freq = Counter()
            for text in text_samples:
                words = re.findall(r'\b[a-z]+\b', text)
                word_freq.update(words)

            total_words = sum(word_freq.values())

            for word, freq in word_freq.items():
                if len(word) <= 3 and freq / total_words > 0.01:
                    noise_words.add(word)

        return noise_words
    
    def get_output_dir(self) -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"nl_pl/output/analysis_{timestamp}"
    
    def generate_unique_module_name(self) -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"dynamic_module_{timestamp}_{unique_id}"
    
    def get_query_method_prefixes(self) -> Tuple[str, ...]:
        if 'query_prefixes' not in self._discovered_patterns:
            self._discover_query_prefixes()
        return self._discovered_patterns['query_prefixes']
    
    def get_query_verbs(self) -> List[str]:
        if 'query_verbs' not in self._discovered_patterns:
            self._discover_semantic_patterns()
        return self._discovered_patterns['query_verbs']

    def get_query_indicators(self) -> List[str]:
        if 'query_indicators' not in self._discovered_patterns:
            self._discover_semantic_patterns()
        return self._discovered_patterns.get('query_indicators', [])

    def get_action_indicators(self) -> List[str]:
        if 'action_indicators' not in self._discovered_patterns:
            self._discover_semantic_patterns()
        return self._discovered_patterns.get('action_indicators', [])
    
    def get_parameter_mappings(self) -> Dict[str, List[str]]:
        if 'parameter_mappings' not in self._discovered_patterns:
            self._discover_parameter_patterns()
        return self._discovered_patterns['parameter_mappings']
    
    def get_noise_words(self, text_samples: List[str] = None) -> Set[str]:
        return self._discover_noise_words_from_context(text_samples)
    
    def get_confidence_threshold(self) -> float:
        if not self._methods_info:
            return 5.0
        
        total_params = 0
        method_count = 0
        
        for class_name, methods in self._methods_info.items():
            for method_name, info in methods.items():
                total_params += len(info['params'])
                method_count += 1
        
        if method_count == 0:
            return 5.0
        
        avg_complexity = total_params / method_count
        return max(3.0, min(10.0, avg_complexity * 1.5))
    
    def analyze_and_report(self) -> Dict[str, Any]:
        return {
            'file_analyzed': self.python_file,
            'classes_found': list(self._methods_info.keys()),
            'total_methods': sum(len(methods) for methods in self._methods_info.values()),
            'query_prefixes': self.get_query_method_prefixes(),
            'query_verbs': self.get_query_verbs(),
            'parameter_mappings': self.get_parameter_mappings(),
            'confidence_threshold': self.get_confidence_threshold(),
            'noise_words_count': len(self.get_noise_words()),
            'timestamp': datetime.now().isoformat()
        }
