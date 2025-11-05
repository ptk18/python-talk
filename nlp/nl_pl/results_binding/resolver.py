import re
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from ..parsers.retrieval_index import RetrievalIndex
from ..parsers.semantic_parser import ParsedIntent
from ..parsers.control_flow_parser import ControlFlowType
from ..ast_analyzer.catalog import DomainCatalog, MethodInfo
from ..dynamic_config import DynamicConfig


@dataclass
class ResolvedCommand:
    method_name: str
    params: Dict[str, Any]
    metadata: Dict[str, Any]
    flow_type: ControlFlowType
    condition: Optional[str] = None


class BridgeResolver:
    def __init__(self, catalog: DomainCatalog, confidence_threshold: float = None, config: DynamicConfig = None):
        self.catalog = catalog
        self.config = config

        if config:
            self.confidence_threshold = confidence_threshold or config.get_confidence_threshold()
            self.parameter_mappings = config.get_parameter_mappings()
            self.noise_words = config.get_noise_words()
            self.action_indicators = config.get_action_indicators()
            self.query_indicators = config.get_query_indicators()
        else:
            self.confidence_threshold = confidence_threshold or 5.0
            self.parameter_mappings = {}
            self.noise_words = set()
            self.action_indicators = []
            self.query_indicators = []

        self.retrieval_index = RetrievalIndex(noise_words=self.noise_words)

        all_methods = []
        for class_name in catalog.methods:
            all_methods.extend(catalog.get_methods(class_name))
        self.retrieval_index.index_methods(all_methods)

    def resolve(self, intent: ParsedIntent, class_name: str) -> Tuple[Optional[str], Dict[str, Any], Optional[Dict[str, Any]]]:
        if intent.control_flow and intent.control_flow.root.flow_type != ControlFlowType.SINGLE:
            return self._resolve_complex_flow(intent, class_name)

        results = self.retrieval_index.search(query=intent.raw_text, class_name=class_name, top_k=5)

        if not results:
            return None, {}, {"error": "no_matches", "confidence": 0.0}

        best_result = results[0]

        if best_result.score < self.confidence_threshold:
            alternatives = [
                {"method": r.method_info.name, "score": r.score, "phrase": r.matched_phrase}
                for r in results[:3]
            ]
            return None, {}, {
                "error": "low_confidence",
                "confidence": best_result.score,
                "threshold": self.confidence_threshold,
                "suggestions": alternatives
            }

        if len(results) > 1:
            second_score = results[1].score
            margin = best_result.score - second_score
            if margin < 2.0:
                # Try to resolve ambiguity based on context and method semantics
                resolved_method = self._resolve_ambiguity(intent, results)
                if resolved_method:
                    method_info = resolved_method.method_info
                    refined_slots = self._refine_slots_for_method(intent, method_info)
                    validated_params = self._validate_params(method_info, refined_slots)
                    
                    metadata = {
                        "confidence": resolved_method.score,
                        "matched_phrase": resolved_method.matched_phrase,
                        "matched_method": f"{method_info.class_name}.{method_info.name}",
                        "disambiguation_reason": "semantic_context",
                        "alternatives": [
                            {"method": r.method_info.name, "score": r.score}
                            for r in results[1:3]
                        ]
                    }
                    
                    return method_info.name, validated_params, metadata
                
                alternatives = [
                    {"method": r.method_info.name, "score": r.score, "phrase": r.matched_phrase}
                    for r in results[:3]
                ]
                return None, {}, {
                    "error": "ambiguous",
                    "confidence": best_result.score,
                    "margin": margin,
                    "suggestions": alternatives
                }

        method_info = best_result.method_info
        refined_slots = self._refine_slots_for_method(intent, method_info)
        validated_params = self._validate_params(method_info, refined_slots)

        metadata = {
            "confidence": best_result.score,
            "matched_phrase": best_result.matched_phrase,
            "matched_method": f"{method_info.class_name}.{method_info.name}",
            "alternatives": [
                {"method": r.method_info.name, "score": r.score}
                for r in results[1:3]
            ]
        }

        return method_info.name, validated_params, metadata

    def _refine_slots_for_method(self, intent: ParsedIntent, method_info: MethodInfo) -> Dict[str, Any]:
        refined_slots = dict(intent.slots)
        numbers = re.findall(r'\d+(?:\.\d+)?', intent.raw_text)

        if numbers:
            numeric_params = []
            for param_name, param_type in method_info.params.items():
                type_name = param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)
                if 'int' in type_name.lower() or 'float' in type_name.lower():
                    numeric_params.append(param_name)
                elif param_type == Any:
                    numeric_params.append(param_name)

            for i, num_str in enumerate(numbers):
                numeric_value = float(num_str) if '.' in num_str else int(num_str)
                if i < len(numeric_params):
                    param_name = numeric_params[i]
                    refined_slots[param_name] = numeric_value

        tokens = intent.raw_text.lower().split()
        if intent.action_verb in tokens:
            verb_index = tokens.index(intent.action_verb)
            remaining_text = ' '.join(tokens[verb_index + 1:])

            for num in numbers:
                remaining_text = remaining_text.replace(num, '').strip()

            remaining_tokens = [w for w in remaining_text.split() if w not in self.noise_words]
            remaining_text = ' '.join(remaining_tokens).strip()

            if remaining_text:
                string_params = []
                for param_name, param_type in method_info.params.items():
                    if param_name in refined_slots:
                        continue
                    type_name = param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)
                    if 'str' in type_name.lower():
                        string_params.append(param_name)
                    elif param_type == Any and param_name not in refined_slots:
                        string_params.append(param_name)

                if string_params:
                    refined_slots[string_params[0]] = remaining_text

        return refined_slots

    def _validate_params(self, method_info: Optional[MethodInfo], slots: Dict[str, Any]) -> Dict[str, Any]:
        if not method_info:
            return {}

        validated = {}

        for param_name, param_type in method_info.params.items():
            if param_name in slots:
                validated[param_name] = slots[param_name]

        if not validated and slots:
            param_list = list(method_info.params.items())
            for i, (param_name, param_type) in enumerate(param_list):
                type_name = param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)

                if param_name in self.parameter_mappings:
                    for mapping in self.parameter_mappings[param_name]:
                        if mapping in slots and param_name not in validated:
                            validated[param_name] = slots[mapping]
                            break

                if param_name not in validated:
                    if ('int' in type_name.lower() or 'float' in type_name.lower()):
                        for generic_name in ['value', 'amount', 'level']:
                            if generic_name in slots and param_name not in validated:
                                validated[param_name] = slots[generic_name]
                                break

                    elif ('str' in type_name.lower() or param_type == Any):
                        for generic_name in ['text', 'name', 'title', 'data']:
                            if generic_name in slots and param_name not in validated:
                                validated[param_name] = slots[generic_name]
                                break

        return validated

    def _resolve_complex_flow(self, intent: ParsedIntent, class_name: str) -> Tuple[Optional[str], Dict[str, Any], Optional[Dict[str, Any]]]:
        flow = intent.control_flow
        resolved_commands = []

        if flow.root.flow_type == ControlFlowType.COMPOUND:
            for child in flow.root.children:
                if child.commands:
                    for command in child.commands:
                        method_name, params, metadata = self._resolve_single_command(command.raw_text, class_name)
                        if method_name:
                            resolved_commands.append({
                                "method": method_name,
                                "params": params,
                                "metadata": metadata,
                                "flow_type": "compound"
                            })

        elif flow.root.flow_type == ControlFlowType.CONDITIONAL:
            condition = flow.root.condition
            for command in flow.root.commands:
                method_name, params, metadata = self._resolve_single_command(command.raw_text, class_name)
                if method_name:
                    resolved_commands.append({
                        "method": method_name,
                        "params": params,
                        "metadata": metadata,
                        "flow_type": "conditional",
                        "condition": condition
                    })

        elif flow.root.flow_type == ControlFlowType.LOOP:
            condition = flow.root.condition
            for command in flow.root.commands:
                method_name, params, metadata = self._resolve_single_command(command.raw_text, class_name)
                if method_name:
                    resolved_commands.append({
                        "method": method_name,
                        "params": params,
                        "metadata": metadata,
                        "flow_type": "loop",
                        "condition": condition
                    })

        if not resolved_commands:
            return None, {}, {"error": "no_resolution", "flow_type": flow.root.flow_type.value}

        metadata = {
            "flow_type": flow.root.flow_type.value,
            "resolved_commands": resolved_commands,
            "execution_order": [cmd["method"] for cmd in resolved_commands]
        }

        return None, {}, metadata

    def _resolve_single_command(self, text: str, class_name: str) -> Tuple[Optional[str], Dict[str, Any], Optional[Dict[str, Any]]]:
        results = self.retrieval_index.search(query=text, class_name=class_name, top_k=3)

        if not results:
            return None, {}, {"error": "no_matches"}

        best_result = results[0]
        method_info = best_result.method_info

        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        params = {}
        if numbers:
            numeric_params = [p for p, t in method_info.params.items()
                            if 'int' in str(t).lower() or 'float' in str(t).lower()]
            for i, num_str in enumerate(numbers):
                if i < len(numeric_params):
                    params[numeric_params[i]] = float(num_str) if '.' in num_str else int(num_str)

        metadata = {
            "confidence": best_result.score,
            "matched_phrase": best_result.matched_phrase
        }

        return method_info.name, params, metadata

    def _resolve_ambiguity(self, intent: ParsedIntent, results: List) -> Optional[any]:
        """Resolve ambiguity between methods using semantic context"""
        if len(results) < 2:
            return None

        query_lower = intent.raw_text.lower()

        has_action_intent = any(word in query_lower for word in self.action_indicators)
        has_query_intent = any(word in query_lower for word in self.query_indicators)
        
        # If there's a clear action intent, prefer non-query methods
        if has_action_intent and not has_query_intent:
            for result in results:
                method_info = result.method_info
                # Check if this is likely a query method based on naming patterns
                is_query_method = (
                    method_info.name.startswith(('is_', 'get_', 'check_', 'has_')) or
                    method_info.name.endswith('_status') or
                    'check' in method_info.name.lower() or
                    'status' in method_info.name.lower()
                )
                
                if not is_query_method:
                    return result
        
        # If there's a clear query intent, prefer query methods
        elif has_query_intent and not has_action_intent:
            for result in results:
                method_info = result.method_info
                is_query_method = (
                    method_info.name.startswith(('is_', 'get_', 'check_', 'has_')) or
                    method_info.name.endswith('_status') or
                    'check' in method_info.name.lower() or
                    'status' in method_info.name.lower()
                )
                
                if is_query_method:
                    return result
        
        # Prefer methods with more specific surface forms (longer phrases)
        best_specificity = results[0]
        max_phrase_length = len(best_specificity.matched_phrase.split())
        
        for result in results[1:]:
            phrase_length = len(result.matched_phrase.split())
            if phrase_length > max_phrase_length:
                best_specificity = result
                max_phrase_length = phrase_length
        
        # Only return if there's a significant difference in specificity
        if max_phrase_length > len(results[0].matched_phrase.split()):
            return best_specificity
            
        return None
