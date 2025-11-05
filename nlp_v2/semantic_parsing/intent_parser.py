from dataclasses import dataclass
from typing import Optional, List
from .pos_tagger import Token, tag_sentence

QUERY_VERBS = {"get", "show", "check", "display", "find", "list", "count", "is", "are", "has", "have"}


@dataclass
class Intent:
    """Parsed intent from natural language"""
    text: str
    verb: str
    subject: Optional[str]
    intent_type: str
    tokens: List[Token]


def parse_intent(text: str) -> Intent:
    """Parse natural language into structured intent"""
    tokens = tag_sentence(text)
    verb = find_main_verb(tokens)
    subject = find_subject(tokens)

    intent_type = "query" if verb and verb in QUERY_VERBS else "action"

    return Intent(
        text=text,
        verb=verb or "",
        subject=subject,
        intent_type=intent_type,
        tokens=tokens
    )


def find_main_verb(tokens: List[Token]) -> Optional[str]:
    """Find and return main verb lemma"""
    for token in tokens:
        if token.pos in ["VERB", "AUX"]:
            return token.lemma

    # Fallback: if first token is a noun, it might be an imperative verb
    if tokens and tokens[0].pos == "NOUN":
        return tokens[0].lemma

    return None


def find_subject(tokens: List[Token]) -> Optional[str]:
    """Find first noun token as subject"""
    for token in tokens:
        if token.pos == "NOUN":
            return token.text
    return None
