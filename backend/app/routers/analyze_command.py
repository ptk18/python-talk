import os
import tempfile
import threading
import time
from collections import OrderedDict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Conversation
from app.nlp_v3.utils import extract_methods_from_file
from app.nlp_v3.main import NLPPipeline

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

# Global pipeline cache with LRU eviction
_pipeline_cache = LRUCache(max_size=CACHE_MAX_SIZE, ttl_seconds=CACHE_TTL_SECONDS)

router = APIRouter(tags=["Analyze Command"])

@router.post("/prewarm_pipeline")
def prewarm_pipeline(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    """Pre-warm the NLP pipeline for faster first command processing"""
    conversation_id = payload.conversation_id

    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not convo.code:
        raise HTTPException(status_code=400, detail="This conversation has no uploaded code")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
        temp_file.write(convo.code.encode("utf-8"))
        temp_path = temp_file.name

    try:
        # Extract methods from the uploaded Python file
        methods = extract_methods_from_file(temp_path)

        if not methods:
            raise HTTPException(status_code=400, detail="No public methods found in uploaded file")

        # Initialize pipeline in cache (LRU with TTL)
        cache_key = f"conv_{conversation_id}"
        existing = _pipeline_cache.get(cache_key)

        if existing is None:
            print(f"Pre-warming NLP v3 pipeline for conversation {conversation_id}")
            pipeline = NLPPipeline()
            pipeline.initialize(methods)
            _pipeline_cache.set(cache_key, pipeline)
            return {"status": "initialized", "message": "Pipeline pre-warmed successfully"}
        else:
            return {"status": "already_cached", "message": "Pipeline already initialized"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error pre-warming pipeline: {str(e)}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/invalidate_pipeline_cache")
def invalidate_pipeline_cache(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    """Invalidate (clear) the NLP pipeline cache for a conversation when code is updated"""
    conversation_id = payload.conversation_id
    cache_key = f"conv_{conversation_id}"

    if _pipeline_cache.delete(cache_key):
        print(f"Invalidated pipeline cache for conversation {conversation_id}")
        return {"status": "invalidated", "message": "Pipeline cache cleared successfully"}
    else:
        return {"status": "not_cached", "message": "No cache found for this conversation"}


@router.get("/pipeline_cache_stats")
def get_pipeline_cache_stats():
    """Get statistics about the pipeline cache"""
    return _pipeline_cache.stats()


@router.post("/analyze_command")
def analyze_command(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    conversation_id = payload.conversation_id
    command = payload.command
    language = payload.language or "en"

    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not convo.code:
        raise HTTPException(status_code=400, detail="This conversation has no uploaded code")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
        temp_file.write(convo.code.encode("utf-8"))
        temp_path = temp_file.name

    try:
        # Extract methods from the uploaded Python file
        methods = extract_methods_from_file(temp_path)

        if not methods:
            raise HTTPException(status_code=400, detail="No public methods found in uploaded file")

        # Extract class name (for response compatibility)
        import ast
        with open(temp_path, 'r') as f:
            tree = ast.parse(f.read())
        class_name = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                break

        if not class_name:
            class_name = "UnknownClass"

        # Use cached pipeline or create new one (LRU with TTL)
        cache_key = f"conv_{conversation_id}"
        pipeline = _pipeline_cache.get(cache_key)

        if pipeline is None:
            print(f"Initializing NLP v3 pipeline for conversation {conversation_id}")
            pipeline = NLPPipeline()
            pipeline.initialize(methods)
            _pipeline_cache.set(cache_key, pipeline)

        # Process the command - remove top_k limit to get all results
        results = pipeline.process_command(command, methods, top_k=None)

        if not results:
            return {
                "class_name": class_name,
                "file_name": convo.file_name,
                "results": [],
                "result": {
                    "success": False,
                    "message": "No matching methods found",
                    "confidence": 0.0
                }
            }

        # Format results and filter by confidence threshold
        formatted_results = []
        for action_verb, match_score in results:
            # Skip low-confidence matches
            if match_score.total_score < CONFIDENCE_THRESHOLD:
                print(f"[Filter] Skipping low-confidence match: {match_score.method_name} ({match_score.total_score*100:.1f}% < {CONFIDENCE_THRESHOLD*100}%)")
                continue

            result_item = {
                "success": True,
                "method": match_score.method_name,
                "parameters": match_score.extracted_params,
                "confidence": match_score.total_score * 100,  # Convert to percentage
                "executable": match_score.get_method_call(),  # This is what frontend expects!
                "intent_type": "nlp_v3",
                "source": "nlp_v3",
                "action_verb": action_verb,  # Include the detected verb
                # Simplified 4-factor breakdown (easier to debug)
                "explanation": match_score.explain(),
                "breakdown": {
                    "direct_match": match_score.phrasal_verb_match * 100,   # 50% weight
                    "synonym_match": match_score.synonym_boost * 100,       # 25% weight
                    "entity_match": match_score.intent_score * 100,         # 15% weight
                    "semantic_score": match_score.semantic_score * 100,     # 10% weight
                    "param_bonus": match_score.param_relevance * 100        # +5% bonus
                }
            }
            formatted_results.append(result_item)

        # If all results were filtered out due to low confidence
        if not formatted_results:
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

        # Maintain backward compatibility - return the top result as "result"
        # and all results as "results"
        top_result = formatted_results[0]

        return {
            "class_name": class_name,
            "file_name": convo.file_name,
            "result": top_result,  # For backward compatibility
            "results": formatted_results,  # All detected commands
            "command_count": len(formatted_results)  # Number of detected commands
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing command: {str(e)}")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
