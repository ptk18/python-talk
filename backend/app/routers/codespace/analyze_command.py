import ast
import json
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Conversation
from app.models.schemas import AnalyzeCommandRequest

from app.parser_engine.api import compile_single, apply_followup
from app.parser_engine.lex_alz import analyze_sentence
from app.parser_engine.phase2_domain import load_domain, phase2_map_tokens
from app.parser_engine.cfg_parser import parse_command, extract_nodes_by_name, span_to_text

router = APIRouter()

# Parser confidence thresholds (0-100 scale)
CONFIDENCE_THRESHOLD = 20.0
SUGGESTION_THRESHOLD = 35.0

CACHE_MAX_SIZE = 50
CACHE_TTL_SECONDS = 3600

# IMPORTANT: file is in backend/app/routers/codespace/
# parents[2] = backend/app
BASE_EXEC_DIR = Path(__file__).resolve().parents[2] / "executions"


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

    module_name = module_path.stem  # "smarthome" from "smarthome.py"
    runner_path.write_text(
        f"from {module_name} import {class_name}\n"
        f"import sys\n\n"
        f"obj = {class_name}()\n",
        encoding="utf-8"
    )
    return runner_path

def _append_to_runner(runner_path: Path, executable: str) -> None:
    line = (executable or "").strip()
    if not line:
        return
    with runner_path.open("a", encoding="utf-8") as f:
        f.write(f"print(obj.{line})\n")


# ============================================================
# Domain helpers (class/methods)
# ============================================================
def _extract_class_and_methods(py_text: str) -> Tuple[Optional[str], List[str]]:
    """
    Returns (class_name, method_names) using first ClassDef found.
    """
    try:
        tree = ast.parse(py_text)
    except Exception:
        return None, []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if item.name.startswith("__") and item.name.endswith("__"):
                        continue
                    methods.append(item.name)
            return class_name, methods

    return None, []


# ============================================================
# CFG-based splitting
# ============================================================
def _filtered_tokens_for_cfg(lex_tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Must match RDParser filtering (punctuation/UNKNOWN removed).
    """
    return [t for t in lex_tokens if t.get("POS") not in ("punctuation", "UNKNOWN")]

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

    # IMPORTANT: parse tree spans are based on parser's filtered token list
    toks_for_span = _filtered_tokens_for_cfg(lex_tokens)

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
        return {
            "success": False,
            "status": "no_match",
            "original_command": command,
            "suggestion_message": r.get("question"),
            "method": r.get("method"),
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
        raise HTTPException(status_code=400, detail=f"Session file not found: {module_path}")

    # class/methods cache
    cached = pipeline_cache.get(f"conv_{conversation_id}")
    if cached:
        class_name = cached.get("class_name")
    else:
        py_text = module_path.read_text(encoding="utf-8")
        class_name, method_names = _extract_class_and_methods(py_text)
        pipeline_cache.set(f"conv_{conversation_id}", {"class_name": class_name, "methods": method_names})

    if not class_name:
        raise HTTPException(status_code=400, detail="No class found in session file")

    # ------------------------------------------------------------
    # Follow-up flow ("turn on" -> "turn on what?" then user says "tv")
    # ------------------------------------------------------------
    state = _load_state(session_dir)
    pending = state.get("pending")

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
                "suggestion_message": r.get("question"),
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

        # append to runner if matched
        if formatted.get("status") == "matched" and formatted.get("executable"):
            runner_path = _ensure_runner_exists(session_dir, module_path, class_name)
            _append_to_runner(runner_path, formatted["executable"])

        return {
            "success": True,
            "class_name": class_name,
            "file_name": convo.file_name,
            "command_count": 1,
            "result": formatted,
            "results": [formatted],
        }

    # ------------------------------------------------------------
    # Normal flow: split into multiple commands using CFG
    # ------------------------------------------------------------
    command_parts = _split_with_cfg(command, module_path)

    results: List[Dict[str, Any]] = []
    for part in command_parts:
        part = (part or "").strip()
        if not part:
            continue
        results.append(_process_single_command(part, module_path))

    # append matched results to runner
    runner_path = _ensure_runner_exists(session_dir, module_path, class_name)
    for rr in results:
        if rr.get("status") == "matched" and rr.get("executable"):
            _append_to_runner(runner_path, rr["executable"])

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
