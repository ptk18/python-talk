# backend/app/parser_engine/api.py
from __future__ import annotations

from typing import Any, Dict, Optional
import threading

from app.parser_engine.lex_alz import setup_nltk
from app.parser_engine.phase2_domain import load_domain
from app.parser_engine import main_process


_nltk_lock = threading.Lock()
_nltk_ready = False


def _ensure_nltk():
    global _nltk_ready
    if _nltk_ready:
        return
    with _nltk_lock:
        if not _nltk_ready:
            setup_nltk()
            _nltk_ready = True


def compile_single(command_text: str, module_path: str) -> Dict[str, Any]:
    """
    Deterministic compile (no AI model):
      NL command -> (lex -> domain -> grammar -> code)

    Returns dict used by analyze_command.py.
    """
    _ensure_nltk()

    domain = load_domain(module_path)

    out = main_process.run(command_text, module_path)
    if not out:
        return {"status": "no_match", "explanation": "Empty parser output", "meta": {}}

    last = out[-1] if isinstance(out, list) else out
    action = last.get("code_function")
    args = last.get("args", {}) or {}

    ranked = last.get("docstring_similarity_ranked") or []
    top_score = float(ranked[0]["score"]) if ranked else 0.0
    confidence = max(0.0, min(1.0, top_score)) * 100.0

    if not action:
        return {
            "status": "no_match",
            "confidence": confidence,
            "explanation": "No action selected",
            "meta": {"ranked": ranked},
        }

    # Missing-argument detection (required params missing)
    required = (domain.get("ACTIONS", {}).get(action, {}) or {}).get("params", []) or []
    missing = [p for p in required if (p not in args) or (args.get(p) in (None, "", []))]

    if missing:
        # simple question
        q = f"{action.replace('_', ' ')} what?"
        return {
            "status": "need_clarification",
            "method": action,
            "parameters": args,
            "confidence": confidence,
            "question": q,
            "explanation": f"Missing required parameter(s): {missing}",
            "meta": {"missing": missing, "ranked": ranked},
        }

    # Build executable: only include required params - freya fix
    parts = []
    if required:
        for p in required:
            parts.append(f"{p}={repr(args.get(p))}")
    executable = f"{action}({', '.join(parts)})"

    # Matched vs suggestion thresholds (you can tune)
    if confidence >= 35.0:
        status = "matched"
    elif confidence >= 20.0:
        status = "suggestion"
    else:
        status = "no_match"

    return {
        "status": status,
        "method": action,
        "parameters": args,
        "confidence": confidence,
        "executable": executable if status == "matched" else None,
        "explanation": "Compiled by deterministic parser",
        "meta": {
            "grammar": last.get("grammar"),
            "grammar_seq": last.get("grammar_seq"),
            "bindings_explained": last.get("bindings_explained"),
            "ranked": ranked,
        },
    }

def apply_followup(pending: dict, answer_text: str, module_path: str) -> Dict[str, Any]:
    """
    User answered a missing-argument question.
    pending = {"method": str, "missing": [..], "parameters": {...}}
    """
    _ensure_nltk()

    method = pending.get("method")
    missing = list(pending.get("missing") or [])
    params = dict(pending.get("parameters") or {})

    if not method or not missing:
        return {"status": "no_match", "explanation": "No pending clarification", "meta": {}}

    # fill the first missing param with user's answer
    param_name = missing.pop(0)
    value = answer_text.strip()
    params[param_name] = value

    domain = load_domain(module_path)
    required = (domain.get("ACTIONS", {}).get(method, {}) or {}).get("params", []) or []

    # still missing?
    still_missing = [p for p in required if (p not in params) or (params.get(p) in (None, "", []))]
    if still_missing:
        q = f"{method.replace('_', ' ')} what?"
        return {
            "status": "need_clarification",
            "method": method,
            "parameters": params,
            "confidence": 100.0,
            "question": q,
            "explanation": f"Missing required parameter(s): {still_missing}",
            "meta": {"missing": still_missing},
        }

    # Build executable: only include required params - freya fix
    parts = []
    if required:
        for p in required:
            parts.append(f"{p}={repr(params.get(p))}")
    executable = f"{method}({', '.join(parts)})"

    return {
        "status": "matched",
        "method": method,
        "parameters": params,
        "confidence": 100.0,
        "executable": executable,
        "explanation": "Filled missing argument from follow-up",
        "meta": {"filled": param_name},
    }
