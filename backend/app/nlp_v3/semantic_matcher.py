"""Semantic similarity matching using sentence-transformers"""


class LocalSemanticMatcher:
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer, util
            # Use faster model with similar performance
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.util = util
            self.available = True
            self.use_codebert = False

            # Try to load CodeBERT for code-specific matching
            try:
                self.code_model = SentenceTransformer('microsoft/codebert-base')
                self.use_codebert = True
                print("  CodeBERT loaded for code-aware similarity")
            except Exception:
                self.use_codebert = False

        except ImportError:
            self.available = False
            self.use_codebert = False

    def compute_similarity(self, text1: str, text2: str) -> float:
        if not self.available:
            raise RuntimeError("Sentence Transformer not available - no fallbacks allowed in POC")

        embeddings = self.model.encode([text1, text2])
        similarity = self.util.cos_sim(embeddings[0], embeddings[1])
        return float(similarity[0][0])

    def compute_code_similarity(self, command: str, method_name: str) -> float:
        """Compute similarity using code-aware model"""
        if not self.use_codebert:
            return 0.0

        try:
            # Format for CodeBERT (works better with natural + code pairs)
            embeddings = self.code_model.encode([command, method_name])
            similarity = self.util.cos_sim(embeddings[0], embeddings[1])
            return float(similarity[0][0])
        except Exception:
            return 0.0
