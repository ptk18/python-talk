import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class JSONExporter:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def export_nl_analysis(self, text: str, intent, metadata: Dict[str, Any]) -> str:
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "input_text": text,
            "semantic_parsing": {
                "target_class": intent.target_class,
                "action_verb": intent.action_verb,
                "intent_type": intent.intent_type,
                "extracted_slots": intent.slots
            },
            "retrieval_metadata": metadata
        }

        filename = self.output_dir / f"nl_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)

        return str(filename)

    def export_ast_analysis(self, class_name: str, methods: List, properties: List = None, object_analysis: Dict = None) -> str:
        ast_data = {
            "timestamp": datetime.now().isoformat(),
            "class_name": class_name,
            "methods": [
                {
                    "name": m.name,
                    "parameters": {
                        param_name: param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)
                        for param_name, param_type in m.params.items()
                    },
                    "required_parameters": m.required_params,
                    "docstring": m.docstring,
                    "is_query": m.is_query,
                    "surface_forms": list(m.surface_forms)
                }
                for m in methods
            ],
            "properties": properties or [],
            "object_analysis": object_analysis or {}
        }

        filename = self.output_dir / f"ast_analysis_{class_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(ast_data, f, indent=2)

        return str(filename)

    def export_resolution_result(self, text: str, method_name: str, params: Dict[str, Any],
                                 metadata: Dict[str, Any], class_name: str) -> str:
        result = {
            "timestamp": datetime.now().isoformat(),
            "input_text": text,
            "resolved_method": f"{class_name}.{method_name}",
            "parameters": params,
            "metadata": metadata
        }

        filename = self.output_dir / f"resolution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)

        return str(filename)

    def export_full_analysis(self, text: str, intent, method_name: str, params: Dict[str, Any],
                            metadata: Dict[str, Any], class_name: str) -> str:
        full_analysis = {
            "timestamp": datetime.now().isoformat(),
            "input": {
                "raw_text": text
            },
            "step1_semantic_parsing": {
                "target_class": intent.target_class,
                "action_verb": intent.action_verb,
                "intent_type": intent.intent_type,
                "extracted_slots": intent.slots
            },
            "step2_method_resolution": {
                "matched_method": f"{class_name}.{method_name}" if method_name else None,
                "confidence": metadata.get("confidence"),
                "matched_phrase": metadata.get("matched_phrase"),
                "alternatives": metadata.get("alternatives", [])
            },
            "step3_parameter_binding": {
                "parameters": params
            }
        }

        filename = self.output_dir / f"full_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(full_analysis, f, indent=2)

        return str(filename)
