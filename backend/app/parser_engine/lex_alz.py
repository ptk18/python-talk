import re
import nltk
from nltk.corpus import wordnet as wn
from typing import List, Dict
# from num2words import num2words
import ssl

# from word2number import w2n

# -----------------------------
# English word → digit mapping
# -----------------------------
WORD_TO_NUMBER = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
}

def _words_to_numbers(sentence: str) -> str:
    """Replace English number words with their digit equivalents."""
    def _replace(match):
        return WORD_TO_NUMBER[match.group(0).lower()]
    pattern = r'\b(?:' + '|'.join(WORD_TO_NUMBER.keys()) + r')\b'
    return re.sub(pattern, _replace, sentence, flags=re.IGNORECASE)

# -----------------------------
# Penn Treebank tag → simple POS
# -----------------------------
def penn_to_simple(tag: str, word: str) -> str:
    if word.isdigit():
        return "NUMBER"
    if tag.startswith("NN"):
        return "NOUN"
    if tag.startswith("VB"):
        return "VERB"
    if tag.startswith("JJ"):
        return "ADJECTIVE"
    if tag.startswith("RB"):
        return "ADVERB"
    if tag == "PRP$":
        return "determiner"
    if tag == "PRP":
        return "pronoun"
    if tag == "DT":
        return "determiner"
    if tag in ("IN", "RP"):
        return "preposition"
    if tag == "CC":
        return "conjunction"
    if tag == "CD": # Cardinal number
        return "NUMBER"
    if tag in (".", ",", ":", "(", ")", "''", "``"):
        return "punctuation"
    return "UNKNOWN"

def setup_nltk():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    resources = ['punkt_tab', 'averaged_perceptron_tagger_eng', 'wordnet', 'omw-1.4']
    for r in resources:
        try:
            nltk.data.find(f'tokenizers/{r}')
        except LookupError:
            try:
                nltk.download(r, quiet=True)
            except:
                pass


# -----------------------------
# Simple POS → WordNet POS
# -----------------------------
POS_TO_WN = {
    "NOUN": wn.NOUN,
    "VERB": wn.VERB,
    "ADJECTIVE": wn.ADJ,
    "ADVERB": wn.ADV,
}


def get_synonyms(word: str, pos: str, limit: int = 10) -> List[str]:
    if pos == "NUMBER":
        return []

    wn_pos = POS_TO_WN.get(pos)
    synsets = wn.synsets(word, pos=wn_pos) if wn_pos else wn.synsets(word)

    synonyms = set()
    for syn in synsets:
        for lemma in syn.lemmas():
            name = lemma.name().replace("_", " ").lower()
            if name != word.lower():
                synonyms.add(name)

    return sorted(synonyms)[:limit]


def analyze_sentence(sentence: str) -> List[Dict]:
    sentence = _words_to_numbers(sentence)
    tokens = nltk.word_tokenize(sentence)
    tagged = nltk.pos_tag(tokens)

    result = []
    for word, penn_tag in tagged:
        simple_pos = penn_to_simple(penn_tag, word)
        
        # Get synonyms only for key types
        syns = []
        if simple_pos in ["NOUN", "VERB", "ADVERB", "ADJECTIVE"]:
            syns = get_synonyms(word, simple_pos)

        result.append({
            "word": word,
            "POS": simple_pos,
            "synonyms": syns
        })

    return result

if __name__ == "__main__":
    # Example usage
    import json
    setup_nltk()
    sentence = "take 3 steps slowly"
    print(json.dumps(analyze_sentence(sentence), indent=2))