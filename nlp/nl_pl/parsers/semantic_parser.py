import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .syntactic_parser import SyntacticParser, SyntacticParse
from .semantic_analyzer import SemanticAnalyzer, SemanticAnalysis, SemanticRole
from .expression_parser import ExpressionParser, Expression
from .control_flow_parser import ControlFlowParser, ControlFlowStructure
from ..dynamic_config import DynamicConfig


@dataclass
class ParsedIntent:
    target_class: Optional[str]
    action_verb: str
    intent_type: str
    slots: Dict[str, Any]
    raw_text: str
    syntactic_parse: Optional[SyntacticParse] = None
    semantic_analysis: Optional[SemanticAnalysis] = None
    expressions: List[Expression] = field(default_factory=list)
    control_flow: Optional[ControlFlowStructure] = None


class SemanticNLParser:
    def __init__(self, catalog=None, config: DynamicConfig = None):
        self.catalog = catalog
        self.config = config
        self.syntactic_parser = SyntacticParser()
        self.expression_parser = ExpressionParser()

        if config:
            self.noise_words = config.get_noise_words()
            self.query_indicators = set(config.get_query_indicators())
        else:
            self.noise_words = set()
            self.query_indicators = set()

    def parse_command(self, text: str, available_methods=None) -> ParsedIntent:
        text_lower = text.lower().strip()
        tokens = self._tokenize(text_lower)

        known_actions = self._extract_known_actions(available_methods)

        self.semantic_analyzer = SemanticAnalyzer(known_actions=known_actions)
        self.control_flow_parser = ControlFlowParser(known_actions=known_actions)

        syntactic_parse = self.syntactic_parser.parse(text)
        semantic_analysis = self.semantic_analyzer.analyze(syntactic_parse)
        expressions = self.expression_parser.parse(text)
        control_flow = self.control_flow_parser.parse(text, syntactic_parse, semantic_analysis)

        intent_type = "query" if any(q in tokens for q in self.query_indicators) else "action"
        verb_candidates = self._extract_verb_candidates_deep(syntactic_parse, semantic_analysis, tokens, available_methods)
        action_verb = verb_candidates[0] if verb_candidates else (tokens[0] if tokens else "")
        slots = self._extract_slots_deep(text, tokens, available_methods, action_verb, semantic_analysis, expressions)

        return ParsedIntent(
            target_class=None,
            action_verb=action_verb,
            intent_type=intent_type,
            slots=slots,
            raw_text=text,
            syntactic_parse=syntactic_parse,
            semantic_analysis=semantic_analysis,
            expressions=expressions,
            control_flow=control_flow
        )

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\b\w+\b', text)

    def _extract_known_actions(self, methods) -> set:
        """Extract action verbs from available methods (lemmatized)"""
        known_actions = set()
        if methods:
            for method in methods:
                parts = method.name.lower().split('_')
                known_actions.update(parts)
        return known_actions

    def _extract_verb_candidates_deep(self, syntactic_parse: SyntacticParse, semantic_analysis: SemanticAnalysis, tokens: List[str], methods) -> List[str]:
        candidates = []

        for frame in semantic_analysis.frames:
            if frame.action:
                candidates.append(frame.action)

        for token in syntactic_parse.tokens:
            if token.pos == "VERB" and token.lemma not in candidates:
                candidates.append(token.lemma)

        if methods:
            text = ' '.join(tokens)
            for method in methods:
                method_phrase = method.name.lower().replace('_', ' ')
                if method_phrase in text:
                    candidates.extend(method.name.lower().split('_'))

        if not candidates:
            for token in tokens:
                if token not in self.noise_words and len(token) > 2:
                    candidates.append(token)

        return candidates

    def _extract_verb_candidates(self, tokens: List[str], methods) -> List[str]:
        if not methods:
            return [t for t in tokens if t not in self.noise_words]

        candidates = []
        text = ' '.join(tokens)

        for method in methods:
            method_phrase = method.name.lower().replace('_', ' ')
            if method_phrase in text:
                candidates.extend(method.name.lower().split('_'))

        for method in methods:
            method_parts = method.name.lower().split('_')
            for part in method_parts:
                if part in tokens and part not in candidates:
                    candidates.append(part)

        if not candidates:
            for token in tokens:
                if token not in self.noise_words and len(token) > 2:
                    candidates.append(token)

        return candidates

    def _extract_slots_deep(self, text: str, tokens: List[str], methods, verb: str, semantic_analysis: SemanticAnalysis, expressions: List[Expression]) -> Dict[str, Any]:
        slots = {}

        for frame in semantic_analysis.frames:
            for role, value in frame.roles.items():
                if role != SemanticRole.ACTION:
                    slots[role.value] = value

        for expr in expressions:
            if hasattr(expr, 'left') and expr.left is not None:
                if isinstance(expr.left, (int, float)):
                    slots['value'] = expr.left
                    slots['amount'] = expr.left
            if hasattr(expr, 'operator') and expr.operator:
                slots['operator'] = expr.operator.value

        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        if numbers and methods:
            numeric_params = self._get_numeric_param_names(methods)
            for i, num_str in enumerate(numbers):
                numeric_value = float(num_str) if '.' in num_str else int(num_str)
                if i < len(numeric_params):
                    slots[numeric_params[i]] = numeric_value
                else:
                    slots[f'param_{i}'] = numeric_value

        text_values = self._extract_text_after_verb(text, tokens, verb)
        if text_values and methods:
            string_params = self._get_string_param_names(methods)
            if string_params:
                slots[string_params[0]] = text_values

        bool_state = self._extract_boolean_state(text)
        if bool_state is not None:
            slots['state'] = bool_state

        return slots

    def _extract_slots_semantic(self, text: str, tokens: List[str], methods, verb: str) -> Dict[str, Any]:
        slots = {}
        numbers = re.findall(r'\d+(?:\.\d+)?', text)

        if numbers and methods:
            numeric_params = self._get_numeric_param_names(methods)
            for i, num_str in enumerate(numbers):
                numeric_value = float(num_str) if '.' in num_str else int(num_str)
                if i < len(numeric_params):
                    slots[numeric_params[i]] = numeric_value
                else:
                    slots[f'param_{i}'] = numeric_value
                if i == 0:
                    slots['value'] = numeric_value
                    slots['amount'] = numeric_value
                    slots['level'] = numeric_value
        elif numbers:
            numeric_value = float(numbers[0]) if '.' in numbers[0] else int(numbers[0])
            slots['value'] = numeric_value
            slots['amount'] = numeric_value
            slots['level'] = numeric_value

        text_values = self._extract_text_after_verb(text, tokens, verb)
        if text_values:
            if methods:
                string_params = self._get_string_param_names(methods)
                if string_params:
                    slots[string_params[0]] = text_values
                    slots['text'] = text_values
                    slots['name'] = text_values
                    slots['title'] = text_values
            else:
                slots['text'] = text_values
                slots['name'] = text_values
                slots['title'] = text_values

        bool_state = self._extract_boolean_state(text)
        if bool_state is not None:
            slots['state'] = bool_state

        return slots

    def _get_numeric_param_names(self, methods) -> List[str]:
        param_names = set()
        for method in methods:
            for param_name, param_type in method.params.items():
                type_name = param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)
                if 'int' in type_name.lower() or 'float' in type_name.lower() or 'number' in type_name.lower():
                    param_names.add(param_name)
        return list(param_names)

    def _get_string_param_names(self, methods) -> List[str]:
        param_names = set()
        for method in methods:
            for param_name, param_type in method.params.items():
                type_name = param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)
                if 'str' in type_name.lower() or 'text' in type_name.lower() or param_type == Any:
                    param_names.add(param_name)
        return list(param_names)

    def _extract_text_after_verb(self, text: str, tokens: List[str], verb: str) -> Optional[str]:
        if verb not in tokens:
            return None
        verb_index = tokens.index(verb)
        remaining = tokens[verb_index + 1:]
        clean_tokens = [t for t in remaining if t not in self.noise_words and not t.isdigit()]
        return ' '.join(clean_tokens) if clean_tokens else None

    def _extract_boolean_state(self, text: str) -> Optional[bool]:
        text_lower = text.lower()
        if 'on' in text_lower or 'true' in text_lower or 'yes' in text_lower or 'enable' in text_lower:
            return True
        if 'off' in text_lower or 'false' in text_lower or 'no' in text_lower or 'disable' in text_lower:
            return False
        return None
