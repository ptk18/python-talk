import re
import math
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass


@dataclass
class MatchResult:
    method_info: any
    score: float
    matched_phrase: str


class RetrievalIndex:
    def __init__(self, noise_words: Set[str] = None):
        self.phrase_to_methods: Dict[str, List[Tuple[any, str]]] = defaultdict(list)
        self.word_df: Counter = Counter()
        self.total_docs = 0
        self.all_methods: List = []
        self.noise_words = noise_words if noise_words else set()

    def index_methods(self, methods: List):
        self.all_methods = methods
        self.phrase_to_methods.clear()
        self.word_df.clear()
        self.total_docs = 0

        for method_info in methods:
            for phrase in method_info.surface_forms:
                normalized = self._normalize(phrase)
                self.phrase_to_methods[normalized].append((method_info, phrase))
                self.total_docs += 1

                words = set(normalized.split())
                for word in words:
                    self.word_df[word] += 1

    def search(self, query: str, class_name: Optional[str] = None, top_k: int = 5,
               min_score_threshold: float = 10.0) -> List[MatchResult]:
        normalized_query = self._normalize(query)
        query_words = set(w for w in normalized_query.split()
                        if w not in self.noise_words and not w.isdigit())

        scored_results: List[Tuple[any, float, str]] = []

        for phrase, method_list in self.phrase_to_methods.items():
            for method_info, original_phrase in method_list:
                if class_name and method_info.class_name != class_name:
                    continue

                score = self._compute_similarity(normalized_query, query_words, phrase)
                if score >= min_score_threshold:
                    scored_results.append((method_info, score, original_phrase))

        scored_results.sort(key=lambda x: x[1], reverse=True)

        method_best_scores: Dict[str, Tuple[any, float, str]] = {}
        for method_info, score, phrase in scored_results:
            key = f"{method_info.class_name}.{method_info.name}"
            if key not in method_best_scores or score > method_best_scores[key][1]:
                method_best_scores[key] = (method_info, score, phrase)

        results = [
            MatchResult(method_info=m, score=s, matched_phrase=p)
            for m, s, p in method_best_scores.values()
        ]

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    def _compute_similarity(self, query: str, query_words: Set[str], phrase: str) -> float:
        normalized_query = query.lower().strip()
        normalized_phrase = phrase.lower().strip()
        clean_query_words = {w for w in query_words if w not in self.noise_words and not w.isdigit()}
        phrase_words = set(normalized_phrase.split())

        if normalized_query == normalized_phrase:
            return 100.0

        clean_query = ' '.join(w for w in normalized_query.split() if w not in self.noise_words and not w.isdigit())
        if clean_query and clean_query == normalized_phrase:
            return 95.0

        if clean_query and clean_query in normalized_phrase:
            if normalized_phrase.startswith(clean_query):
                return 85.0
            return 75.0

        if normalized_phrase in normalized_query:
            # Give bonus for longer phrases
            length_bonus = len(normalized_phrase.split()) * 5
            return 60.0 + length_bonus

        if len(phrase_words) > 1:
            query_tokens = normalized_query.split()
            phrase_tokens = normalized_phrase.split()
            for i in range(len(query_tokens) - len(phrase_tokens) + 1):
                if query_tokens[i:i+len(phrase_tokens)] == phrase_tokens:
                    return 90.0

        common_words = clean_query_words & phrase_words
        if not common_words:
            return 0.0

        score = 0.0
        for word in common_words:
            idf = math.log((self.total_docs + 1) / (self.word_df[word] + 1)) + 1
            score += idf

        coverage_query = len(common_words) / len(clean_query_words) if clean_query_words else 0.0
        coverage_phrase = len(common_words) / len(phrase_words) if phrase_words else 0.0
        avg_coverage = (coverage_query + coverage_phrase) / 2
        coverage_multiplier = 1 + (avg_coverage ** 2)
        score = score * coverage_multiplier

        if len(common_words) > 1:
            multi_word_bonus = len(common_words) * 1.5
            score += multi_word_bonus

        score = score / max(len(clean_query_words), len(phrase_words))
        return score * 10
