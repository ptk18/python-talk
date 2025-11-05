from typing import Tuple, Dict, Any
from .parsers.semantic_parser import SemanticNLParser
from .ast_analyzer.catalog_builder import DomainCatalogBuilder
from .results_binding.resolver import BridgeResolver
from .results_binding.json_exporter import JSONExporter
from .dynamic_config import DynamicConfig


class NaturalLanguageInterface:
    def __init__(self, python_file: str, class_name: str, output_dir: str = None):
        self.python_file = python_file
        self.class_name = class_name
        
        self.config = DynamicConfig(python_file)
        
        if output_dir is None:
            output_dir = self.config.get_output_dir()

        self.catalog = DomainCatalogBuilder.build_from_file(python_file)

        if class_name not in self.catalog.classes:
            raise ValueError(f"Class '{class_name}' not found in {python_file}")

        self.parser = SemanticNLParser(self.catalog, self.config)
        self.resolver = BridgeResolver(self.catalog, config=self.config)
        self.json_exporter = JSONExporter(output_dir)

    def process(self, text: str, export_json: bool = True) -> Tuple[str, Dict[str, Any], Dict[str, Any]]:
        available_methods = self.catalog.get_methods(self.class_name)

        intent = self.parser.parse_command(text, available_methods)
        method_name, params, metadata = self.resolver.resolve(intent, self.class_name)

        result = {
            "input_text": text,
            "linguistic_analysis": self._build_linguistic_analysis(intent),
            "semantic_parsing": {
                "parsed_structure": f"{self.class_name}.{intent.action_verb}({', '.join(f'{k}={v}' for k, v in intent.slots.items())})" if intent.slots else f"{self.class_name}.{intent.action_verb}()",
                "target_class": self.class_name,
                "action_verb": intent.action_verb,
                "intent_type": intent.intent_type,
                "extracted_slots": intent.slots
            },
            "control_flow": self._build_control_flow_analysis(intent),
            "method_resolution": {
                "matched_method": f"{self.class_name}.{method_name}" if method_name else None,
                "parameters": params,
                "metadata": metadata
            }
        }

        if export_json:
            json_path = self.json_exporter.export_full_analysis(
                text, intent, method_name, params, metadata, self.class_name
            )
            result["exported_json"] = json_path

        return method_name, params, result

    def _build_linguistic_analysis(self, intent) -> Dict[str, Any]:
        analysis = {}

        if intent.syntactic_parse:
            analysis["pos_tags"] = [
                {"text": t.text, "pos": t.pos, "lemma": t.lemma}
                for t in intent.syntactic_parse.tokens
            ]
            analysis["noun_phrases"] = intent.syntactic_parse.noun_phrases
            analysis["verb_phrases"] = [
                {"verb": vp[0], "dependents": vp[1]}
                for vp in intent.syntactic_parse.verb_phrases
            ]

        if intent.semantic_analysis:
            analysis["semantic_frames"] = [
                {
                    "action": frame.action,
                    "roles": {role.value: value for role, value in frame.roles.items()},
                    "confidence": frame.confidence
                }
                for frame in intent.semantic_analysis.frames
            ]

        if intent.expressions:
            analysis["expressions"] = [
                {
                    "type": expr.expr_type.value,
                    "operator": expr.operator.value if expr.operator else None,
                    "left": expr.left,
                    "right": expr.right,
                    "raw": expr.raw
                }
                for expr in intent.expressions
            ]

        return analysis

    def _build_control_flow_analysis(self, intent) -> Dict[str, Any]:
        if not intent.control_flow:
            return {"type": "single"}

        flow = intent.control_flow.root
        analysis = {
            "type": flow.flow_type.value,
            "condition": flow.condition,
            "commands": [
                {
                    "action": cmd.action,
                    "params": cmd.params,
                    "raw_text": cmd.raw_text
                }
                for cmd in flow.commands
            ]
        }

        if flow.children:
            analysis["sub_commands"] = [
                {
                    "type": child.flow_type.value,
                    "commands": [
                        {"action": cmd.action, "params": cmd.params}
                        for cmd in child.commands
                    ]
                }
                for child in flow.children
            ]

        return analysis

    def export_ast_analysis(self):
        methods = self.catalog.get_methods(self.class_name)
        object_analysis = getattr(self.catalog, 'object_analysis', {})
        return self.json_exporter.export_ast_analysis(self.class_name, methods, object_analysis=object_analysis)

    def get_class_instance(self, *args, **kwargs):
        class_obj = self.catalog.classes[self.class_name]
        return class_obj(*args, **kwargs)
    
    def get_object_name_for_class(self, class_name: str = None) -> str:
        """Get the object variable name for the specified class or current class"""
        if class_name is None:
            class_name = self.class_name
        return self.catalog.get_object_name_for_class(class_name)
