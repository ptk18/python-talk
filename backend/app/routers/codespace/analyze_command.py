import ast
import re
import threading
import time
from collections import OrderedDict
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Conversation
from app.models.schemas import AnalyzeCommandRequest

from app.parser_engine.api import compile_single, apply_followup 

import json
import os

router = APIRouter()

# Parser confidence thresholds (0-100 scale)
CONFIDENCE_THRESHOLD = 20.0   # below -> no_match
SUGGESTION_THRESHOLD = 35.0   # below this but >= CONFIDENCE -> suggestion, above -> matched

CACHE_MAX_SIZE = 50
CACHE_TTL_SECONDS = 3600

BASE_EXEC_DIR = Path(__file__).resolve().parents[2] / "executions"

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

    def clear(self):
        with self.lock:
            self.cache.clear()

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
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def _ensure_runner_exists(session_dir: Path, module_path: Path, class_name: str) -> Path:
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
    # executable is like: turn_on(device='tv')
    line = executable.strip()
    if not line:
        return
    with runner_path.open("a", encoding="utf-8") as f:
        f.write(f"print(obj.{line})\n")


def _extract_class_and_methods(py_text: str):
    """
    Returns (class_name, method_names)
    Uses first ClassDef found.
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


def _split_compound_command(command: str, method_names: list = None):
    """
    Split compound commands like:
      'turn on light and turn on tv then wait'
    """
    processed = command.strip()

    split_patterns = [
        r"\bthen\b",
        r"\bnext\b",
        r"\band then\b",
        r"\bafter that\b",
        r"\bafterwards\b",
        r";",
    ]

    # Split on hard separators first
    parts = [processed]
    for pattern in split_patterns:
        new_parts = []
        for p in parts:
            new_parts.extend([x.strip() for x in re.split(pattern, p, flags=re.IGNORECASE) if x.strip()])
        parts = new_parts

    # Optional: split on bare "and" only when it starts a new method
    if method_names:
        final_parts = []
        for p in parts:
            tokens = p.split()
            if "and" not in [t.lower() for t in tokens]:
                final_parts.append(p)
                continue

            buf = []
            i = 0
            while i < len(tokens):
                t = tokens[i]
                if t.lower() == "and" and i + 1 < len(tokens) and tokens[i + 1].lower() in {m.lower() for m in method_names}:
                    if buf:
                        final_parts.append(" ".join(buf).strip())
                        buf = []
                    i += 1  # skip 'and'
                    continue
                buf.append(t)
                i += 1
            if buf:
                final_parts.append(" ".join(buf).strip())
        parts = [p for p in final_parts if p]
    return parts


def _process_single_command(command: str, module_path: Path):
    r = compile_single(command, str(module_path))

    status = r.get("status")
    confidence = float(r.get("confidence", 0.0))

    # Need clarification -> return no_match but with a helpful suggestion_message
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

    # no match
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

    # cache class/method list only (optional)
    py_text = module_path.read_text(encoding="utf-8")
    class_name, method_names = _extract_class_and_methods(py_text)
    pipeline_cache.set(f"conv_{conversation_id}", {"class_name": class_name, "methods": method_names})
    return {"success": True, "message": "Pipeline prewarmed"}


@router.post("/invalidate_pipeline_cache")
def invalidate_pipeline_cache(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    conversation_id = payload.conversation_id
    pipeline_cache.invalidate(f"conv_{conversation_id}")
    return {"success": True, "message": "Cache invalidated"}


@router.get("/pipeline_cache_stats")
def get_pipeline_cache_stats():
    return pipeline_cache.stats()


@router.post("/analyze_command")
def analyze_command(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    conversation_id = payload.conversation_id
    command = payload.command

    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    session_dir = BASE_EXEC_DIR / f"session_{conversation_id}"
    module_path = session_dir / convo.file_name
    if not module_path.exists():
        raise HTTPException(status_code=400, detail=f"Session file not found: {module_path}")
    
    # get class_name + method_names early (needed for follow-up response too)
    cached = pipeline_cache.get(f"conv_{conversation_id}")
    if cached:
        class_name = cached.get("class_name")
        method_names = cached.get("methods", [])
    else:
        py_text = module_path.read_text(encoding="utf-8")
        class_name, method_names = _extract_class_and_methods(py_text)
        pipeline_cache.set(f"conv_{conversation_id}", {"class_name": class_name, "methods": method_names})

    
    # follow-up flow (answer to "turn on what?")
    state = _load_state(session_dir)
    pending = state.get("pending")

    if pending:
        r = apply_followup(pending, command, str(module_path))

        # clear or update pending
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

        # return in same schema
        result_obj = _process_single_command("FOLLOWUP", module_path)  # dummy call not used
        # overwrite with followup result in frontend schema:
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
            
        if r.get("status") == "matched" and r.get("executable"):
            runner_path = _ensure_runner_exists(session_dir, module_path, class_name)
            _append_to_runner(runner_path, r["executable"])

        return {
            "success": True,
            "class_name": class_name,
            "file_name": convo.file_name,
            "command_count": 1,
            "result": formatted,
            "results": [formatted],
        }


    # cached method names for better compound split
    cached = pipeline_cache.get(f"conv_{conversation_id}")
    if cached:
        class_name = cached.get("class_name")
        method_names = cached.get("methods", [])
    else:
        py_text = module_path.read_text(encoding="utf-8")
        class_name, method_names = _extract_class_and_methods(py_text)
        pipeline_cache.set(f"conv_{conversation_id}", {"class_name": class_name, "methods": method_names})

    command_parts = _split_compound_command(command, method_names=method_names)

    results = []
    for part in command_parts:
        results.append(_process_single_command(part, module_path))
        
    # auto-append all matched commands to runner.py
    runner_path = _ensure_runner_exists(session_dir, module_path, class_name)
    for rr in results:
        if rr.get("status") == "matched" and rr.get("executable"):
            _append_to_runner(runner_path, rr["executable"])
            
    # if parser asked a question, store pending in session state
    for i, r in enumerate(results):
        if r.get("suggestion_message") and r.get("method"):
            state = _load_state(session_dir)
            state["pending"] = {
                "method": r.get("method"),
                "missing": ((r.get("breakdown") or {}).get("missing")) or ["unknown"],
                "parameters": r.get("parameters", {}) or {},
            }
            _save_state(session_dir, state)
            break


    # Keep same response fields your frontend uses
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
