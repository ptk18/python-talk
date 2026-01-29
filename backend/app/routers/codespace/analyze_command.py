import ast
import re
import threading
import time
from collections import OrderedDict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Conversation
from app.nlp_v4 import NLPService, ASTExtractor

from app.models.schemas import AnalyzeCommandRequest

# Configuration
CONFIDENCE_THRESHOLD = 0.15  # Minimum confidence (15%) to return a match
SUGGESTION_THRESHOLD = 0.40  # Below this = "suggestion", above = "matched"
CACHE_MAX_SIZE = 50  # Maximum number of cached pipelines
CACHE_TTL_SECONDS = 3600  # 1 hour TTL for cache entries

# LRU Cache with TTL for pipeline instances
class LRUCache:
    def __init__(self, max_size: int = 50, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache = OrderedDict()  # {key: (pipeline, timestamp)}
        self.lock = threading.Lock()

    def get(self, key: str):
        with self.lock:
            if key not in self.cache:
                return None
            pipeline, timestamp = self.cache[key]
            # Check TTL
            if time.time() - timestamp > self.ttl:
                del self.cache[key]
                return None
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return pipeline

    def set(self, key: str, pipeline):
        with self.lock:
            # Remove if exists to update position
            if key in self.cache:
                del self.cache[key]
            # Evict oldest if at capacity
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                print(f"[Cache] Evicting oldest pipeline: {oldest_key}")
                del self.cache[oldest_key]
            # Add new entry
            self.cache[key] = (pipeline, time.time())

    def delete(self, key: str):
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self):
        with self.lock:
            self.cache.clear()

    def stats(self):
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl,
                "keys": list(self.cache.keys())
            }

# Global service cache with LRU eviction
_service_cache = LRUCache(max_size=CACHE_MAX_SIZE, ttl_seconds=CACHE_TTL_SECONDS)

router = APIRouter(tags=["Analyze Command"])


def _split_compound_command(command: str, method_names: list = None):
    """Split compound commands like 'add 2 and 3 then multiply 4 by 6' into parts.

    When method_names is provided, also splits on bare 'and' when it is followed
    by a known method name (e.g. 'divide 3 by 9 and add 4 and 6' splits into
    ['divide 3 by 9', 'add 4 and 6']).  Without this, bare 'and' is preserved
    so that 'add 2 and 3' keeps working.
    """
    processed = command.strip()

    split_patterns = [
        r'\s+and\s+then\s+',
        r'\s+after\s+that\s+',
        r'\s+then\s+',
        r'\s+next\s+',
        r',\s*then\s+',
        r',\s*and\s+',
        r',\s+',
    ]

    parts = [processed]
    for pattern in split_patterns:
        new_parts = []
        for part in parts:
            split_result = re.split(pattern, part, flags=re.IGNORECASE)
            new_parts.extend([p.strip() for p in split_result if p.strip()])
        parts = new_parts

    # Smart "and" splitting: only split on bare "and" when it is followed by
    # a known method name.  This preserves "add 2 and 3" while splitting
    # "divide 3 by 9 and add 4 and 6" correctly.
    if method_names:
        names_lower = {n.lower() for n in method_names}
        new_parts = []
        for part in parts:
            new_parts.extend(_split_on_and_before_method(part, names_lower))
        parts = new_parts

    parts = [p for p in parts if len(p) > 2]
    return parts if parts else [command]


def _split_on_and_before_method(text: str, method_names_lower: set) -> list:
    """Split text on ' and ' only when the word immediately after is a known method name."""
    # Find all occurrences of ' and ' (case-insensitive)
    pattern = re.compile(r'\s+and\s+', re.IGNORECASE)
    matches = list(pattern.finditer(text))
    if not matches:
        return [text]

    # Determine which 'and' occurrences are separators (next word is a method name)
    split_positions = []
    for m in matches:
        after = text[m.end():].strip()
        first_word = after.split()[0].lower() if after.split() else ""
        # Also check underscore-separated method names (e.g. "set_temperature")
        if first_word in method_names_lower:
            split_positions.append((m.start(), m.end()))

    if not split_positions:
        return [text]

    # Split at the identified positions
    result = []
    prev_end = 0
    for start, end in split_positions:
        chunk = text[prev_end:start].strip()
        if chunk:
            result.append(chunk)
        prev_end = end
    # Remaining text after last split
    remaining = text[prev_end:].strip()
    if remaining:
        result.append(remaining)

    return result


def _process_single_command(command: str, service: NLPService):
    """Process a single sub-command and return a result dict with status."""
    results = service.process(command, top_k=1)

    if not results:
        return {
            "success": False,
            "status": "no_match",
            "original_command": command,
            "suggestion_message": None,
            "method": None,
            "parameters": {},
            "confidence": 0.0,
            "executable": None,
        }

    r = results[0]
    confidence_frac = r.confidence / 100.0  # Convert back to 0-1 for threshold check

    if confidence_frac >= SUGGESTION_THRESHOLD:
        status = "matched"
        suggestion_message = None
    else:
        status = "suggestion"
        suggestion_message = f"Did you mean {r.method_name}?"

    return {
        "success": r.success,
        "status": status,
        "original_command": command,
        "suggestion_message": suggestion_message,
        "method": r.method_name,
        "parameters": r.parameters,
        "confidence": r.confidence,
        "executable": r.executable,
        "intent_type": "nlp_v4",
        "source": "nlp_v4",
        "action_verb": r.action_verb,
        "explanation": r.explanation,
        "breakdown": r.breakdown,
    }


@router.post("/prewarm_pipeline")
def prewarm_pipeline(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    """Pre-warm the NLP service for faster first command processing"""
    conversation_id = payload.conversation_id

    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not convo.code:
        raise HTTPException(status_code=400, detail="This conversation has no uploaded code")

    # Check if already cached
    cache_key = f"conv_{conversation_id}"
    existing = _service_cache.get(cache_key)

    if existing is not None:
        return {"status": "already_cached", "message": "Service already initialized"}

    try:
        print(f"Pre-warming NLP service for conversation {conversation_id}")

        # Create NLPService with ASTExtractor (no preprocessor for Codespace)
        service = NLPService(
            extractor=ASTExtractor(),
            confidence_threshold=CONFIDENCE_THRESHOLD
        )

        # Initialize with the code string directly (ASTExtractor supports this)
        methods = service.initialize(convo.code)

        if not methods:
            raise HTTPException(status_code=400, detail="No public methods found in uploaded file")

        _service_cache.set(cache_key, service)
        return {
            "status": "initialized",
            "message": "Service pre-warmed successfully",
            "method_count": len(methods)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pre-warming service: {str(e)}")


@router.post("/invalidate_pipeline_cache")
def invalidate_pipeline_cache(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    """Invalidate (clear) the NLP service cache for a conversation when code is updated"""
    conversation_id = payload.conversation_id
    cache_key = f"conv_{conversation_id}"

    if _service_cache.delete(cache_key):
        print(f"Invalidated service cache for conversation {conversation_id}")
        return {"status": "invalidated", "message": "Service cache cleared successfully"}
    else:
        return {"status": "not_cached", "message": "No cache found for this conversation"}


@router.get("/pipeline_cache_stats")
def get_pipeline_cache_stats():
    """Get statistics about the service cache"""
    return _service_cache.stats()


@router.post("/analyze_command")
def analyze_command(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    request_start = time.perf_counter()
    print(f"\n{'='*60}")
    print(f"[DEBUG] Processing command: '{payload.command}'")
    print(f"[DEBUG] Conversation ID: {payload.conversation_id}")
    print(f"[DEBUG] Language: {payload.language or 'en'}")
    print(f"{'='*60}")

    conversation_id = payload.conversation_id
    command = payload.command
    language = payload.language or "en"

    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not convo.code:
        raise HTTPException(status_code=400, detail="This conversation has no uploaded code")

    try:
        # Extract class name from the code (for response compatibility)
        tree = ast.parse(convo.code)
        class_name = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                break
        if not class_name:
            class_name = "UnknownClass"

        # Use cached service or create new one (LRU with TTL)
        cache_key = f"conv_{conversation_id}"
        service = _service_cache.get(cache_key)

        if service is None:
            print(f"[DEBUG] Cache MISS - Initializing NLP service for conversation {conversation_id}")
            init_start = time.perf_counter()

            # Create NLPService with ASTExtractor (no preprocessor for Codespace)
            service = NLPService(
                extractor=ASTExtractor(),
                confidence_threshold=CONFIDENCE_THRESHOLD
            )
            methods = service.initialize(convo.code)

            if not methods:
                raise HTTPException(status_code=400, detail="No public methods found in uploaded file")

            _service_cache.set(cache_key, service)
            init_time = (time.perf_counter() - init_start) * 1000
            print(f"[TIMING] Service initialization: {init_time:.2f}ms")
        else:
            print(f"[DEBUG] Cache HIT - Using cached service for conversation {conversation_id}")

        # Split compound command and process each part
        process_start = time.perf_counter()
        method_names = service.get_method_names()
        command_parts = _split_compound_command(command, method_names=method_names)
        print(f"[DEBUG] Split into {len(command_parts)} part(s): {command_parts}")

        formatted_results = []
        for part in command_parts:
            result = _process_single_command(part, service)
            formatted_results.append(result)

        process_time = (time.perf_counter() - process_start) * 1000
        print(f"\n[TIMING] Service processing: {process_time:.2f}ms")

        if not formatted_results:
            return {
                "class_name": class_name,
                "file_name": convo.file_name,
                "results": [],
                "result": {
                    "success": False,
                    "status": "no_match",
                    "message": f"No confident matches found (threshold: {CONFIDENCE_THRESHOLD*100:.0f}%)",
                    "confidence": 0.0
                }
            }

        # Maintain backward compatibility - return the top result as "result"
        top_result = formatted_results[0]

        # Final timing summary
        total_time = (time.perf_counter() - request_start) * 1000
        print(f"\n[TIMING] Total request time: {total_time:.2f}ms")
        print(f"[DEBUG] Returning {len(formatted_results)} result(s):")
        for i, r in enumerate(formatted_results, 1):
            status_tag = r['status'].upper()
            print(f"  Result {i} [{status_tag}]: {r.get('method', '?')}({r.get('parameters', {})}) - {r.get('confidence', 0):.1f}%")
        print(f"{'='*60}\n")

        return {
            "class_name": class_name,
            "file_name": convo.file_name,
            "result": top_result,
            "results": formatted_results,
            "command_count": len(formatted_results)
        }

    except Exception as e:
        total_time = (time.perf_counter() - request_start) * 1000
        print(f"\n[ERROR] Request failed after {total_time:.2f}ms: {str(e)}")
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=f"Error analyzing command: {str(e)}")
