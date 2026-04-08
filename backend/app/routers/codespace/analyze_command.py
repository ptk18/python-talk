# backend/app/routers/codespace/analyze_command.py
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
from app.models.schemas import AnalyzeCommandRequest, UndoRequest

from app.parser_engine.api import compile_single, apply_followup
from app.parser_engine.lex_alz import analyze_sentence
from app.parser_engine.phase2_domain import load_domain, phase2_map_tokens, DOMAIN_CACHE
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

    obj_name = m.group(1)

    st = _load_state(session_dir)
    st.setdefault("objects", {})
    st["objects"][obj_name] = {
        "class": "Turtle",
        "constructor_args": [],
        "constructor_kwargs": {}
    }
    st["active_object"] = obj_name
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
      - if targeted to "t." rewrite to active
      - screen-level turtle calls stay global: bgcolor(...), title(...), ...
      - plain turtle movement/drawing calls prefix active -> t1.forward(...)
    """
    s = (executable or "").strip()
    if not s:
        return s

    # assignment stays raw
    if re.match(r"^[A-Za-z_]\w*\s*=", s):
        return s

    # screen-level call stays global
    if _is_turtle_screen_method_call(s):
        return s

    # already targeted: X.something(...)
    m = re.match(r"^([A-Za-z_]\w*)\.(.+)$", s)
    if m:
        target = m.group(1)
        rest = m.group(2)

        if target == "t" and active:
            return f"{active}.{rest}"
        return s

    # plain call like forward(...), write(...), color(...)
    if active:
        return f"{active}.{s}"

    return s

def _is_turtle_screen_method_call(executable: str) -> bool:
    """
    These are turtle-module / screen-level calls in turtle mode.
    They should NOT be prefixed with active turtle object.
    """
    s = (executable or "").strip()
    if not s:
        return False

    screen_methods = {
        "bgcolor",
        "title",
        "setup",
        "screensize",
        "clearscreen",
        "resetscreen",
    }

    m = re.match(r"^([A-Za-z_]\w*)\s*\(", s)
    if not m:
        return False

    method_name = m.group(1)
    return method_name in screen_methods

def _extract_init_info(module_path: Path, class_name: str) -> Dict[str, Any]:
    """
    Return constructor info for class_name:
    {
        "params": [...],          # excluding self
        "required": [...],        # params without defaults
        "defaults": {...}         # param -> default value if simple literal
    }
    """
    try:
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
    except Exception:
        return {"params": [], "required": [], "defaults": {}}

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                    args = item.args.args[1:]  # skip self
                    param_names = [a.arg for a in args]

                    defaults = item.args.defaults or []
                    num_required = len(param_names) - len(defaults)

                    required = param_names[:num_required]
                    default_map = {}

                    for param, default_node in zip(param_names[num_required:], defaults):
                        try:
                            default_map[param] = ast.literal_eval(default_node)
                        except Exception:
                            pass

                    return {
                        "params": param_names,
                        "required": required,
                        "defaults": default_map,
                    }

    return {"params": [], "required": [], "defaults": {}}


def _extract_object_name(command: str) -> Optional[str]:
    s = command.strip()

    patterns = [
        r"\bcall\s+it\s+([A-Za-z_]\w*)\b",
        r"\bnamed\s+([A-Za-z_]\w*)\b",
        r"\bcalled\s+([A-Za-z_]\w*)\b",
        r"\bas\s+([A-Za-z_]\w*)\b",
    ]

    for pat in patterns:
        m = re.search(pat, s, flags=re.IGNORECASE)
        if m:
            return m.group(1)

    return None

def _extract_constructor_args(command: str, init_params: List[str], object_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Very simple rule-based binding for constructor params.

    Supports examples like:
    - create bank account named acc1 for top with balance 1000
    - create bank account called acc1 with owner preme and balance 500
    """
    s = " ".join(command.strip().split())
    low = s.lower()

    args: Dict[str, Any] = {}

    def first_number_after(keyword: str) -> Optional[int]:
        m = re.search(rf"\b{re.escape(keyword)}\s+(-?\d+)\b", s, flags=re.IGNORECASE)
        return int(m.group(1)) if m else None

    def first_word_after(keyword: str) -> Optional[str]:
        m = re.search(rf"\b{re.escape(keyword)}\s+([A-Za-z_]\w*)\b", s, flags=re.IGNORECASE)
        return m.group(1) if m else None

    for p in init_params:
        pl = p.lower()

        # numeric-like params
        if pl in {"balance", "amount", "temperature", "age", "count", "limit"}:
            n = first_number_after(pl)
            if n is not None:
                args[p] = n
                continue

        # owner/name-like params
        if pl in {"owner", "owner_name", "user", "username"}:
            v = first_word_after("owner")
            if v:
                args[p] = v
                continue

            v = first_word_after("for")
            if v and v != object_name:
                args[p] = v
                continue

        if pl == "name":
            v = first_word_after("name")
            if v:
                args[p] = v
                continue

        # direct pattern: "<param> value"
        m = re.search(rf"\b{re.escape(pl)}\s+([A-Za-z_]\w*|-?\d+)\b", s, flags=re.IGNORECASE)
        if m:
            raw = m.group(1)
            if re.fullmatch(r"-?\d+", raw):
                args[p] = int(raw)
            else:
                args[p] = raw

    return args

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

def _try_build_constructor_executable(command: str, class_name: str, init_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns:
    {
        "matched": bool,
        "object_name": str | None,
        "args": {...},
        "missing": [...],
        "executable": str | None
    }
    """
    s = " ".join(command.strip().split())
    low = s.lower()

    if not re.search(r"\b(create|make|initialize|init|new|instantiate|build|open|start)\b", low):
        return {
            "matched": False,
            "object_name": None,
            "args": {},
            "missing": [],
            "executable": None,
        }

    params = init_info.get("params", [])
    required = init_info.get("required", [])

    object_name = _extract_object_name(s)
    bound_args = _extract_constructor_args(s, params, object_name)

    missing = []

    if not object_name:
        missing.append("object_name")

    for p in required:
        if p not in bound_args:
            missing.append(p)

    if missing:
        return {
            "matched": True,
            "object_name": object_name,
            "args": bound_args,
            "missing": missing,
            "executable": None,
        }

    executable = _build_constructor_executable(object_name, class_name, bound_args)

    return {
        "matched": True,
        "object_name": object_name,
        "args": bound_args,
        "missing": [],
        "executable": executable,
    }
    
def _extract_switch_object_name(command: str) -> Optional[str]:
    s = (command or "").strip()

    patterns = [
        r"^\s*change\s+object\s+to\s+([A-Za-z_]\w*)\s*\.?\s*$",
        r"^\s*switch\s+object\s+to\s+([A-Za-z_]\w*)\s*\.?\s*$",
        r"^\s*set\s+active\s+object\s+to\s+([A-Za-z_]\w*)\s*\.?\s*$",
        r"^\s*use\s+object\s+([A-Za-z_]\w*)\s*\.?\s*$",
        r"^\s*use\s+([A-Za-z_]\w*)\s*\.?\s*$",
        r"^\s*select\s+object\s+([A-Za-z_]\w*)\s*\.?\s*$",
    ]

    for pat in patterns:
        m = re.match(pat, s, flags=re.IGNORECASE)
        if m:
            return m.group(1)

    return None

def _extract_referenced_object(command: str, known_objects: Dict[str, Any]) -> Optional[str]:
    s = (command or "").strip().rstrip(".").lower()
    if not s or not known_objects:
        return None

    for obj_name in known_objects.keys():
        if re.search(rf"\b{re.escape(obj_name.lower())}\b", s):
            return obj_name

    return None
   
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
# Undo History (truncate runner by bytes + restore state.json)
# ============================================================
def _history_dir(session_dir: Path) -> Path:
    return session_dir / ".history"


def _next_step_id(history_dir: Path) -> int:
    if not history_dir.exists():
        return 1
    files = sorted([p for p in history_dir.glob("*.json") if p.is_file()])
    if not files:
        return 1
    # filenames like 000001.json
    last = files[-1].stem
    try:
        return int(last) + 1
    except Exception:
        return len(files) + 1


def _write_undo_snapshot(
    conversation_id: int,
    session_dir: Path,
    command: str,
    app_type: str | None,
) -> dict:
    session_dir.mkdir(parents=True, exist_ok=True)
    hdir = _history_dir(session_dir)
    hdir.mkdir(parents=True, exist_ok=True)

    runner_path = session_dir / "runner.py"
    prev_size = runner_path.stat().st_size if runner_path.exists() else 0

    prev_state = _load_state(session_dir)  # snapshot BEFORE changes

    step_id = _next_step_id(hdir)
    rec = {
        "step_id": step_id,
        "conversation_id": conversation_id,
        "runner_prev_size_bytes": prev_size,
        "state_prev": prev_state,
        "command": command,
        "app_type": app_type,
    }
    (hdir / f"{step_id:06d}.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return rec


def _pop_last_undo_snapshot(session_dir: Path) -> dict | None:
    hdir = _history_dir(session_dir)
    if not hdir.exists():
        return None
    files = sorted([p for p in hdir.glob("*.json") if p.is_file()])
    if not files:
        return None
    last_path = files[-1]
    try:
        rec = json.loads(last_path.read_text(encoding="utf-8"))
    except Exception:
        rec = None
    # delete snapshot file (no redo for now)
    try:
        last_path.unlink()
    except Exception:
        pass
    return rec


# ============================================================
# Runner (session runner)
# ============================================================
def _is_value_returning_turtle_call(executable: str) -> bool:
    s = (executable or "").strip()
    if not s:
        return False

    value_methods = {
        "heading",
        "position",
        "pos",
        "xcor",
        "ycor",
        "isdown",
        "isvisible",
        "distance",
        "towards",
    }

    # targeted call: t1.heading(...)
    m1 = re.match(r"^[A-Za-z_]\w*\.(\w+)\s*\(", s)
    if m1 and m1.group(1) in value_methods:
        return True

    # plain call: heading(...)
    m2 = re.match(r"^(\w+)\s*\(", s)
    if m2 and m2.group(1) in value_methods:
        return True

    return False

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
    active = state.get("active_object")

    with runner_path.open("a", encoding="utf-8") as f:
        if comment:
            f.write(f"# {comment.strip()}\n")

        # raw assignment stays raw
        if re.match(r"^[A-Za-z_]\w*\s*=", line):
            f.write(f"{line}\n")
            return

        # screen-level turtle call stays global
        if _is_turtle_screen_method_call(line):
            f.write(f"{line}\n")
            return

        # already targeted like acc1.deposit(...) or t1.forward(...)
        if re.match(r"^[A-Za-z_]\w*\.", line):
            if _is_value_returning_turtle_call(line):
                f.write(f"print({line})\n")
            else:
                f.write(f"{line}\n")
            return

        # plain call like write(...), forward(...), color(...)
        if active:
            final_line = f"{active}.{line}"
            if _is_value_returning_turtle_call(final_line):
                f.write(f"print({final_line})\n")
            else:
                f.write(f"{final_line}\n")
            return

        raise HTTPException(status_code=400, detail="No active object. Create an object first.")
    

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

_COMPOUND_SEP = re.compile(
    r'\b(?:and\s+then|and\s+also|and|then|next|afterwards?|after\s+that)\b',
    re.IGNORECASE,
)

def _split_compound_simple(full_text: str) -> List[str]:
    """
    Simple regex-based compound command splitting for turtle apps.
    'turn left 90 and move forward 50' -> ['turn left 90', 'move forward 50']
    """
    parts = _COMPOUND_SEP.split(full_text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts if parts else [full_text.strip()]


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

    # Also invalidate domain cache for this conversation's file
    convo = db.query(Conversation).filter(Conversation.id == payload.conversation_id).first()
    if convo:
        session_dir = BASE_EXEC_DIR / f"session_{payload.conversation_id}"
        module_path = session_dir / convo.file_name
        abs_path = str(module_path.resolve())
        DOMAIN_CACHE.pop(abs_path, None)

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

    # Also warm the domain cache (AST + synonym expansion) to avoid cold-start on first command
    try:
        load_domain(str(module_path))
        print(f"[prewarm] Domain cache warmed for conv_{conversation_id}")
    except Exception as e:
        print(f"[prewarm] Domain cache warm failed: {e}")

    return {"success": True, "message": "Pipeline prewarmed"}


@router.post("/undo_last")
def undo_last(payload: UndoRequest, db: Session = Depends(get_db)):
    conversation_id = payload.conversation_id

    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    session_dir = BASE_EXEC_DIR / f"session_{conversation_id}"
    runner_path = session_dir / "runner.py"
    state_path = session_dir / "state.json"

    rec = _pop_last_undo_snapshot(session_dir)
    if not rec:
        return {"success": False, "message": "Nothing to undo"}

    prev_size = int(rec.get("runner_prev_size_bytes", 0))
    prev_state = rec.get("state_prev", {})

    if not runner_path.exists():
        # If prev_size is 0 and runner missing, ok. Otherwise corruption.
        if prev_size != 0:
            raise HTTPException(
                status_code=500,
                detail="runner.py missing but undo expects non-zero size",
            )
    else:
        cur_size = runner_path.stat().st_size
        if prev_size > cur_size:
            raise HTTPException(
                status_code=500,
                detail="Undo snapshot size is larger than current runner.py size",
            )
        # truncate by bytes
        with runner_path.open("r+b") as f:
            f.truncate(prev_size)

    # restore state.json
    session_dir.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(prev_state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "success": True,
        "message": f"Undid step {rec.get('step_id')}",
        "undone_step": rec.get("step_id"),
    }


@router.post("/analyze_command")
def analyze_command(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    t_total_start = time.time()
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
    
    # ------------------------------------------------------------
    # Universal object switch command
    # ------------------------------------------------------------
    switch_name = _extract_switch_object_name(command)
    if switch_name:
        known_objects = state.get("objects", {}) or {}

        real_name = None
        for obj_name in known_objects.keys():
            if obj_name.lower() == switch_name.lower():
                real_name = obj_name
                break

        if not real_name:
            return {
                "success": True,
                "class_name": class_name,
                "file_name": convo.file_name,
                "command_count": 1,
                "result": {
                    "success": False,
                    "status": "no_match",
                    "original_command": command,
                    "suggestion_message": f'No object named "{switch_name}" exists.',
                    "method": None,
                    "parameters": {},
                    "confidence": 100.0,
                    "executable": None,
                    "intent_type": "session_control",
                    "source": "state",
                    "explanation": "Requested object does not exist in session state.",
                    "breakdown": {"known_objects": list(known_objects.keys())},
                },
                "results": [{
                    "success": False,
                    "status": "no_match",
                    "original_command": command,
                    "suggestion_message": f'No object named "{switch_name}" exists.',
                    "method": None,
                    "parameters": {},
                    "confidence": 100.0,
                    "executable": None,
                    "intent_type": "session_control",
                    "source": "state",
                    "explanation": "Requested object does not exist in session state.",
                    "breakdown": {"known_objects": list(known_objects.keys())},
                }],
            }

        state["active_object"] = real_name
        state["pending"] = None
        _save_state(session_dir, state)

        formatted = {
            "success": True,
            "status": "matched",
            "original_command": command,
            "suggestion_message": None,
            "method": "__set_active_object__",
            "parameters": {"object_name": real_name},
            "confidence": 100.0,
            "executable": None,
            "intent_type": "session_control",
            "source": "state",
            "explanation": f'Active object changed to "{real_name}".',
            "breakdown": {"active_object": real_name},
        }

        return {
            "success": True,
            "class_name": class_name,
            "file_name": convo.file_name,
            "command_count": 1,
            "result": formatted,
            "results": [formatted],
        }

    # ------------------------------------------------------------
    # Undo snapshot: record at most once per request
    # ------------------------------------------------------------
    undo_recorded = False

    def _record_undo_once():
        nonlocal undo_recorded
        if undo_recorded:
            return
        v = getattr(convo, "app_type", None)
        if hasattr(v, "value"):
            v = v.value
        _write_undo_snapshot(
            conversation_id,
            session_dir,
            command,
            str(v) if v else None,
        )
        undo_recorded = True

    # constructor intent for NON-turtle apps
    if not _is_turtle_app(convo):
        init_info = _extract_init_info(module_path, class_name)
        constructor_result = _try_build_constructor_executable(command, class_name, init_info)

        if constructor_result.get("matched"):
            missing = constructor_result.get("missing", [])
            object_name = constructor_result.get("object_name")
            bound_args = constructor_result.get("args", {})
            exe = constructor_result.get("executable")

            # missing object variable name (and maybe other constructor params too)
            if "object_name" in missing:
                state = _load_state(session_dir)
                state["pending"] = {
                    "method": "__init__",
                    "missing": missing,
                    "parameters": bound_args,
                    "class_name": class_name,
                }
                _save_state(session_dir, state)

                formatted = {
                    "success": False,
                    "status": "no_match",
                    "original_command": command,
                    "suggestion_message": "What should I call this object?",
                    "method": "__init__",
                    "parameters": bound_args,
                    "confidence": 100.0,
                    "executable": None,
                    "intent_type": "constructor",
                    "source": "constructor",
                    "explanation": f"Missing constructor parameter(s): {missing}",
                    "breakdown": {
                        "init_params": init_info.get("params", []),
                        "missing": missing,
                    },
                }

                return {
                    "success": True,
                    "class_name": class_name,
                    "file_name": convo.file_name,
                    "command_count": 1,
                    "result": formatted,
                    "results": [formatted],
                }

            # missing constructor params
            if missing:
                state = _load_state(session_dir)
                state["pending"] = {
                    "method": "__init__",
                    "missing": missing,
                    "parameters": {
                        "object_name": object_name,
                        **bound_args,
                    },
                    "class_name": class_name,
                }
                _save_state(session_dir, state)

                first_missing = missing[0].replace("_", " ")
                formatted = {
                    "success": False,
                    "status": "no_match",
                    "original_command": command,
                    "suggestion_message": f"What is the {first_missing} for this {class_name} object?",
                    "method": "__init__",
                    "parameters": {
                        "object_name": object_name,
                        **bound_args,
                    },
                    "confidence": 100.0,
                    "executable": None,
                    "intent_type": "constructor",
                    "source": "constructor",
                    "explanation": f"Missing constructor parameter(s): {missing}",
                    "breakdown": {
                        "init_params": init_info.get("params", []),
                        "missing": missing,
                    },
                }

                return {
                    "success": True,
                    "class_name": class_name,
                    "file_name": convo.file_name,
                    "command_count": 1,
                    "result": formatted,
                    "results": [formatted],
                }

            # fully matched constructor
            if exe:
                _record_undo_once()

                state = _load_state(session_dir)
                state["active_object"] = object_name
                state.setdefault("objects", {})
                state["objects"][object_name] = {
                    "class": class_name,
                    "constructor_args": bound_args,
                }
                state["pending"] = None
                _save_state(session_dir, state)

                formatted = {
                    "success": True,
                    "status": "matched",
                    "original_command": command,
                    "suggestion_message": None,
                    "method": "__init__",
                    "parameters": bound_args,
                    "confidence": 100.0,
                    "executable": exe,
                    "intent_type": "constructor",
                    "source": "constructor",
                    "explanation": "Constructor intent matched (create/make/init).",
                    "breakdown": {
                        "init_params": init_info.get("params", []),
                        "required": init_info.get("required", []),
                    },
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
        
        print("FOLLOWUP RESULT:", r)

        will_append = (r.get("status") == "matched" and r.get("executable"))

        # update pending state FIRST
        if r.get("status") == "matched":
            state["pending"] = None
            _save_state(session_dir, state)

            # IMPORTANT: constructor completed through follow-up
            if r.get("method") == "__init__":
                meta = r.get("meta") or {}
                object_name = meta.get("object_name")
                class_name_from_meta = meta.get("class_name") or class_name

                if object_name:
                    state["active_object"] = object_name
                    state["pending"] = None
                    state.setdefault("objects", {})
                    state["objects"][object_name] = {
                        "class": class_name_from_meta,
                        "constructor_args": r.get("parameters", {}) or {},
                    }
                    _save_state(session_dir, state)

        elif r.get("status") == "need_clarification":
            meta = r.get("meta") or {}
            state["pending"] = {
                "method": r.get("method"),
                "missing": meta.get("missing", []),
                "parameters": r.get("parameters", {}) or {},
                "class_name": meta.get("class_name"),
            }
            _save_state(session_dir, state)
        else:
            state["pending"] = None
            _save_state(session_dir, state)

        # record undo AFTER state is correct
        if will_append:
            _record_undo_once()
            
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
    # Try CFG split first, fall back to simple regex split if CFG returns only 1 part
    command_parts = _split_with_cfg(command, module_path)
    if len(command_parts) <= 1:
        command_parts = _split_compound_simple(command)

    print("command_parts:", command_parts)
    print("[DEBUG] convo.app_type =", getattr(convo, "app_type", None))

    results: List[Dict[str, Any]] = []
    for part in command_parts:
        part = (part or "").strip()
        if not part:
            continue
        results.append(_process_single_command(part, module_path))
        print("[DEBUG] raw executables =", [r.get("executable") for r in results])

    # Determine if any command will append; if so, snapshot before state mutation
    will_append_any = any(
        rr.get("status") == "matched" and rr.get("executable")
        for rr in results
    )
    if will_append_any:
        _record_undo_once()

    # IMPORTANT: if any command created a turtle, set active_object immediately
    for rr in results:
        _maybe_set_active_from_assignment(session_dir, rr.get("executable"))
        
    # Turtle: rewrite executables to active turtle (backend sends final line)
    if _is_turtle_app(convo):
        st = _load_state(session_dir)
        active = st.get("active_object")
        known_objects = st.get("objects", {}) or {}

        print("[DEBUG] active_object at targeting =", active)
        print("[DEBUG] known_objects =", list(known_objects.keys()))

        for rr in results:
            exe_before = rr.get("executable")
            original_command = rr.get("original_command") or ""
            if exe_before:
                explicit_obj = _extract_referenced_object(original_command, known_objects)
                target_obj = explicit_obj or active

                exe_after = _target_turtle_executable(exe_before, target_obj)
                rr["executable"] = exe_after

                print(
                    "[DEBUG] target:",
                    exe_before,
                    "=>",
                    exe_after,
                    "| explicit_obj =",
                    explicit_obj,
                    "| active =",
                    active
                )

    # append matched results to runner
    runner_path = _ensure_runner_exists(session_dir, module_path, class_name)
    for rr in results:
        if rr.get("status") == "matched" and rr.get("executable"):
            _append_to_runner(session_dir, runner_path, rr["executable"], rr.get("original_command"))

    # store pending follow-up if needed
    for rr in results:
        if rr.get("suggestion_message") and rr.get("method"):
            breakdown = rr.get("breakdown") or {}
            state = _load_state(session_dir)
            state["pending"] = {
                "method": rr.get("method"),
                "missing": breakdown.get("missing") or ["unknown"],
                "parameters": rr.get("parameters", {}) or {},
                "class_name": breakdown.get("class_name"),
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

    t_total = (time.time() - t_total_start) * 1000
    print(f"[TIMING] analyze_command conv={conversation_id} cmd='{command[:50]}': {t_total:.0f}ms total")

    return {
        "success": True,
        "class_name": class_name,
        "file_name": convo.file_name,
        "command_count": len(command_parts),
        "result": primary,
        "results": results,
    }