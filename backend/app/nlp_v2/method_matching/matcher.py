from dataclasses import dataclass
from typing import List
from app.nlp_v2.extract_catalog_from_source_code.catalog import Catalog, MethodInfo
from app.nlp_v2.semantic_parsing.intent_parser import Intent


@dataclass
class MatchResult:
    """Result of matching intent to method"""
    method_info: MethodInfo
    score: float
    matched_component: str


def compute_similarity(intent_verb: str, method_name: str) -> float:
    """Compute similarity score between intent verb and method name"""
    verb = normalize_string(intent_verb)
    method = normalize_string(method_name.replace('_', ' '))

    if verb == method:
        return 100.0

    if verb in method:
        return 80.0

    if method in verb:
        return 70.0

    verb_words = verb.split()
    method_words = method.split()
    overlap = compute_word_overlap(verb_words, method_words)

    return overlap * 60


def find_matching_methods(intent: Intent, catalog: Catalog, class_name: str) -> List[MatchResult]:
    """Find methods matching the intent"""
    methods = catalog.get_methods(class_name)
    results = []

    for method in methods:
        score = compute_similarity(intent.verb, method.name)

        if score > 30:
            results.append(MatchResult(
                method_info=method,
                score=score,
                matched_component=f"verb:{intent.verb}"
            ))

    results.sort(key=lambda x: x.score, reverse=True)
    return results[:5]


def normalize_string(text: str) -> str:
    """Lowercase and clean string"""
    return text.lower().strip()


def compute_word_overlap(words1: List[str], words2: List[str]) -> float:
    """Calculate overlap ratio between two word lists"""
    if not words1 or not words2:
        return 0.0

    set1 = set(words1)
    set2 = set(words2)
    common = set1.intersection(set2)

    max_len = max(len(words1), len(words2))
    return len(common) / max_len if max_len > 0 else 0.0
