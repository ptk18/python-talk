import os
import tempfile
import threading
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Conversation
from app.nlp_v3.utils import extract_methods_from_file
from app.nlp_v3.main import NLPPipeline

from app.models.schemas import AnalyzeCommandRequest

# Global pipeline instance (reused across requests for performance) with thread lock
_pipeline_cache = {}
_cache_lock = threading.Lock()

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

    import tempfile, os
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
        temp_file.write(convo.code.encode("utf-8"))
        temp_path = temp_file.name

    try:
        # Extract methods from the uploaded Python file
        methods = extract_methods_from_file(temp_path)

        if not methods:
            raise HTTPException(status_code=400, detail="No public methods found in uploaded file")

        # Initialize pipeline in cache (thread-safe)
        cache_key = f"conv_{conversation_id}"

        with _cache_lock:
            if cache_key not in _pipeline_cache:
                print(f"Pre-warming NLP v3 pipeline for conversation {conversation_id}")
                pipeline = NLPPipeline()
                pipeline.initialize(methods)
                _pipeline_cache[cache_key] = pipeline
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

    with _cache_lock:
        if cache_key in _pipeline_cache:
            del _pipeline_cache[cache_key]
            print(f"Invalidated pipeline cache for conversation {conversation_id}")
            return {"status": "invalidated", "message": "Pipeline cache cleared successfully"}
        else:
            return {"status": "not_cached", "message": "No cache found for this conversation"}


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

    import tempfile, os
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

        # Use cached pipeline or create new one per conversation (thread-safe)
        cache_key = f"conv_{conversation_id}"

        with _cache_lock:
            if cache_key not in _pipeline_cache:
                print(f"Initializing NLP v3 pipeline for conversation {conversation_id}")
                pipeline = NLPPipeline()
                pipeline.initialize(methods)
                _pipeline_cache[cache_key] = pipeline
            else:
                pipeline = _pipeline_cache[cache_key]

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

        # Format all results
        formatted_results = []
        for action_verb, match_score in results:
            result_item = {
                "success": True,
                "method": match_score.method_name,
                "parameters": match_score.extracted_params,
                "confidence": match_score.total_score * 100,  # Convert to percentage
                "executable": match_score.get_method_call(),  # This is what frontend expects!
                "intent_type": "nlp_v3",
                "source": "nlp_v3",
                "action_verb": action_verb,  # Include the detected verb
                # Additional v3-specific fields
                "explanation": match_score.explain(),
                "breakdown": {
                    "semantic_score": match_score.semantic_score * 100,
                    "intent_score": match_score.intent_score * 100,
                    "synonym_boost": match_score.synonym_boost * 100,
                    "param_relevance": match_score.param_relevance * 100,
                    "phrasal_verb_match": match_score.phrasal_verb_match * 100
                }
            }
            formatted_results.append(result_item)

        # Maintain backward compatibility - return the top result as "result" 
        # and all results as "results"
        top_result = formatted_results[0] if formatted_results else {
            "success": False,
            "message": "No matching methods found",
            "confidence": 0.0
        }

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
