import ast
import threading
import time
from collections import OrderedDict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Conversation
from app.nlp_v3 import NLPService, ASTExtractor

from app.models.schemas import AnalyzeCommandRequest

# Configuration
CONFIDENCE_THRESHOLD = 0.15  # Minimum confidence (15%) to return a match
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

        # Process the command using NLPService
        process_start = time.perf_counter()
        results = service.process(command, language=language, top_k=None)
        process_time = (time.perf_counter() - process_start) * 1000
        print(f"\n[TIMING] Service processing: {process_time:.2f}ms")

        if not results:
            return {
                "class_name": class_name,
                "file_name": convo.file_name,
                "results": [],
                "result": {
                    "success": False,
                    "message": f"No confident matches found (threshold: {CONFIDENCE_THRESHOLD*100:.0f}%)",
                    "confidence": 0.0
                }
            }

        # Format results from ProcessResult objects
        formatted_results = []
        for r in results:
            result_item = {
                "success": r.success,
                "method": r.method_name,
                "parameters": r.parameters,
                "confidence": r.confidence,
                "executable": r.executable,
                "intent_type": "nlp_v3",
                "source": "nlp_v3",
                "action_verb": r.action_verb,
                "explanation": r.explanation,
                "breakdown": r.breakdown
            }
            formatted_results.append(result_item)

        # Maintain backward compatibility - return the top result as "result"
        top_result = formatted_results[0]

        # Final timing summary
        total_time = (time.perf_counter() - request_start) * 1000
        print(f"\n[TIMING] Total request time: {total_time:.2f}ms")
        print(f"[DEBUG] Returning {len(formatted_results)} result(s):")
        for i, r in enumerate(formatted_results, 1):
            print(f"  Result {i}: {r['method']}({r['parameters']}) - {r['confidence']:.1f}%")
        print(f"{'='*60}\n")

        return {
            "class_name": class_name,
            "file_name": convo.file_name,
            "result": top_result,  # For backward compatibility
            "results": formatted_results,  # All detected commands
            "command_count": len(formatted_results)
        }

    except Exception as e:
        total_time = (time.perf_counter() - request_start) * 1000
        print(f"\n[ERROR] Request failed after {total_time:.2f}ms: {str(e)}")
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=f"Error analyzing command: {str(e)}")
