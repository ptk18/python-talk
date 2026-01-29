"""
GLiNER + Pydantic Parameter Extractor

Uses GLiNER (zero-shot NER) to extract parameter values from natural language,
then validates/coerces types with Pydantic.

Flow:
  command + method signature
    → GLiNER extracts entities using param names as labels
    → Pydantic validates and coerces types
    → returns {param_name: value}
"""

import re
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError, create_model
from .models import MethodInfo


_TYPE_MAP = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "complex": complex,
}

_NUMERIC_PARAM_NAMES = {
    "price", "amount", "cost", "number", "count", "quantity",
    "distance", "size", "width", "height", "length", "radius",
    "angle", "temperature", "temp", "percentage", "celsius", "humidity",
    "duration", "guests", "days", "a", "b", "x", "y", "n",
    "table_number", "quadrant", "pensize", "speed",
}

_NUMERIC_SUBSTRINGS = {
    "num", "count", "size", "amount", "price", "cost",
    "distance", "angle", "temp", "percent", "duration",
    "width", "height", "length", "radius",
}

_NUMBER_RE = re.compile(r"-?\d+\.?\d*")


class ParamExtractor:

    def extract(self, command: str, method: MethodInfo) -> Dict[str, object]:
        params = [p for p in method.params if p != "self"]
        if not params:
            return {}

        from . import get_gliner_model
        model = get_gliner_model()
        if model is None:
            return {}

        labels, label_to_params = self._build_labels(params, method)
        entities = model.predict_entities(command, labels, threshold=0.3)
        raw = self._map_entities(entities, label_to_params)

        # Fallback: fill missing numeric params via regex
        unfilled_numeric = [
            p for p in params
            if p not in raw and self._is_numeric_param(p, method.param_types)
        ]
        if unfilled_numeric:
            numbers = _NUMBER_RE.findall(command)
            used_numbers = {str(self._extract_number(v)) for v in raw.values()
                           if self._extract_number(str(v)) is not None}
            for p in unfilled_numeric:
                for n in numbers:
                    if n not in used_numbers:
                        raw[p] = n
                        used_numbers.add(n)
                        break

        return self._validate(raw, params, method.param_types)

    def _build_labels(
        self, params: List[str], method: MethodInfo
    ) -> Tuple[List[str], Dict[str, List[str]]]:
        """Build NER labels from param names + method context.

        Returns (unique_labels, label_to_param_names_mapping).
        Multiple params can share a label (e.g., a, b both → 'number').
        """
        context_noun = self._extract_context_noun(method)
        label_to_params: Dict[str, List[str]] = {}
        seen_labels = []

        for p in params:
            label = p.replace("_", " ")
            if context_noun and label in ("title", "name", "item"):
                label = f"{context_noun} {label}"

            if label not in label_to_params:
                label_to_params[label] = []
                seen_labels.append(label)
            label_to_params[label].append(p)

        return seen_labels, label_to_params

    def _extract_context_noun(self, method: MethodInfo) -> str:
        parts = method.name.split("_")
        skip = {"add", "remove", "get", "set", "create", "delete", "update",
                "to", "from", "by", "the", "a", "an"}
        for part in parts:
            if part.lower() not in skip:
                return part.lower()
        return ""

    def _map_entities(
        self,
        entities: List[dict],
        label_to_params: Dict[str, List[str]],
    ) -> Dict[str, str]:
        """Map GLiNER entities to param names.

        When multiple params share a label (e.g., a, b both → 'number'),
        entities are assigned by position in the text.
        """
        # Group entities by label, sorted by position
        by_label: Dict[str, List[dict]] = {}
        for ent in entities:
            label = ent["label"]
            if label not in by_label:
                by_label[label] = []
            by_label[label].append(ent)

        result: Dict[str, str] = {}
        for label, param_names in label_to_params.items():
            ents = by_label.get(label, [])
            ents.sort(key=lambda e: e["start"])

            if len(param_names) == 1:
                # Single param for this label — pick highest score
                if ents:
                    best = max(ents, key=lambda e: e.get("score", 0))
                    result[param_names[0]] = best["text"]
            else:
                # Multiple params share this label — assign by text position (left to right)
                assigned = set()
                for pname in param_names:
                    for e in ents:
                        eid = (e["start"], e["end"])
                        if eid in assigned:
                            continue
                        result[pname] = e["text"]
                        assigned.add(eid)
                        break

        return result

    def _validate(
        self,
        raw: Dict[str, str],
        params: List[str],
        param_types: Optional[Dict[str, str]],
    ) -> Dict[str, object]:
        """Validate and coerce extracted values using Pydantic."""
        if not raw:
            return {}

        # Pre-process: extract numeric part from strings like "50 THB", "6 minutes"
        cleaned = {}
        for p, val in raw.items():
            if self._is_numeric_param(p, param_types):
                num = self._extract_number(val)
                cleaned[p] = num if num is not None else val
            else:
                cleaned[p] = val

        fields = {}
        for p in params:
            py_type = self._resolve_type(p, param_types)
            if p in cleaned:
                fields[p] = (py_type, ...)
            else:
                fields[p] = (Optional[py_type], None)

        try:
            Model = create_model("ExtractedParams", **fields)
            validated = Model(**cleaned)
            result = validated.model_dump(exclude_none=True)
            return {k: v for k, v in result.items() if k in raw}
        except ValidationError:
            return {k: v for k, v in cleaned.items() if k in raw}

    def _extract_number(self, text: str) -> Optional[float]:
        """Pull the first number from a string like '50 THB' → 50."""
        m = _NUMBER_RE.search(text)
        if m:
            val = m.group()
            return float(val) if "." in val else int(val)
        return None

    def _is_numeric_param(self, name: str, param_types: Optional[Dict[str, str]] = None) -> bool:
        if param_types and name in param_types:
            t = param_types[name].lower()
            if t in ("int", "float", "complex", "number", "numeric"):
                return True
            if t == "str":
                return False
        name_lower = name.lower()
        if name_lower in _NUMERIC_PARAM_NAMES:
            return True
        return any(s in name_lower for s in _NUMERIC_SUBSTRINGS)

    def _resolve_type(self, name: str, param_types: Optional[Dict[str, str]]) -> type:
        if param_types and name in param_types:
            type_str = param_types[name].lower()
            if type_str in _TYPE_MAP:
                return _TYPE_MAP[type_str]
        if self._is_numeric_param(name, param_types):
            return float
        return str
