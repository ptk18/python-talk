# backend/app/parser_engine/api.py
from __future__ import annotations

from typing import Any, Dict, Optional
import threading

from app.parser_engine.lex_alz import setup_nltk
from app.parser_engine.phase2_domain import load_domain
from app.parser_engine import main_process

import re
import turtle
from typing import Any, Dict, Optional, List

_nltk_lock = threading.Lock()
_nltk_ready = False

def _extract_name_after_markers(text: str) -> Optional[str]:
    # supports: called t1 / called "t1" / called 't1' / called t1.
    m = re.search(
        r"\b(?:called|call|named|name|calls|names)\s+['\"\(\[]*([A-Za-z_]\w*)",
        text,
        flags=re.IGNORECASE
    )
    return m.group(1) if m else None

def _looks_like_turtle_create(text: str) -> bool:
    s = text.lower()
    return ("turtle" in s) and any(w in s for w in ["create", "make", "init", "initialize", "spawn", "new"])

def _first_number(text: str) -> Optional[int]:
    # match only standalone numbers, not digits inside identifiers like t1 or acc2
    m = re.search(r"(?<![A-Za-z_])(-?\d+)(?![A-Za-z_])", text)
    return int(m.group(1)) if m else None


def _ensure_nltk():
    global _nltk_ready
    if _nltk_ready:
        return
    with _nltk_lock:
        if not _nltk_ready:
            setup_nltk()
            _nltk_ready = True
            
def _build_constructor_executable(object_name: str, class_name: str, constructor_args: Dict[str, Any]) -> str:
    if not constructor_args:
        return f"{object_name} = {class_name}()"

    parts = []
    for k, v in constructor_args.items():
        if isinstance(v, str):
            parts.append(f'{k}="{v}"')
        else:
            parts.append(f"{k}={v}")

    return f"{object_name} = {class_name}({', '.join(parts)})"

def compile_single(command_text: str, module_path: str) -> Dict[str, Any]:
    """
    Deterministic compile (no AI model):
      NL command -> (lex -> domain -> grammar -> code)

    Returns dict used by analyze_command.py.
    """
    _ensure_nltk()
    command_text = (command_text or "").strip()

    # remove only trailing sentence period
    # "top." -> "top"
    # "move to x 10 y 15." -> "move to x 10 y 15"
    # keeps decimals like 3.14 inside text untouched
    if command_text.endswith("."):
        command_text = command_text[:-1].strip()

    # ---- HARDCASE: turtle creation -> emit assignment line (no file read) ----
    # This runs BEFORE load_domain/main_process, so turtle creation follows preset rules only.
    if _looks_like_turtle_create(command_text):
        name = _extract_name_after_markers(command_text)
        if name:
            executable = f"{name} = turtle.Turtle()"
            return {
                "status": "matched",
                "method": "create_turtle",
                "parameters": {"name": name},
                "confidence": 100.0,
                "executable": executable,
                "explanation": "Hardcoded turtle creation",
                "meta": {"hardcode": "turtle_create_assignment"},
            }
        else:
            return {
                "status": "need_clarification",
                "method": "create_turtle",
                "parameters": {},
                "confidence": 100.0,
                "question": "What should I name the turtle? (e.g., 'call t1')",
                "explanation": "Missing turtle name for creation",
                "meta": {"missing": ["name"], "hardcode": "turtle_create_missing_name"},
            }

    domain = load_domain(module_path)
    
    print("\n[DEBUG] phrases per action:")
    for a, info in domain["ACTIONS"].items():
        print(a, "=>", info.get("phrases"))
    print()

    out = main_process.run(command_text, module_path)
    if not out:
        return {"status": "no_match", "explanation": "Empty parser output", "meta": {}}

    print("\n========== PARSER DEBUG ==========")
    print("User input:", command_text)
    print("Raw parser output:", out)

    last = out[-1] if isinstance(out, list) else out
    # Extract POS tokens (all items except the last result dict)
    pos_tokens = [t for t in (out[:-1] if isinstance(out, list) else [])
                  if isinstance(t, dict) and "word" in t]
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
            "meta": {"ranked": ranked, "pos_tokens": pos_tokens},
        }

    print("Selected action:", action)
    print("Args:", args)
    print("Ranked similarity:", ranked[:3])  # top 3
    print("==================================\n")

    # required params from domain
    required = (domain.get("ACTIONS", {}).get(action, {}) or {}).get("params", []) or []

    # ---- number binding (1 required param) ----
    # Only bind number to param if it's an int-like param, not a string param like colour
    STR_PARAM_HINTS = {"colour", "color", "name", "note", "category", "recipient", "owner", "owner_name", "target", "device", "room"}
    n = _first_number(command_text)
    if n is not None and len(required) == 1:
        p = required[0]
        if p.lower() not in STR_PARAM_HINTS:
            v = args.get(p)
            if v in (None, "", []) or isinstance(v, str):
                args[p] = n

    # ---- missing required params ----
    missing = [p for p in required if (p not in args) or (args.get(p) in (None, "", []))]

    if missing:
        q = f"Missing {missing} for {action}"
        return {
            "status": "need_clarification",
            "method": action,
            "parameters": args,
            "confidence": confidence,
            "question": q,
            "explanation": f"Missing required parameter(s): {missing}",
            "meta": {"missing": missing, "ranked": ranked, "pos_tokens": pos_tokens},
        }

    # ---- build executable (only required params) ----
    parts: List[str] = []
    for p in required:
        v = args.get(p)
        if isinstance(v, str):
            parts.append(repr(v))
        else:
            parts.append(str(v))
    executable = f"{action}({', '.join(parts)})"

    # thresholds
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
            "pos_tokens": pos_tokens,
        },
    }

def apply_followup(pending: dict, answer_text: str, module_path: str) -> Dict[str, Any]:
    """
    User answered a missing-argument question.
    pending = {"method": str, "missing": [..], "parameters": {...}}

    For turtle create follow-up, we do NOT read domain/module file.
    We only apply preset rules.
    """
    _ensure_nltk()
    
    # -------------------------
    # CLEAN PUNCTUATION
    # -------------------------
    # if answer_text:
    #     answer_text = answer_text.strip()
    #     answer_text = re.sub(r"[^\w\s\-\.]", "", answer_text)   # remove punctuation except dot/space/hyphen
    #     answer_text = answer_text.strip()
    
    answer_text = (answer_text or "").strip()
    if answer_text.endswith("."):
        answer_text = answer_text[:-1].strip()

    method = (pending or {}).get("method")
    missing = list((pending or {}).get("missing") or [])
    params = dict((pending or {}).get("parameters") or {})

    # -------------------------
    # DEBUG PRINTS (always)
    # -------------------------
    print("\n========== FOLLOWUP DEBUG ==========")
    print("pending:", pending)
    print("answer_text:", repr(answer_text))
    print("method:", method)
    print("missing:", missing)
    print("params(before):", params)

    if not method or not missing:
        print("FOLLOWUP: no pending clarification")
        print("===================================\n")
        return {"status": "no_match", "explanation": "No pending clarification", "meta": {}}

    # fill the first missing param with user's answer
    param_name = missing.pop(0)
    raw = (answer_text or "").strip()

    # Try extract name from markers first (works for "create turtle called t1")
    extracted = _extract_name_after_markers(raw)

    # If no markers, accept single-token identifier (works for "t1")
    if not extracted:
        m = re.match(r"^\s*([A-Za-z_]\w*)\s*$", raw)
        extracted = m.group(1) if m else None

    print("param_name:", param_name)
    print("raw:", repr(raw))
    print("extracted:", extracted)

    # -------------------------
    # TURTLE: create_turtle follow-up (preset rules only)
    # -------------------------
    if method == "create_turtle" and param_name == "name":
        name = (extracted or "").strip()

        # Validate python identifier
        if not re.match(r"^[A-Za-z_]\w*$", name):
            print("FOLLOWUP: invalid turtle name:", repr(name))
            print("===================================\n")
            return {
                "status": "need_clarification",
                "method": method,
                "parameters": params,
                "confidence": 100.0,
                "question": "Give a valid name like t1, turtle1, my_turtle.",
                "explanation": "Invalid turtle name (must be a Python identifier)",
                "meta": {"missing": ["name"], "invalid": raw, "extracted": extracted},
            }

        params["name"] = name
        executable = f"{name} = turtle.Turtle()"

        print("FOLLOWUP: turtle assignment executable:", executable)
        print("params(after):", params)
        print("===================================\n")

        return {
            "status": "matched",
            "method": method,
            "parameters": {"name": name},
            "confidence": 100.0,
            "executable": executable,
            "explanation": "Filled turtle name from follow-up (hardcoded assignment)",
            "meta": {"filled": "name", "hardcode": "turtle_create_assignment_followup"},
        }
        
    # -------------------------
    # CONSTRUCTOR follow-up
    # -------------------------
    if method == "__init__":
        class_name = pending.get("class_name")
        object_name = params.get("object_name")

        if param_name == "object_name":
            if not re.match(r"^[A-Za-z_]\w*$", raw):
                return {
                    "status": "need_clarification",
                    "method": "__init__",
                    "parameters": params,
                    "confidence": 100.0,
                    "question": "Give a valid object name like acc1, home, or my_account.",
                    "explanation": "Invalid object name.",
                    "meta": {"missing": ["object_name"], "class_name": class_name},
                }
            params["object_name"] = raw
        else:
            if raw.isdigit() or (raw.startswith("-") and raw[1:].isdigit()):
                params[param_name] = int(raw)
            else:
                params[param_name] = raw

        still_missing = [p for p in missing if p not in params or params[p] in (None, "", [])]
        if still_missing:
            first_missing = still_missing[0].replace("_", " ")
            return {
                "status": "need_clarification",
                "method": "__init__",
                "parameters": params,
                "confidence": 100.0,
                "question": f"What is the {first_missing} for this {class_name} object?",
                "explanation": f"Missing constructor parameter(s): {still_missing}",
                "meta": {"missing": still_missing, "class_name": class_name},
            }

        object_name = params.pop("object_name")
        executable = _build_constructor_executable(object_name, class_name, params)
        
        print("CONSTRUCTOR FOLLOWUP class_name:", class_name)
        print("CONSTRUCTOR FOLLOWUP params(after bind):", params)
        print("CONSTRUCTOR FOLLOWUP still_missing:", still_missing)
        
        print("CONSTRUCTOR FOLLOWUP: executable:", executable)
        print("params(after):", params)
        print("===================================\n")
        

        return {
            "status": "matched",
            "method": "__init__",
            "parameters": params,
            "confidence": 100.0,
            "executable": executable,
            "explanation": "Filled missing constructor argument from follow-up",
            "meta": {"filled": param_name, "class_name": class_name, "object_name": object_name},
        }

    # -------------------------
    # GENERAL (non-turtle) follow-up:
    # keep your existing behavior (domain-based)
    # -------------------------
    # support answers like:
    # "10"
    # "y 15"
    # "x 10"
    # "x = 10"
    # "y = 15"

    target_param = param_name
    value: Any = raw

    named_match = re.match(r"^\s*([A-Za-z_]\w*)\s*(?:=\s*)?(-?\d+)\s*$", raw)
    if named_match:
        typed_param = named_match.group(1)
        typed_value = int(named_match.group(2))

        # only accept if user named one of the still-missing/required params
        domain = load_domain(module_path)
        required = (domain.get("ACTIONS", {}).get(method, {}) or {}).get("params", []) or []

        if typed_param in required:
            target_param = typed_param
            value = typed_value
        else:
            value = raw
    else:
        m = re.search(r"-?\d+", raw)
        if m:
            value = int(m.group(0))
        else:
            value = raw

        if extracted:
            value = extracted

    params[target_param] = value

    print("GENERAL FOLLOWUP: params(after bind):", params)

    domain = load_domain(module_path)
    required = (domain.get("ACTIONS", {}).get(method, {}) or {}).get("params", []) or []

    still_missing = [p for p in required if (p not in params) or (params.get(p) in (None, "", []))]
    if still_missing:
        print("GENERAL FOLLOWUP: still_missing:", still_missing)
        print("===================================\n")
        return {
            "status": "need_clarification",
            "method": method,
            "parameters": params,
            "confidence": 100.0,
            "question": f"Missing {still_missing}",
            "explanation": f"Missing required parameter(s): {still_missing}",
            "meta": {"missing": still_missing},
        }

    parts: List[str] = []
    for p in required:
        v = params.get(p)
        if isinstance(v, str):
            parts.append(repr(v))
        else:
            parts.append(str(v))
    executable = f"{method}({', '.join(parts)})"

    print("GENERAL FOLLOWUP: executable:", executable)
    print("===================================\n")

    return {
        "status": "matched",
        "method": method,
        "parameters": params,
        "confidence": 100.0,
        "executable": executable,
        "explanation": "Filled missing argument from follow-up",
        "meta": {"filled": param_name},
    }