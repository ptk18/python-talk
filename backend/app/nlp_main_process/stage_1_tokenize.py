import nltk
from typing import List
from .models import WordInfo
from .dictionary_lookup import get_lemma, get_synonyms, get_inflections, is_direction_word


def penn_to_simple(tag: str, word: str) -> str:
    if word.isdigit() or tag == "CD":
        return "NUMBER"
    if tag.startswith("NN"):
        return "noun"
    if tag.startswith("VB"):
        return "verb"
    if tag.startswith("JJ"):
        return "adjective"
    if tag.startswith("RB"):
        return "adverb"
    if tag in ("DT", "PRP$"):
        return "determiner"
    if tag == "IN":
        return "preposition"
    if tag in (".", ",", ":", "(", ")", "''", "``"):
        return "punctuation"
    return "other"


def analyze_sentence(sentence: str) -> List[WordInfo]:
    tokens = nltk.word_tokenize(sentence)
    tagged = nltk.pos_tag(tokens)

    result = []
    for i, (word, penn_tag) in enumerate(tagged):
        pos = penn_to_simple(penn_tag, word)
        word_lower = word.lower()

        # Fix POS using WordNet sense check
        from nltk.corpus import wordnet as wn

        # First word in command context is likely a verb
        if i == 0 and pos == "noun":
            if wn.synsets(word_lower, pos=wn.VERB):
                pos = "verb"

        # Fix direction words - they should be adverbs in command context
        if is_direction_word(word_lower):
            pos = "adverb"
        # Fix mistagged nouns (e.g., "turtle" tagged as adverb)
        elif pos in ("adverb", "other") and wn.synsets(word_lower, pos=wn.NOUN):
            # Check if noun sense is more common than current sense
            noun_synsets = wn.synsets(word_lower, pos=wn.NOUN)
            other_synsets = wn.synsets(word_lower)
            if noun_synsets and len(noun_synsets) >= len(other_synsets) // 2:
                pos = "noun"

        lemma = get_lemma(word, pos) if pos in ("noun", "verb", "adjective", "adverb") else word.lower()

        if pos in ("noun", "verb", "adjective", "adverb"):
            synonyms = get_synonyms(lemma, pos)
            inflections = get_inflections(lemma, pos)
        else:
            synonyms = []
            inflections = []

        result.append(WordInfo(
            original=word,
            lemma=lemma,
            pos=pos,
            synonyms=synonyms,
            inflections=inflections
        ))

    return result
