"""
NLP v3 - Honest Pipeline with Transparent Scoring
Based on nlp_poc_honest.py with modular architecture

Global Model Registry:
- Models are loaded ONCE at module import time
- Shared across all pipeline instances
- Eliminates repeated model loading per request
"""

import os
import threading

# Global model registry - loaded once, shared across all pipelines
_MODELS = {}
_MODELS_LOCK = threading.Lock()


def get_semantic_model():
    """
    Get or create the SentenceTransformer model (shared singleton).
    Model is loaded once and reused across all pipelines.
    Returns None if DISABLE_SEMANTIC_MATCHING=true.
    """
    # Check if semantic matching is disabled
    if os.getenv("DISABLE_SEMANTIC_MATCHING", "false").lower() == "true":
        return None

    if 'sentence_transformer' not in _MODELS:
        with _MODELS_LOCK:
            if 'sentence_transformer' not in _MODELS:
                print("[ModelRegistry] Loading SentenceTransformer (all-MiniLM-L6-v2)...")
                try:
                    from sentence_transformers import SentenceTransformer
                    _MODELS['sentence_transformer'] = SentenceTransformer('all-MiniLM-L6-v2')
                    print("[ModelRegistry] SentenceTransformer loaded successfully")
                except ImportError:
                    print("[ModelRegistry] Warning: sentence_transformers not installed")
                    _MODELS['sentence_transformer'] = None
    return _MODELS.get('sentence_transformer')


def get_sentence_transformer_util():
    """Get the sentence_transformers util module for cosine similarity."""
    if 'st_util' not in _MODELS:
        with _MODELS_LOCK:
            if 'st_util' not in _MODELS:
                try:
                    from sentence_transformers import util
                    _MODELS['st_util'] = util
                except ImportError:
                    _MODELS['st_util'] = None
    return _MODELS.get('st_util')


def get_spacy_model():
    """
    Get or create the spaCy model (shared singleton).
    Model is loaded once and reused across all pipelines.
    Prefers en_core_web_md, falls back to en_core_web_sm or en_core_web_trf.
    """
    if 'spacy' not in _MODELS:
        with _MODELS_LOCK:
            if 'spacy' not in _MODELS:
                print("[ModelRegistry] Loading spaCy model...")
                try:
                    import spacy
                    # Try models in order of preference
                    for model_name in ["en_core_web_md", "en_core_web_sm", "en_core_web_trf"]:
                        try:
                            _MODELS['spacy'] = spacy.load(model_name)
                            print(f"[ModelRegistry] spaCy loaded: {model_name}")
                            break
                        except OSError:
                            continue
                    if 'spacy' not in _MODELS:
                        print("[ModelRegistry] Warning: No spaCy model available")
                        _MODELS['spacy'] = None
                except ImportError:
                    print("[ModelRegistry] Warning: spaCy not installed")
                    _MODELS['spacy'] = None
    return _MODELS.get('spacy')


def preload_models():
    """
    Pre-load all models at application startup.
    Call this in FastAPI lifespan or main.py to warm up models.
    """
    print("[ModelRegistry] Pre-loading models...")
    get_semantic_model()
    get_sentence_transformer_util()
    get_spacy_model()
    print("[ModelRegistry] All models pre-loaded")


def get_model_status():
    """Get status of loaded models for debugging."""
    return {
        'sentence_transformer': 'sentence_transformer' in _MODELS and _MODELS['sentence_transformer'] is not None,
        'spacy': 'spacy' in _MODELS and _MODELS['spacy'] is not None,
        'st_util': 'st_util' in _MODELS and _MODELS['st_util'] is not None,
    }


# Imports for public API
from .main import NLPPipeline, process_command
from .models import MethodInfo, MatchScore
from .catalog import extract_from_file, FileCatalog, ClassCatalog, MethodCatalog

# New generic service architecture
from .service import NLPService, ProcessResult
from .extractors import BaseExtractor, ASTExtractor, ModuleExtractor, TurtleExtractor
from .preprocessors import BasePreprocessor, DefaultPreprocessor, TurtlePreprocessor

__all__ = [
    # Core pipeline (legacy - for backward compatibility)
    'NLPPipeline',
    'process_command',
    'MethodInfo',
    'MatchScore',
    'extract_from_file',
    'FileCatalog',
    'ClassCatalog',
    'MethodCatalog',
    # Model registry functions
    'get_semantic_model',
    'get_sentence_transformer_util',
    'get_spacy_model',
    'preload_models',
    'get_model_status',
    # New generic service architecture
    'NLPService',
    'ProcessResult',
    # Extractors (pluggable method extraction strategies)
    'BaseExtractor',
    'ASTExtractor',
    'ModuleExtractor',
    'TurtleExtractor',
    # Preprocessors (pluggable command preprocessing strategies)
    'BasePreprocessor',
    'DefaultPreprocessor',
    'TurtlePreprocessor',
]
