import re
from typing import Dict, List, Optional, Any
from .intent_parser import Intent
from .pos_tagger import Token

NOISE_WORDS = {
    "the", "a", "an", "to", "from", "in", "on", "at",
    "of", "for", "with", "my", "your", "our", "their"
}


def extract_parameters(intent: Intent) -> Dict[str, Any]:
    """Extract parameters from intent"""
    numbers = extract_numbers(intent.text)
    strings = extract_strings(intent.tokens, intent.verb)
    boolean = extract_boolean(intent.text)

    return {
        "numbers": numbers,
        "strings": strings,
        "boolean": boolean
    }


def extract_numbers(text: str) -> List[float]:
    """Extract all numeric values from text"""
    pattern = r'\d+(?:\.\d+)?'
    matches = re.findall(pattern, text)

    numbers = []
    for match in matches:
        if '.' in match:
            numbers.append(float(match))
        else:
            numbers.append(int(match))

    return numbers


def extract_strings(tokens: List[Token], verb: str) -> List[str]:
    """Extract string values after verb, excluding noise words"""
    strings = []
    verb_found = False

    for token in tokens:
        if verb and token.lemma == verb:
            verb_found = True
            continue

        if verb_found:
            if token.text.lower() not in NOISE_WORDS and token.pos != "NUM":
                if not token.text.isdigit():
                    strings.append(token.text.lower())

    return strings


def extract_boolean(text: str) -> Optional[bool]:
    """Detect boolean state from keywords"""
    text_lower = text.lower()

    if any(kw in text_lower for kw in ["on", "true", "yes", "enable"]):
        return True

    if any(kw in text_lower for kw in ["off", "false", "no", "disable"]):
        return False

    return None
