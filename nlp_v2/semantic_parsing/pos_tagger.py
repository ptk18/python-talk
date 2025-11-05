from dataclasses import dataclass
from typing import List
import spacy

nlp = None


def _load_spacy_model():
    """Load spacy model once and reuse"""
    global nlp
    if nlp is None:
        nlp = spacy.load("en_core_web_sm")
    return nlp


@dataclass
class Token:
    """Token with POS tag information"""
    text: str
    pos: str
    lemma: str
    is_stop: bool


def tag_sentence(text: str) -> List[Token]:
    """Tokenize and tag input text with POS information"""
    model = _load_spacy_model()
    doc = model(text)

    tokens = []
    for token in doc:
        tokens.append(Token(
            text=token.text,
            pos=token.pos_,
            lemma=token.lemma_,
            is_stop=token.is_stop
        ))

    return tokens
