from typing import List, Optional, Tuple
from .models import GrammarExtraction, MethodInfo, MatchResult, MatchType
from .dictionary_lookup import is_direction_word

LOG_PREFIX = "[NLP]"
CONFIDENCE_THRESHOLD = 0.35  # Minimum confidence to accept a match


def match_word(input_word: str, input_syns: List[str], target: str, target_syns: List[str], target_forms: List[str]) -> Tuple[MatchType, bool]:
    input_lower = input_word.lower()
    target_lower = target.lower()

    if input_lower == target_lower:
        return MatchType.EXACT, True

    if input_lower in [f.lower() for f in target_forms]:
        return MatchType.INFLECTION, True

    if target_lower in [s.lower() for s in input_syns]:
        is_direct = is_direction_word(target_lower)
        return MatchType.SYNONYM, is_direct

    input_set = set(s.lower() for s in input_syns)
    target_set = set(s.lower() for s in target_syns)
    if input_set & target_set:
        return MatchType.SYNONYM, False

    return MatchType.NONE, False


def match_method(grammar: GrammarExtraction, method: MethodInfo) -> Optional[MatchResult]:
    if not grammar.verb:
        return None

    verb_match, verb_direct = match_word(
        grammar.verb,
        grammar.verb_synonyms,
        method.verb,
        method.verb_synonyms,
        method.verb_forms
    )

    obj_used_as_verb = False
    if verb_match == MatchType.NONE and grammar.object:
        verb_match, verb_direct = match_word(
            grammar.object,
            grammar.object_synonyms,
            method.verb,
            method.verb_synonyms,
            method.verb_forms
        )
        if verb_match != MatchType.NONE:
            obj_used_as_verb = True

    if verb_match == MatchType.NONE:
        return None

    obj_match = MatchType.NONE
    if method.object:
        if grammar.object and not obj_used_as_verb:
            obj_match, _ = match_word(
                grammar.object,
                grammar.object_synonyms,
                method.object,
                method.object_synonyms,
                method.object_forms
            )
            if obj_match == MatchType.NONE:
                return None
        else:
            return None
    else:
        if grammar.object is None or obj_used_as_verb:
            obj_match = MatchType.EXACT

    particle_match = False
    if method.particle:
        if grammar.particle == method.particle:
            particle_match = True
        else:
            return None
    else:
        particle_match = True

    confidence = 0.0
    if verb_match == MatchType.EXACT:
        confidence += 0.5
    elif verb_match == MatchType.INFLECTION:
        confidence += 0.45
    elif verb_match == MatchType.SYNONYM:
        # Boost confidence if direction word in verb_synonyms matches direction command
        if verb_direct and is_direction_word(method.name):
            confidence += 0.5  # Treat as near-exact match
        else:
            confidence += 0.45 if verb_direct else 0.35

    if obj_match == MatchType.EXACT:
        confidence += 0.3
    elif obj_match == MatchType.INFLECTION:
        confidence += 0.25
    elif obj_match == MatchType.SYNONYM:
        confidence += 0.2

    if particle_match and method.particle:
        confidence += 0.2

    # Bonus for direction commands without object (cleaner command pattern)
    if is_direction_word(method.name) and grammar.object is None:
        confidence += 0.1

    params = {}
    if method.params and grammar.numbers:
        for i, p in enumerate(method.params):
            if i < len(grammar.numbers):
                val = grammar.numbers[i]
                if p["type"] == "int":
                    params[p["name"]] = int(float(val))
                elif p["type"] == "float":
                    params[p["name"]] = float(val)
                else:
                    params[p["name"]] = val

    if method.params:
        for p in method.params:
            if p["type"] == "str" and p["name"] not in params:
                if grammar.modifiers:
                    params[p["name"]] = grammar.modifiers[0]

    param_str = ", ".join(f"{v}" for v in params.values())
    executable = f"{method.name}({param_str})"

    return MatchResult(
        success=True,
        method=method.name,
        confidence=confidence,
        verb_match=verb_match,
        object_match=obj_match,
        particle_match=particle_match,
        params=params,
        executable=executable
    )


def find_best_match(grammar: GrammarExtraction, methods: List[MethodInfo]) -> MatchResult:
    results = []

    for method in methods:
        result = match_method(grammar, method)
        if result:
            results.append(result)

    if not results:
        print(f"{LOG_PREFIX} Match: No matching method found")
        return MatchResult(success=False)

    results.sort(key=lambda r: r.confidence, reverse=True)
    best = results[0]
    top_3 = [(r.method, f"{r.confidence:.2f}") for r in results[:3]]
    print(f"{LOG_PREFIX} Match: {best.method} (verb={best.verb_match.name}, obj={best.object_match.name}) | Top 3: {top_3}")

    # Reject low-confidence matches
    if best.confidence < CONFIDENCE_THRESHOLD:
        print(f"{LOG_PREFIX} Rejected: confidence {best.confidence:.2f} < threshold {CONFIDENCE_THRESHOLD}")
        return MatchResult(success=False, error=f"Low confidence match ({best.confidence:.2f})")

    return best
