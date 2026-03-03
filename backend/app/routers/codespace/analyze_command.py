import ast
import json
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Conversation
from app.models.schemas import AnalyzeCommandRequest

from app.parser_engine.api import compile_single, apply_followup
from app.parser_engine.lex_alz import analyze_sentence
from app.parser_engine.phase2_domain import load_domain, phase2_map_tokens
from app.parser_engine.cfg_parser import parse_command, extract_nodes_by_name, span_to_text

from app.routers.codespace.conversations import initialize_turtle_session, load_turtle_domain_code

router = APIRouter()

# Parser confidence thresholds (0-100 scale)
CONFIDENCE_THRESHOLD = 20.0
SUGGESTION_THRESHOLD = 35.0

CACHE_MAX_SIZE = 50
CACHE_TTL_SECONDS = 3600

# IMPORTANT: file is in backend/app/routers/codespace/
# parents[2] = backend/app
BASE_EXEC_DIR = Path(__file__).resolve().parents[2] / "executions"

def _maybe_set_active_from_assignment(session_dir: Path, executable: str | None) -> None:
    exe = (executable or "").strip()
    m = re.match(r"^([A-Za-z_]\w*)\s*=\s*turtle\.Turtle\(\)\s*$", exe)
    if not m:
        return
    st = _load_state(session_dir)
    st["active_object"] = m.group(1)
    st["pending"] = None
    _save_state(session_dir, st)
    
def _is_turtle_app(convo) -> bool:
    v = getattr(convo, "app_type", None)
    # Enum -> use .value if exists, else compare raw
    if hasattr(v, "value"):
        v = v.value
    return str(v).lower().endswith("turtle")  # works for "turtle" and "AppTypeEnum.turtle"

def _target_turtle_executable(executable: str, active: str | None) -> str:
    """
    Return a final python line for turtle playground:
      - assignment stays raw: t1 = turtle.Turtle()
      - already-targeted stays (t1.forward(...))
      - BUT if it is targeted to "t." then rewrite to active (t1.)
      - if plain call forward(...), prefix active -> t1.forward(...)
    """
    s = (executable or "").strip()
    if not s:
        return s

    # assignment stays raw: t1 = turtle.Turtle()
    if re.match(r"^[A-Za-z_]\w*\s*=", s):
        return s

    # already targeted: X.something(...)
    m = re.match(r"^([A-Za-z_]\w*)\.(.+)$", s)
    if m:
        target = m.group(1)
        rest = m.group(2)
        # IMPORTANT FIX: if backend/frontend produced "t.xxx(...)" rewrite to active turtle
        if target == "t" and active:
            return f"{active}.{rest}"
        return s

    # prefix with active if we have it
    if active:
        return f"{active}.{s}"

    return s

def _extract_init_params(module_path: Path, class_name: str) -> List[str]:
    """
    Return __init__ params excluding self, in order.
    If no __init__, return [].
    """
    try:
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
    except Exception:
        return []

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    return [a.arg for a in item.args.args if a.arg != "self"]
    return []


def _try_build_constructor_executable(command: str, class_name: str, init_params: List[str]) -> Optional[str]:
    """
    Detect create/make/init intent and produce:
      acc1 = ClassName(param="value")
    Heuristic:
      - var name from: 'call it X' | 'named X' | 'called X' | 'as X'
      - value from: after 'named' or 'for' (owner_name-like)
    """
    s = " ".join(command.strip().split())
    low = s.lower()

    # step 1: detect creation intent words
    if not re.search(r"\b(create|make|initialize|init|new|instantiate|build)\b", low):
        return None

    # step 2: get variable name
    var = None
    m = re.search(r"\bcall\s+it\s+([A-Za-z_]\w*)\b", low)
    if m: var = m.group(1)
    if not var:
        m = re.search(r"\bas\s+([A-Za-z_]\w*)\b", low)
        if m: var = m.group(1)
    if not var:
        m = re.search(r"\bnamed\s+([A-Za-z_]\w*)\b", low)
        if m: var = m.group(1)
    if not var:
        m = re.search(r"\bcalled\s+([A-Za-z_]\w*)\b", low)
        if m: var = m.group(1)

    # If no var name, we can't generate assignment (force user to provide)
    if not var:
        return None

    # step 3: pick constructor value (only if there is exactly 1 param)
    if len(init_params) == 1:
        p = init_params[0]

        # Try: "named Suriya" or "for Suriya"
        val = None
        m = re.search(r"\bnamed\s+([A-Za-z][\w\-]*)\b", s, flags=re.I)
        if m: val = m.group(1)
        if not val:
            m = re.search(r"\bfor\s+([A-Za-z][\w\-]*)\b", s, flags=re.I)
            if m: val = m.group(1)

        # If still no value, just construct with default
        if val:
            return f'{var} = {class_name}({p}="{val}")'
        return f"{var} = {class_name}()"

    # multi-param init: only allow if user provided none (use defaults) OR fail
    # (keep simple for now)
    return f"{var} = {class_name}()"

# ============================================================
# Cache
# ============================================================
class LRUCache:
    def __init__(self, max_size: int = 50, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache = OrderedDict()  # {key: (value, timestamp)}
        self.lock = threading.Lock()

    def get(self, key: str):
        with self.lock:
            if key not in self.cache:
                return None
            value, timestamp = self.cache[key]
            if time.time() - timestamp > self.ttl:
                del self.cache[key]
                return None
            self.cache.move_to_end(key)
            return value

    def set(self, key: str, value):
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = (value, time.time())
            while len(self.cache) > self.max_size:
                self.cache.popitem(last=False)

    def invalidate(self, key: str):
        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def stats(self):
        with self.lock:
            now = time.time()
            valid_items = sum(1 for _, ts in self.cache.values() if now - ts <= self.ttl)
            return {
                "size": len(self.cache),
                "valid_items": valid_items,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl,
            }


pipeline_cache = LRUCache(max_size=CACHE_MAX_SIZE, ttl_seconds=CACHE_TTL_SECONDS)


# ============================================================
# Session State (follow-up)
# ============================================================
def _state_path(session_dir: Path) -> Path:
    return session_dir / "state.json"

def _load_state(session_dir: Path) -> dict:
    p = _state_path(session_dir)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_state(session_dir: Path, state: dict) -> None:
    p = _state_path(session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ============================================================
# Runner (session runner)
# ============================================================
def _ensure_runner_exists(session_dir: Path, module_path: Path, class_name: str) -> Path:
    session_dir.mkdir(parents=True, exist_ok=True)
    runner_path = session_dir / "runner.py"

    if runner_path.exists():
        return runner_path

    state = _load_state(session_dir)

    # Default constructor args from state
    constructor_args = state.get("constructor_args", [])
    constructor_kwargs = state.get("constructor_kwargs", {})

    # Build constructor call dynamically
    args_str = ", ".join(
        [repr(a) for a in constructor_args] +
        [f"{k}={repr(v)}" for k, v in constructor_kwargs.items()]
    )

    module_name = module_path.stem

    runner_path.write_text(
        f"from {module_name} import {class_name}\n"
        f"import sys\n\n",
        encoding="utf-8"
    )
    return runner_path

def _append_to_runner(session_dir: Path, runner_path: Path, executable: str, comment: str | None = None) -> None:
    line = (executable or "").strip()
    if not line:
        return

    state = _load_state(session_dir)
    active = state.get("active_object")  # can be None (turtle before create)

    # IMPORTANT FIX: if somehow "t.xxx(...)" arrives, rewrite to active before writing
    if active and re.match(r"^t\.", line):
        line = f"{active}.{line[2:]}"

    with runner_path.open("a", encoding="utf-8") as f:
        if comment:
            f.write(f"# {comment.strip()}\n")

        # raw assignment: t1 = turtle.Turtle()
        if re.match(r"^[A-Za-z_]\w*\s*=", line):
            f.write(f"{line}\n")
            return

        # no active yet: allow explicit target calls only (t1.right(...))
        if not active:
            if re.match(r"^[A-Za-z_]\w*\.", line):
                f.write(f"{line}\n")
                return
            raise HTTPException(status_code=400, detail="No active turtle. Create one first (e.g., 'create turtle call t1').")

        # already prefixed
        if line.startswith(f"{active}."):
            f.write(f"{line}\n")
            return

        # normal call -> prefix active
        f.write(f"{active}.{line}\n")


# ============================================================
# Domain helpers (class/methods)
# ============================================================
def _extract_class_and_methods(py_text: str) -> Tuple[Optional[str], List[str]]:
    """
    Select the main domain class.
    Heuristic:
      - Choose class with the MOST non-dunder methods.
    """
    try:
        tree = ast.parse(py_text)
    except Exception:
        return None, []

    best_class = None
    best_methods = []
    max_method_count = -1

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if item.name.startswith("__") and item.name.endswith("__"):
                        continue
                    methods.append(item.name)

            if len(methods) > max_method_count:
                best_class = node.name
                best_methods = methods
                max_method_count = len(methods)

    return best_class, best_methods


# ============================================================
# CFG-based splitting
# ============================================================
def _filtered_tokens_for_cfg(lex_tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Must match RDParser filtering (punctuation/UNKNOWN removed).
    """
    return [t for t in lex_tokens if t.get("POS") not in ("punctuation")]

def _split_with_cfg(full_text: str, module_path: Path) -> List[str]:
    """
    CFG-based command splitting:
      'turn on tv then turn on light' -> ['turn on tv', 'turn on light']
    If CFG fails, returns [full_text].
    """
    lex_tokens = analyze_sentence(full_text)
    domain = load_domain(str(module_path))
    sem_tokens = phase2_map_tokens(lex_tokens, domain)

    g = parse_command(lex_tokens, sem_tokens)
    tree = g.get("parse_tree")
    if not tree:
        return [full_text.strip()]

    command_nodes = extract_nodes_by_name(tree, "Command")
    if not command_nodes:
        return [full_text.strip()]

    # keep UNKNOWN so names like t1 are preserved in the extracted command text
    toks_for_span = [t for t in lex_tokens if t.get("POS") != "punctuation"]

    out: List[str] = []
    for n in command_nodes:
        start = int(n.get("start", 0))
        end = int(n.get("end", 0))
        txt = span_to_text(toks_for_span, start, end)
        txt = " ".join(txt.split()).strip()
        if txt:
            out.append(txt)

    # remove duplicates, keep order
    seen = set()
    cleaned: List[str] = []
    for x in out:
        k = x.lower()
        if k not in seen:
            seen.add(k)
            cleaned.append(x)

    return cleaned if cleaned else [full_text.strip()]


# ============================================================
# Single command compilation to frontend schema
# ============================================================
def _process_single_command(command: str, module_path: Path) -> Dict[str, Any]:
    r = compile_single(command, str(module_path))

    status = r.get("status")
    confidence = float(r.get("confidence", 0.0))

    # Need clarification -> return no_match but with a suggestion_message
    if status == "need_clarification":
        method = r.get("method") or ""
        meta = r.get("meta") or {}
        missing = meta.get("missing", [])

        nice_question = None
        if missing:
            param = missing[0].replace("_", " ")
            method_nice = method.replace("_", " ")
            nice_question = f"What {param} would you like to specify for {method_nice}?"
        else:
            nice_question = r.get("question") or r.get("explanation")

        return {
            "success": False,
            "status": "no_match",
            "original_command": command,
            "suggestion_message": nice_question,
            "method": method,
            "parameters": r.get("parameters", {}) or {},
            "confidence": confidence,
            "executable": None,
            "intent_type": "parser",
            "source": "parser",
            "explanation": r.get("explanation"),
            "breakdown": r.get("meta"),
        }

    if status == "matched" and r.get("executable"):
        return {
            "success": True,
            "status": "matched",
            "original_command": command,
            "suggestion_message": None,
            "method": r.get("method"),
            "parameters": r.get("parameters", {}) or {},
            "confidence": confidence,
            "executable": r.get("executable"),
            "intent_type": "parser",
            "source": "parser",
            "explanation": r.get("explanation"),
            "breakdown": r.get("meta"),
        }

    if status == "suggestion":
        return {
            "success": True,
            "status": "suggestion",
            "original_command": command,
            "suggestion_message": r.get("suggestion_message") or f"Did you mean {r.get('method')}?",
            "method": r.get("method"),
            "parameters": r.get("parameters", {}) or {},
            "confidence": confidence,
            "executable": None,
            "intent_type": "parser",
            "source": "parser",
            "explanation": r.get("explanation"),
            "breakdown": r.get("meta"),
        }

    return {
        "success": False,
        "status": "no_match",
        "original_command": command,
        "suggestion_message": None,
        "method": None,
        "parameters": {},
        "confidence": confidence,
        "executable": None,
        "intent_type": "parser",
        "source": "parser",
        "explanation": r.get("explanation"),
        "breakdown": r.get("meta"),
    }


# ============================================================
# Routes
# ============================================================
@router.get("/pipeline_cache_stats")
def get_pipeline_cache_stats():
    return pipeline_cache.stats()


@router.post("/invalidate_pipeline_cache")
def invalidate_pipeline_cache(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    pipeline_cache.invalidate(f"conv_{payload.conversation_id}")
    return {"success": True, "message": "Cache invalidated"}


@router.post("/prewarm_pipeline")
def prewarm_pipeline(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    conversation_id = payload.conversation_id
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    session_dir = BASE_EXEC_DIR / f"session_{conversation_id}"
    module_path = session_dir / convo.file_name
    if not module_path.exists():
        if _is_turtle_app(convo):
            code = load_turtle_domain_code()
            initialize_turtle_session(conversation_id, code)
        else:
            raise HTTPException(status_code=400, detail=f"Session file not found: {module_path}")

    if not module_path.exists():
        raise HTTPException(status_code=400, detail=f"Session file not found: {module_path}")

    py_text = module_path.read_text(encoding="utf-8")
    class_name, method_names = _extract_class_and_methods(py_text)
    pipeline_cache.set(f"conv_{conversation_id}", {"class_name": class_name, "methods": method_names})
    return {"success": True, "message": "Pipeline prewarmed"}


@router.post("/analyze_command")
def analyze_command(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    conversation_id = payload.conversation_id
    command = (payload.command or "").strip()

    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    session_dir = BASE_EXEC_DIR / f"session_{conversation_id}"
    module_path = session_dir / convo.file_name
    if not module_path.exists():
        if _is_turtle_app(convo):
            code = load_turtle_domain_code()
            initialize_turtle_session(conversation_id, code)
        else:
            raise HTTPException(status_code=400, detail=f"Session file not found: {module_path}")

    if not module_path.exists():
        raise HTTPException(status_code=400, detail=f"Session file not found: {module_path}")

    cached = pipeline_cache.get(f"conv_{conversation_id}")
    if cached:
        class_name = cached.get("class_name")
    else:
        py_text = module_path.read_text(encoding="utf-8")
        class_name, method_names = _extract_class_and_methods(py_text)
        pipeline_cache.set(f"conv_{conversation_id}", {"class_name": class_name, "methods": method_names})

    if not class_name:
        raise HTTPException(status_code=400, detail="No class found in session file")

    # Ensure constructor config exists
    state = _load_state(session_dir)
    state.setdefault("active_object", None)
    state.setdefault("objects", {})
    state.setdefault("pending", None)
    state.setdefault("constructor_args", [])
    state.setdefault("constructor_kwargs", {})

    _save_state(session_dir, state)
    
    # constructor intent for NON-turtle apps
    if not _is_turtle_app(convo):
        init_params = _extract_init_params(module_path, class_name)
        exe = _try_build_constructor_executable(command, class_name, init_params)

        if exe:
            # update state (many objects)
            m = re.match(r"^([A-Za-z_]\w*)\s*=\s*", exe)
            if m:
                obj_name = m.group(1)
                state = _load_state(session_dir)
                state["active_object"] = obj_name
                state.setdefault("objects", {})
                state["objects"][obj_name] = {"class": class_name}
                state["pending"] = None
                _save_state(session_dir, state)

            formatted = {
                "success": True,
                "status": "matched",
                "original_command": command,
                "suggestion_message": None,
                "method": "__init__",
                "parameters": {},
                "confidence": 100.0,
                "executable": exe,          # <-- frontend will append this line
                "intent_type": "constructor",
                "source": "constructor",
                "explanation": "Constructor intent matched (create/make/init).",
                "breakdown": {"init_params": init_params},
            }
            
            runner_path = _ensure_runner_exists(session_dir, module_path, class_name)
            _append_to_runner(session_dir, runner_path, exe, formatted.get("original_command"))

            return {
                "success": True,
                "class_name": class_name,
                "file_name": convo.file_name,
                "command_count": 1,
                "result": formatted,
                "results": [formatted],
            }

    pending = state.get("pending")

    # ------------------------------------------------------------
    # Follow-up flow
    # ------------------------------------------------------------
    if pending:
        r = apply_followup(pending, command, str(module_path))

        # update pending state
        if r.get("status") == "matched":
            state["pending"] = None
        elif r.get("status") == "need_clarification":
            state["pending"] = {
                "method": r.get("method"),
                "missing": (r.get("meta") or {}).get("missing", []),
                "parameters": r.get("parameters", {}) or {},
            }
        else:
            state["pending"] = None

        _save_state(session_dir, state)

        # format result
        if r.get("status") == "matched":
            formatted = {
                "success": True,
                "status": "matched",
                "original_command": command,
                "suggestion_message": None,
                "method": r.get("method"),
                "parameters": r.get("parameters", {}) or {},
                "confidence": float(r.get("confidence", 0.0)),
                "executable": r.get("executable"),
                "intent_type": "parser",
                "source": "parser",
                "explanation": r.get("explanation"),
                "breakdown": r.get("meta"),
            }
        elif r.get("status") == "need_clarification":
            formatted = {
                "success": False,
                "status": "no_match",
                "original_command": command,
                "suggestion_message": r.get("question") or r.get("explanation"),
                "method": r.get("method"),
                "parameters": r.get("parameters", {}) or {},
                "confidence": float(r.get("confidence", 0.0)),
                "executable": None,
                "intent_type": "parser",
                "source": "parser",
                "explanation": r.get("explanation"),
                "breakdown": r.get("meta"),
            }
        else:
            formatted = {
                "success": False,
                "status": "no_match",
                "original_command": command,
                "suggestion_message": None,
                "method": None,
                "parameters": {},
                "confidence": float(r.get("confidence", 0.0)),
                "executable": None,
                "intent_type": "parser",
                "source": "parser",
                "explanation": r.get("explanation"),
                "breakdown": r.get("meta"),
            }
            
        # IMPORTANT: if this creates a turtle, set active_object immediately
        _maybe_set_active_from_assignment(session_dir, formatted.get("executable"))

        # Turtle: if followup created a turtle, set active BEFORE targeting
        if _is_turtle_app(convo) and formatted.get("executable"):
            exe = (formatted.get("executable") or "").strip()
            m = re.match(r"^([A-Za-z_]\w*)\s*=\s*turtle\.Turtle\(\)\s*$", exe)
            if m:
                st = _load_state(session_dir)
                st["active_object"] = m.group(1)
                st["pending"] = None
                _save_state(session_dir, st)

            st = _load_state(session_dir)
            formatted["executable"] = _target_turtle_executable(formatted["executable"], st.get("active_object"))

        # append to runner if matched
        if formatted.get("status") == "matched" and formatted.get("executable"):
            runner_path = _ensure_runner_exists(session_dir, module_path, class_name)
            _append_to_runner(session_dir, runner_path, formatted["executable"], formatted.get("original_command"))

        return {
            "success": True,
            "class_name": class_name,
            "file_name": convo.file_name,
            "command_count": 1,
            "result": formatted,
            "results": [formatted],
        }

    # ------------------------------------------------------------
    # Normal flow
    # ------------------------------------------------------------
    if _is_turtle_app(convo):
        command_parts = [command]   # keep raw text so t1 isn't lost
    else:
        command_parts = _split_with_cfg(command, module_path)

    print("command_parts:", command_parts)
    print("[DEBUG] convo.app_type =", getattr(convo, "app_type", None))

    results: List[Dict[str, Any]] = []
    for part in command_parts:
        part = (part or "").strip()
        if not part:
            continue
        results.append(_process_single_command(part, module_path))
        print("[DEBUG] raw executables =", [r.get("executable") for r in results])
        
    # IMPORTANT: if any command created a turtle, set active_object immediately
    for rr in results:
        _maybe_set_active_from_assignment(session_dir, rr.get("executable"))
        
    # Turtle: rewrite executables to active turtle (backend sends final line)
    if _is_turtle_app(convo):
        st = _load_state(session_dir)
        active = st.get("active_object")
        print("[DEBUG] active_object at targeting =", active)

        for rr in results:
            exe_before = rr.get("executable")
            if exe_before:
                exe_after = _target_turtle_executable(exe_before, active)
                rr["executable"] = exe_after
                print("[DEBUG] target:", exe_before, "=>", exe_after)

    # append matched results to runner
    runner_path = _ensure_runner_exists(session_dir, module_path, class_name)
    for rr in results:
        if rr.get("status") == "matched" and rr.get("executable"):
            _append_to_runner(session_dir, runner_path, rr["executable"], rr.get("original_command"))

    # store pending follow-up if needed
    for rr in results:
        if rr.get("suggestion_message") and rr.get("method"):
            state = _load_state(session_dir)
            state["pending"] = {
                "method": rr.get("method"),
                "missing": ((rr.get("breakdown") or {}).get("missing")) or ["unknown"],
                "parameters": rr.get("parameters", {}) or {},
            }
            _save_state(session_dir, state)
            break

    primary = results[0] if results else {
        "success": False,
        "status": "no_match",
        "original_command": command,
        "suggestion_message": None,
        "method": None,
        "parameters": {},
        "confidence": 0.0,
        "executable": None,
        "intent_type": "parser",
        "source": "parser",
        "explanation": "No results",
        "breakdown": {},
    }

    return {
        "success": True,
        "class_name": class_name,
        "file_name": convo.file_name,
        "command_count": len(command_parts),
        "result": primary,
        "results": results,
    }