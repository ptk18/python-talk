from typing import List
from .models import WordInfo, GrammarExtraction
from .dictionary_lookup import is_direction_word, is_color_word

# Particles detected via WordNet check for preposition/adverb senses
PARTICLE_LEMMAS = {"up", "down", "on", "off", "to", "in", "out", "over", "back"}


def extract_grammar(words: List[WordInfo]) -> GrammarExtraction:
    result = GrammarExtraction()
    verb_idx = -1
    pending_adjectives = []  # Track adjectives before nouns

    if words and words[0].pos != "verb":
        result.verb = words[0].lemma
        result.verb_synonyms = list(words[0].synonyms) if words[0].synonyms else []
        verb_idx = 0

    for i, w in enumerate(words):
        original_lower = w.original.lower()
        lemma_lower = w.lemma.lower()

        if w.pos == "verb" and (result.verb is None or i == 0):
            result.verb = w.lemma
            result.verb_synonyms = list(w.synonyms)
            verb_idx = i
        elif w.pos == "adverb" and is_direction_word(original_lower):
            # Direction adverbs (forward, backward, left, right) - add to verb synonyms
            clean = original_lower.rstrip("s") if original_lower.endswith("wards") else original_lower
            result.verb_synonyms.append(clean)
            # Also add normalized form (backwards -> backward)
            if clean.endswith("ward"):
                result.verb_synonyms.append(clean + "s")
        elif is_direction_word(original_lower):
            # Fallback: direction word detected by other POS
            clean = original_lower.rstrip("s") if original_lower.endswith("wards") else original_lower
            result.verb_synonyms.append(clean)
        elif lemma_lower in PARTICLE_LEMMAS and result.particle is None and verb_idx >= 0:
            result.particle = w.lemma
        elif w.pos == "adjective" and i > 0:
            # Check if it's a color - store as modifier
            if is_color_word(lemma_lower):
                result.modifiers.append(w.lemma)
            else:
                pending_adjectives.append(w.lemma)
        elif w.pos == "noun" and i > verb_idx and result.object is None:
            # Skip directional nouns (they were added to verb_synonyms)
            if not is_direction_word(original_lower):
                result.object = w.lemma
                result.object_synonyms = list(w.synonyms)
                # Clear pending adjectives - they modified this noun
                pending_adjectives = []
        elif w.pos == "NUMBER":
            result.numbers.append(w.original)

    # Any remaining adjectives are modifiers (e.g., colors without noun)
    result.modifiers.extend(pending_adjectives)

    return result
