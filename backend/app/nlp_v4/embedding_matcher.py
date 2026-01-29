"""
Embedding Matcher - Core semantic matching using all-mpnet-base-v2

Embeds method descriptions at initialization time, then matches
user queries by cosine similarity at request time.
"""

from typing import List, Tuple, Optional
from functools import lru_cache

import numpy as np

from .models import MethodInfo
from .method_describer import describe_methods


class EmbeddingMatcher:
    def __init__(self):
        from . import get_embedding_model, get_sentence_transformer_util

        self.model = get_embedding_model()
        self.util = get_sentence_transformer_util()
        self.method_embeddings = None
        self.method_names: List[str] = []
        self.method_descriptions: List[str] = []
        self._initialized = False

    def initialize(
        self,
        methods: List[MethodInfo],
        class_name: Optional[str] = None,
    ) -> None:
        """Pre-compute embeddings for all method descriptions."""
        if not self.model:
            raise RuntimeError("SentenceTransformer model not available")

        self.method_names = [m.name for m in methods]
        self.method_descriptions = describe_methods(methods, class_name)

        # Batch encode all descriptions at once
        self.method_embeddings = self.model.encode(
            self.method_descriptions,
            convert_to_tensor=True,
            show_progress_bar=False,
        )
        self._initialized = True

        print(f"[EmbeddingMatcher] Embedded {len(methods)} methods:")
        for name, desc in zip(self.method_names, self.method_descriptions):
            print(f"  {name}: \"{desc}\"")

    def match(self, query: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        """
        Match a query against all method embeddings.

        Returns:
            List of (method_name, similarity_score, description) tuples,
            sorted by descending similarity.
        """
        if not self._initialized:
            raise RuntimeError("EmbeddingMatcher not initialized")

        # Encode query
        print(f"[EmbeddingMatcher] Query: \"{query}\"")
        query_embedding = self.model.encode(query, convert_to_tensor=True)

        # Cosine similarity against all methods
        similarities = self.util.cos_sim(query_embedding, self.method_embeddings)[0]

        # Debug: show all scores
        print(f"[EmbeddingMatcher] Similarity scores:")
        for i, score in enumerate(similarities):
            print(f"  {float(score)*100:.1f}% - {self.method_names[i]}: \"{self.method_descriptions[i][:80]}\"")

        # Build results sorted by similarity
        results = []
        for i, score in enumerate(similarities):
            results.append((
                self.method_names[i],
                float(score),
                self.method_descriptions[i],
            ))

        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k] if top_k else results
