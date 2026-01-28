"""Semantic similarity matching using sentence-transformers with caching"""

import os
from functools import lru_cache
from typing import List, Dict, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from .models import MethodInfo

# Feature flag for CodeBERT - disabled by default to save ~340MB RAM
# Enable with FEATURE_CODEBERT=true if you have enough memory
FEATURE_CODEBERT = os.getenv("FEATURE_CODEBERT", "false").lower() == "true"

# Feature flag to disable SentenceTransformer (heavy model)
# When true, falls back to spaCy word vectors (lightweight ~50MB vs ~500MB)
DISABLE_SEMANTIC_MATCHING = os.getenv("DISABLE_SEMANTIC_MATCHING", "false").lower() == "true"


class LocalSemanticMatcher:
    def __init__(self):
        self.method_embeddings: Dict[str, np.ndarray] = {}
        self.method_embeddings_code: Dict[str, np.ndarray] = {}
        self._initialized = False
        self.use_codebert = False
        self._spacy_nlp = None  # Lazy-loaded spaCy model for fallback

        # Skip SentenceTransformer loading if disabled - will use spaCy fallback
        if DISABLE_SEMANTIC_MATCHING:
            print("[SemanticMatcher] SentenceTransformer disabled - using spaCy word vectors")
            self.model = None
            self.util = None
            self.available = False
            return

        # Use shared model from global registry (loaded once at app startup)
        from . import get_semantic_model, get_sentence_transformer_util

        self.model = get_semantic_model()
        self.util = get_sentence_transformer_util()
        self.available = self.model is not None and self.util is not None

        # Only load CodeBERT if explicitly enabled (saves ~340MB RAM)
        if FEATURE_CODEBERT and self.available:
            try:
                from sentence_transformers import SentenceTransformer
                self.code_model = SentenceTransformer('microsoft/codebert-base')
                self.use_codebert = True
                print("  CodeBERT loaded for code-aware similarity")
            except Exception:
                self.use_codebert = False

    def _get_spacy_nlp(self):
        """Lazy-load spaCy model for word vector fallback."""
        if self._spacy_nlp is None:
            from . import get_spacy_model
            self._spacy_nlp = get_spacy_model()
        return self._spacy_nlp

    def _compute_spacy_similarity(self, query: str, method_text: str) -> float:
        """
        Compute similarity using spaCy word vectors (lightweight fallback).
        Works with en_core_web_md or en_core_web_lg models.
        """
        nlp = self._get_spacy_nlp()
        if nlp is None:
            return 0.0

        try:
            doc1 = nlp(query.lower())
            doc2 = nlp(method_text.lower())

            # Check if vectors are available (md/lg models have vectors, sm doesn't)
            if not doc1.has_vector or not doc2.has_vector:
                return 0.0

            similarity = doc1.similarity(doc2)
            # Clamp to 0-1 range (spaCy can return slightly negative values)
            return max(0.0, min(1.0, similarity))
        except Exception:
            return 0.0

    def initialize(self, methods: List["MethodInfo"]) -> None:
        """
        Pre-compute embeddings for all methods at initialization.
        This avoids re-encoding method texts on every request.
        """
        if not self.available or self._initialized:
            return

        print("  Pre-computing method embeddings...")

        # Batch encode all method texts at once (much faster than sequential)
        method_texts = [m.to_searchable_text().lower() for m in methods]
        method_names = [m.name for m in methods]

        # Encode all at once using batch processing
        all_embeddings = self.model.encode(method_texts, show_progress_bar=False)

        # Store in dictionary for O(1) lookup
        for name, embedding in zip(method_names, all_embeddings):
            self.method_embeddings[name] = embedding

        # Also pre-compute CodeBERT embeddings if available
        if self.use_codebert:
            print("  Pre-computing CodeBERT embeddings...")
            code_embeddings = self.code_model.encode(method_names, show_progress_bar=False)
            for name, embedding in zip(method_names, code_embeddings):
                self.method_embeddings_code[name] = embedding

        self._initialized = True
        print(f"  Cached embeddings for {len(methods)} methods")

    def _get_query_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a query text with LRU caching."""
        # Use a tuple key for lru_cache compatibility
        return self._cached_encode(text)

    @lru_cache(maxsize=1000)
    def _cached_encode(self, text: str) -> np.ndarray:
        """LRU-cached encoding for query texts."""
        return self.model.encode([text], show_progress_bar=False)[0]

    @lru_cache(maxsize=1000)
    def _cached_encode_code(self, text: str) -> np.ndarray:
        """LRU-cached encoding for code queries."""
        if not self.use_codebert:
            return np.array([])
        return self.code_model.encode([text], show_progress_bar=False)[0]

    def compute_similarity(self, query: str, method_text: str, method_name: str = None) -> float:
        """
        Compute semantic similarity between query and method.

        If method_name is provided and embeddings are pre-computed, uses cached embedding.
        Otherwise falls back to encoding on-the-fly.
        Falls back to spaCy word vectors if SentenceTransformer is disabled.
        """
        if not self.available:
            # Fallback to spaCy word vectors (lightweight alternative)
            return self._compute_spacy_similarity(query, method_text)

        # Get query embedding (cached via LRU)
        query_embedding = self._get_query_embedding(query.lower())

        # Get method embedding (pre-computed if available)
        if method_name and method_name in self.method_embeddings:
            method_embedding = self.method_embeddings[method_name]
        else:
            # Fallback: encode on-the-fly
            method_embedding = self.model.encode([method_text.lower()], show_progress_bar=False)[0]

        similarity = self.util.cos_sim(query_embedding, method_embedding)
        return float(similarity[0][0])

    def compute_code_similarity(self, command: str, method_name: str) -> float:
        """Compute similarity using code-aware model with caching."""
        if not self.use_codebert:
            return 0.0

        try:
            # Get query embedding (cached via LRU)
            query_embedding = self._cached_encode_code(command)

            # Get method embedding (pre-computed if available)
            if method_name in self.method_embeddings_code:
                method_embedding = self.method_embeddings_code[method_name]
            else:
                # Fallback: encode on-the-fly
                method_embedding = self.code_model.encode([method_name], show_progress_bar=False)[0]

            similarity = self.util.cos_sim(query_embedding, method_embedding)
            return float(similarity[0][0])
        except Exception:
            return 0.0

    def clear_cache(self) -> None:
        """Clear all caches (useful for testing or reinitialization)."""
        self.method_embeddings.clear()
        self.method_embeddings_code.clear()
        self._cached_encode.cache_clear()
        self._cached_encode_code.cache_clear()
        self._initialized = False
