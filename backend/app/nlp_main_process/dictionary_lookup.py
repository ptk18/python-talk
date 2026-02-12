from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet as wn
from functools import lru_cache
from typing import List, Set

_lemmatizer = WordNetLemmatizer()

POS_MAP = {
    "verb": wn.VERB,
    "noun": wn.NOUN,
    "adjective": wn.ADJ,
    "adverb": wn.ADV,
}


@lru_cache(maxsize=1)
def _get_direction_synsets() -> Set[str]:
    """Get direction-related synset names for hierarchy checking."""
    direction_roots = set()
    # Root synsets for direction concepts in WordNet
    root_synset_names = ["direction.n.01", "direction.n.04", "way.n.06"]
    for synset_name in root_synset_names:
        try:
            synset = wn.synset(synset_name)
            direction_roots.add(synset.name())
            # Add all hyponyms (more specific direction concepts)
            for hypo in synset.closure(lambda s: s.hyponyms()):
                direction_roots.add(hypo.name())
        except Exception:
            pass
    return direction_roots


@lru_cache(maxsize=1)
def _get_direction_words() -> Set[str]:
    """Build direction word set from WordNet synsets and their lemmas."""
    words = set()

    # Get words from direction noun synsets
    for synset_name in _get_direction_synsets():
        try:
            synset = wn.synset(synset_name)
            for lemma in synset.lemmas():
                words.add(lemma.name().lower().replace("_", " "))
        except Exception:
            pass

    # Get directional adverbs by finding adverb synsets with directional definitions
    # Use lemmas from direction synsets as definition keywords
    direction_keywords = {"direction", "toward", "away", "front", "back", "side"}
    for synset_name in list(_get_direction_synsets())[:10]:  # Sample to get keywords
        try:
            for lemma in wn.synset(synset_name).lemmas():
                word = lemma.name().lower()
                if len(word) > 2:
                    direction_keywords.add(word)
        except Exception:
            pass

    # Find adverbs whose definitions contain direction keywords
    for synset in wn.all_synsets(pos=wn.ADV):
        definition = synset.definition().lower()
        if any(kw in definition for kw in direction_keywords):
            for lemma in synset.lemmas():
                name = lemma.name().lower().replace("_", " ")
                if len(name) < 15:
                    words.add(name)

    return words


@lru_cache(maxsize=1)
def _get_color_synsets() -> Set[str]:
    """Get color-related synset names for checking."""
    color_roots = set()
    try:
        # chromatic_color.n.01 is parent of most colors
        color_synset = wn.synset("chromatic_color.n.01")
        color_roots.add(color_synset.name())
        for hypo in color_synset.hyponyms():
            color_roots.add(hypo.name())
            for h2 in hypo.hyponyms():
                color_roots.add(h2.name())
    except Exception:
        pass
    return color_roots


@lru_cache(maxsize=200)
def is_color_word(word: str) -> bool:
    """Check if a word is a color using WordNet hierarchy."""
    word_lower = word.lower()
    color_synsets = _get_color_synsets()
    for syn in wn.synsets(word_lower, pos=wn.NOUN):
        if syn.name() in color_synsets:
            return True
        # Check hypernyms
        for hyper in syn.hypernyms():
            if "color" in hyper.name() or "colour" in hyper.name():
                return True
    return False


@lru_cache(maxsize=200)
def is_direction_word(word: str) -> bool:
    """Check if a word is directional using WordNet semantic hierarchy."""
    word_lower = word.lower()

    # Check against dynamically built direction word set
    if word_lower in _get_direction_words():
        return True

    # Also check synset hierarchy for nouns
    direction_synsets = _get_direction_synsets()
    for syn in wn.synsets(word_lower):
        if syn.name() in direction_synsets:
            return True
        for hypernym in syn.closure(lambda s: s.hypernyms()):
            if hypernym.name() in direction_synsets:
                return True

    return False


def get_lemma(word: str, pos: str) -> str:
    wn_pos = POS_MAP.get(pos)
    if wn_pos:
        return _lemmatizer.lemmatize(word.lower(), wn_pos)
    return word.lower()


@lru_cache(maxsize=500)
def get_synonyms(word: str, pos: str, limit: int = 6, max_synsets: int = 2) -> List[str]:
    """Get synonyms from WordNet, limited to first N synsets (most common meanings)."""
    wn_pos = POS_MAP.get(pos)
    synsets = wn.synsets(word, pos=wn_pos) if wn_pos else wn.synsets(word)
    synonyms = set()
    # Only use first max_synsets (most relevant meanings)
    for syn in synsets[:max_synsets]:
        for lemma in syn.lemmas():
            name = lemma.name().replace("_", " ").lower()
            if name != word.lower():
                synonyms.add(name)
    return sorted(synonyms)[:limit]


def get_inflections(word: str, pos: str) -> List[str]:
    word = word.lower()
    forms = {word}

    if pos == "verb":
        forms.add(word + "s")
        forms.add(word + "ed")
        forms.add(word + "ing")
        if word.endswith("e"):
            forms.add(word + "d")
            forms.add(word[:-1] + "ing")
        if word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
            forms.add(word[:-1] + "ies")
            forms.add(word[:-1] + "ied")
    elif pos == "noun":
        forms.add(word + "s")
        if word.endswith(("s", "sh", "ch", "x", "z")):
            forms.add(word + "es")
        elif word.endswith("y") and len(word) > 1 and word[-2] not in "aeiou":
            forms.add(word[:-1] + "ies")
    elif pos == "adverb":
        if word.endswith("ward"):
            forms.add(word + "s")

    return list(forms)
