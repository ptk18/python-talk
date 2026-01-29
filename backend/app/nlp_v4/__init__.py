"""
NLP v4 - Semantic-First Pipeline with all-mpnet-base-v2

Pure embedding-based command-to-method matching.
No lexical heuristics, no LLM calls, no synonym generators.

Global Model Registry:
- SentenceTransformer loaded ONCE, shared across all pipeline instances
"""

import os
import threading

_MODELS = {}
_MODELS_LOCK = threading.Lock()

MODEL_NAME = os.getenv("NLP_V4_MODEL", "all-mpnet-base-v2")


def get_embedding_model():
    """Get or create the SentenceTransformer model (shared singleton)."""
    if "embedding_model" not in _MODELS:
        with _MODELS_LOCK:
            if "embedding_model" not in _MODELS:
                print(f"[NLP_v4] Loading SentenceTransformer ({MODEL_NAME})...")
                try:
                    from sentence_transformers import SentenceTransformer
                    _MODELS["embedding_model"] = SentenceTransformer(MODEL_NAME)
                    print(f"[NLP_v4] Model loaded successfully")
                except ImportError:
                    print("[NLP_v4] Warning: sentence_transformers not installed")
                    _MODELS["embedding_model"] = None
    return _MODELS.get("embedding_model")


def get_sentence_transformer_util():
    """Get the sentence_transformers util module for cosine similarity."""
    if "st_util" not in _MODELS:
        with _MODELS_LOCK:
            if "st_util" not in _MODELS:
                try:
                    from sentence_transformers import util
                    _MODELS["st_util"] = util
                except ImportError:
                    _MODELS["st_util"] = None
    return _MODELS.get("st_util")


GLINER_MODEL_NAME = os.getenv("NLP_V4_GLINER_MODEL", "knowledgator/gliner-multitask-large-v0.5")


def get_gliner_model():
    """Get or create the GLiNER model (shared singleton)."""
    if "gliner_model" not in _MODELS:
        with _MODELS_LOCK:
            if "gliner_model" not in _MODELS:
                print(f"[NLP_v4] Loading GLiNER ({GLINER_MODEL_NAME})...")
                try:
                    from gliner import GLiNER
                    _MODELS["gliner_model"] = GLiNER.from_pretrained(GLINER_MODEL_NAME)
                    print("[NLP_v4] GLiNER loaded successfully")
                except ImportError:
                    print("[NLP_v4] Warning: gliner not installed")
                    _MODELS["gliner_model"] = None
    return _MODELS.get("gliner_model")


def preload_models():
    """Pre-load all models at application startup."""
    print("[NLP_v4] Pre-loading models...")
    get_embedding_model()
    get_sentence_transformer_util()
    get_gliner_model()
    print("[NLP_v4] All models pre-loaded")


def get_model_status():
    """Get status of loaded models for debugging."""
    return {
        "embedding_model": "embedding_model" in _MODELS and _MODELS["embedding_model"] is not None,
        "model_name": MODEL_NAME,
        "st_util": "st_util" in _MODELS and _MODELS["st_util"] is not None,
        "gliner_model": "gliner_model" in _MODELS and _MODELS["gliner_model"] is not None,
        "gliner_model_name": GLINER_MODEL_NAME,
    }


# Public API
from .service import NLPService, ProcessResult
from .models import MethodInfo, MatchResult
from .extractors import BaseExtractor, ASTExtractor, ModuleExtractor, TurtleExtractor
from .preprocessors import BasePreprocessor, DefaultPreprocessor, TurtlePreprocessor

__all__ = [
    "NLPService",
    "ProcessResult",
    "MatchResult",
    "MethodInfo",
    "BaseExtractor",
    "ASTExtractor",
    "ModuleExtractor",
    "TurtleExtractor",
    "BasePreprocessor",
    "DefaultPreprocessor",
    "TurtlePreprocessor",
    "get_embedding_model",
    "get_sentence_transformer_util",
    "get_gliner_model",
    "preload_models",
    "get_model_status",
]
