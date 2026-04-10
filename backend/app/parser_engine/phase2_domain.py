# phase2_domain.py
import ast
import os
from typing import Dict, List, Set, Optional, Any, Tuple
import re
import time

# from lex_alz import get_synonyms

DOMAIN_CACHE: Dict[str, Dict[str, Any]] = {}

# -----------------------------
# Helpers
# -----------------------------
def split_snake_case(name: str) -> List[str]:
    return name.lower().split("_")

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


def normalize(word: str) -> str:
    return word.lower().strip()

def extract_phrases_from_docstring(doc: str) -> List[str]:
    """
    Pull phrases from a docstring section like:

        Phrases: back, go back, move back, backward,
                 reverse, step back, go backwards.

    Returns normalized phrases (lowercase).
    """
    if not doc:
        return []

    # find "Phrases:" block until blank line or "Args:" or end
    m = re.search(r"(?is)\bphrases?\s*:\s*(.*?)(?:\n\s*\n|\n\s*args\s*:|$)", doc)
    if not m:
        return []

    blob = m.group(1)

    # split by commas and newlines
    raw = re.split(r"[,\n]", blob)
    phrases = []
    for x in raw:
        p = x.strip().lower()
        if not p:
            continue
        # remove trailing punctuation
        p = re.sub(r"[.\;:]+$", "", p).strip()
        if p:
            phrases.append(p)

    # de-dup keep order
    seen = set()
    out = []
    for p in phrases:
        if p not in seen:
            seen.add(p)
            out.append(p)

    return out

def _remove_leading_action_words(words: List[str], action: str) -> List[str]:
    action_words = action.replace("_", " ").lower().split()
    i = 0
    while i < len(words) and i < len(action_words) and words[i] == action_words[i]:
        i += 1
    return words[i:]


def _trim_string_fillers(words: List[str], param_name: str) -> List[str]:
    """
    Remove filler endings like:
      hello as text  -> hello
      hello in text  -> hello
      text hello     -> hello   (if user says 'write text hello')
    """
    if not words:
        return words

    p = param_name.lower()

    # remove leading param-name word: "text hello" -> "hello"
    if words and words[0] == p:
        words = words[1:]

    # remove trailing "... as text" / "... in text" / "... for text"
    if len(words) >= 2 and words[-2] in {"as", "in", "for"} and words[-1] == p:
        words = words[:-2]

    # remove trailing lone param-name if user says weird filler
    if words and words[-1] == p:
        words = words[:-1]

    return words

def _remove_leading_phrase(words: List[str], phrase: str) -> List[str]:
    parts = _norm_text(phrase).split()
    if not parts:
        return words
    if words[:len(parts)] == parts:
        return words[len(parts):]
    return words

def _split_device_number_joins(words: List[str]) -> List[str]:
    """Normalize device tokens in word list.

    - lightbulb2 -> lightbulb 2, light1 -> light 1
    - light + bulb -> lightbulb  (merge two-word form)
    - first -> 1, second -> 2  (ordinals to numbers)
    """
    _ordinals = {
        "first": "1", "second": "2", "third": "3", "fourth": "4", "fifth": "5",
        "sixth": "6", "seventh": "7", "eighth": "8", "ninth": "9", "tenth": "10",
        "1st": "1", "2nd": "2", "3rd": "3", "4th": "4", "5th": "5",
    }
    _word_nums = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "ten": "10",
    }
    out: List[str] = []
    i = 0
    while i < len(words):
        w = words[i]
        # merge "light" + "bulb" or "light" + "bulb2" -> "lightbulb" or "lightbulb2"
        if w == "light" and i + 1 < len(words) and (words[i + 1] == "bulb" or re.match(r'^bulb\d+$', words[i + 1])):
            out.append("light" + words[i + 1])  # "lightbulb" or "lightbulb2"
            i += 2
            continue
        # split joined device-number: lightbulb2 -> lightbulb 2
        m = re.match(r'^(lightbulb|light|fan|ac|tv)(\d+)$', w)
        if m:
            out.append(m.group(1))
            out.append(m.group(2))
            i += 1
            continue
        # ordinals to numbers
        if w in _ordinals:
            out.append(_ordinals[w])
            i += 1
            continue
        # English number words to digits
        if w in _word_nums:
            out.append(_word_nums[w])
            i += 1
            continue
        out.append(w)
        i += 1
    return out


def _extract_free_string_value(
    semantic_tokens: List[Dict[str, Any]],
    action: str,
    param_name: str,
    domain: Dict[str, Any]
) -> Optional[str]:
    words: List[str] = []

    for t in semantic_tokens:
        w = _norm_text(str(t.get("word") or ""))
        pos = t.get("POS")

        if not w:
            continue
        if t.get("semantic_type") == "NUMBER":
            continue
        if pos in ("punctuation", "conjunction"):
            continue

        words.append(w)

    if not words:
        return None

    # Normalize joined device-number tokens: lightbulb2 -> lightbulb 2
    words = _split_device_number_joins(words)

    # 1) remove the longest matching docstring phrase for this action FIRST
    action_phrases = (domain.get("ACTIONS", {}).get(action, {}) or {}).get("phrases", []) or []
    action_phrases = sorted(
        action_phrases,
        key=lambda x: len(_norm_text(x).split()),
        reverse=True
    )

    for ph in action_phrases:
        new_words = _remove_leading_phrase(words, ph)
        if new_words != words:
            words = new_words
            break
    else:
        # No leading phrase matched — try removing phrase words found anywhere
        # This handles word-order variants like "change the color of lightbulb 2 red"
        # where the phrase is "change lightbulb 2 color" but user reordered it.
        action_name_words = set(_norm_text(action.replace("_", " ")).split())
        best_remaining = words  # fallback
        best_removed = 0
        for ph in action_phrases:
            ph_words_set = set(_norm_text(ph).split()) | action_name_words
            remaining = [w for w in words if w not in ph_words_set]
            removed = len(words) - len(remaining)
            if removed > best_removed:
                best_removed = removed
                best_remaining = remaining
        if best_removed > 0:
            words = best_remaining

    # 2) then remove leftover generic command verbs and param-name echoes
    pn = param_name.lower()
    param_aliases = {pn}
    if "colour" in pn:
        param_aliases.add(pn.replace("colour", "color"))
    elif "color" in pn:
        param_aliases.add(pn.replace("color", "colour"))
    device_words = {"lightbulb", "light", "fan", "ac", "tv"}
    strip_words = {"set", "change", "make", "use", "to", "as", "in", "with", "into", "for",
                    "the", "a", "an", "of", "on", "my",
                    "color", "colour", "brightness", "temperature", "temp",
                    "speed", "volume", "channel", "swing"} | param_aliases
    # Only strip device words when we're NOT extracting the device param itself
    if param_name.lower() != "device":
        strip_words |= device_words
    # Strip from the front
    while words and (words[0] in strip_words or (re.match(r'^\d+$', words[0]) and param_name.lower() != "device")):
        words = words[1:]

    # Also strip these filler/device words from the end (e.g. trailing "lightbulb" or numbers)
    while words and (words[-1] in strip_words or (re.match(r'^\d+$', words[-1]) and param_name.lower() != "device")):
        words = words[:-1]

    # 4) trim param filler patterns
    words = _trim_string_fillers(words, param_name)

    text = " ".join(words).strip()
    return text or None

# -----------------------------
# Normalization helpers
# -----------------------------
def _norm_text(s: str) -> str:
    """
    Lowercase, trim, collapse whitespace, strip punctuation around words.
    Keeps inner spaces for phrase matching.
    """
    s = (s or "").lower().strip()
    # replace punctuation with space (keep letters/numbers/_)
    s = re.sub(r"[^a-z0-9_]+", " ", s)
    s = " ".join(s.split())
    return s


def normalize_user_input(s: str) -> str:
    """
    Pre-process user input before phrase matching to reduce variant explosion.

    1. Lowercase + strip punctuation (via _norm_text)
    2. Strip filler articles: the, a, an, please, can you, could you
    3. Normalize joined device names: lightbulb1 -> lightbulb 1, light2 -> light 2
    4. Normalize spelling: colour -> color (canonical form)
    5. Normalize synonyms: air conditioner / air con -> ac, television -> tv
    6. Strip filler linking words: of, to, be, to be, for me
    """
    s = _norm_text(s)

    # strip polite prefixes
    s = re.sub(r"^(please\s+|can you\s+|could you\s+|i want to\s+|i need to\s+)", "", s)

    # strip articles
    s = re.sub(r"\b(the|a|an)\b", " ", s)

    # normalize "light bulb" / "light bulb2" -> "lightbulb" / "lightbulb2"
    s = re.sub(r"\blight\s+bulb", "lightbulb", s)

    # normalize English number words: one -> 1, two -> 2, etc.
    _word_numbers = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
        "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
        "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
        "eighteen": "18", "nineteen": "19", "twenty": "20",
    }
    for word, num in _word_numbers.items():
        s = re.sub(rf"\b{word}\b", num, s)

    # normalize ordinals: first -> 1, second -> 2, etc.
    _ordinals = {
        "first": "1", "second": "2", "third": "3", "fourth": "4", "fifth": "5",
        "sixth": "6", "seventh": "7", "eighth": "8", "ninth": "9", "tenth": "10",
        "1st": "1", "2nd": "2", "3rd": "3", "4th": "4", "5th": "5",
    }
    for word, num in _ordinals.items():
        s = re.sub(rf"\b{word}\b", num, s)

    # normalize device-number joins: lightbulb1 -> lightbulb 1, light2 -> light 2, etc.
    s = re.sub(r"\b(lightbulb|light|fan|ac|tv)(\d+)\b", r"\1 \2", s)

    # normalize spelling: colour -> color
    s = s.replace("colour", "color")

    # normalize device synonyms
    s = re.sub(r"\bair\s+conditioner\b", "ac", s)
    s = re.sub(r"\bair\s+con\b", "ac", s)
    s = re.sub(r"\btelevision\b", "tv", s)

    # strip filler linking words between device and param: "of", "to be", "to", "for me"
    s = re.sub(r"\bto\s+be\b", " ", s)
    s = re.sub(r"\bfor\s+me\b", " ", s)
    s = re.sub(r"\b(of|to)\b", " ", s)

    # collapse whitespace
    s = " ".join(s.split())
    return s

def _token_words(tokens: Optional[List[Dict[str, Any]]]) -> List[str]:
    out = []
    if not tokens:
        return out
    for t in tokens:
        w = str(t.get("word") or "").strip()
        if w:
            out.append(_norm_text(w))
    return [w for w in out if w]

def _phrase_words(phrase: str) -> List[str]:
    return [w for w in _norm_text(phrase).split() if w]


def _sentence_words(sentence: str, tokens: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    if tokens:
        return [w for w in _token_words(tokens) if w]
    return [w for w in _norm_text(sentence).split() if w]


def _ordered_match_score(phrase_words: List[str], sent_words: List[str]) -> Optional[float]:
    """
    Exact ordered match with gaps allowed.
    Example:
      phrase = ["face", "angle"]
      sent   = ["face", "to", "90", "degree", "angle"]
      => match

    Score:
      - more words matched is better
      - fewer gaps is better
    """
    if not phrase_words or not sent_words:
        return None

    positions = []
    j = 0

    for pw in phrase_words:
        found = False
        while j < len(sent_words):
            if sent_words[j] == pw:
                positions.append(j)
                j += 1
                found = True
                break
            j += 1
        if not found:
            return None

    gaps = 0
    for i in range(1, len(positions)):
        gaps += positions[i] - positions[i - 1] - 1

    # exact ordered, lower gaps better
    return 70.0 + (len(phrase_words) * 5.0) - (gaps * 1.0)


def _word_matches_with_synonyms(phrase_word: str, sent_word: str) -> bool:
    if phrase_word == sent_word:
        return True

    phrase_syns = set()
    sent_syns = set()

    try:
        phrase_syns |= safe_syns(phrase_word, "VERB")
        phrase_syns |= safe_syns(phrase_word, "NOUN")
        phrase_syns |= safe_syns(phrase_word, "ADJECTIVE")
        phrase_syns |= safe_syns(phrase_word, "ADVERB")
    except Exception:
        pass

    try:
        sent_syns |= safe_syns(sent_word, "VERB")
        sent_syns |= safe_syns(sent_word, "NOUN")
        sent_syns |= safe_syns(sent_word, "ADJECTIVE")
        sent_syns |= safe_syns(sent_word, "ADVERB")
    except Exception:
        pass

    phrase_syns = {_norm_text(x) for x in phrase_syns}
    sent_syns = {_norm_text(x) for x in sent_syns}

    if sent_word in phrase_syns:
        return True
    if phrase_word in sent_syns:
        return True

    if phrase_syns & sent_syns:
        return True

    return False


def _ordered_synonym_match_score(phrase_words: List[str], sent_words: List[str]) -> Optional[float]:
    """
    Ordered match with gaps allowed, but each phrase word may match
    by exact word OR synonym.
    """
    if not phrase_words or not sent_words:
        return None

    positions = []
    exact_count = 0
    synonym_count = 0
    j = 0

    for pw in phrase_words:
        found = False
        while j < len(sent_words):
            sw = sent_words[j]
            if sw == pw:
                positions.append(j)
                exact_count += 1
                j += 1
                found = True
                break
            elif _word_matches_with_synonyms(pw, sw):
                positions.append(j)
                synonym_count += 1
                j += 1
                found = True
                break
            j += 1
        if not found:
            return None

    gaps = 0
    for i in range(1, len(positions)):
        gaps += positions[i] - positions[i - 1] - 1

    # synonym match weaker than exact
    return 50.0 + (exact_count * 5.0) + (synonym_count * 2.0) - (gaps * 1.0)

def build_phrase_index(domain: Dict[str, Any]) -> Dict[str, str]:
    """
    Build phrase -> action map from domain["ACTIONS"][action]["phrases"].
    Phrases should already be extracted from docstrings in expand_domain().
    """
    phrase_to_action: Dict[str, str] = {}

    for action, info in (domain.get("ACTIONS") or {}).items():
        for raw in (info.get("phrases") or []):
            ph = _norm_text(str(raw))
            if not ph:
                continue
            # De-dupe: if same phrase maps to multiple actions, keep first (or choose later)
            phrase_to_action.setdefault(ph, action)

    return phrase_to_action


def safe_syns(word: str, pos: str) -> Set[str]:
    try:
        return set(get_synonyms(word, pos))
    except Exception:
        return set()
    
def _is_number_token(t: Dict[str, Any]) -> bool:
    return t.get("POS") == "NUMBER" or t.get("semantic_type") == "NUMBER"


def _as_int(s: str) -> Optional[int]:
    if not s:
        return None

    # remove punctuation like 100. 100, 100!
    cleaned = re.sub(r"[^\d\-]", "", s)

    if not cleaned:
        return None

    try:
        return int(cleaned)
    except Exception:
        return None

def _is_stop_word(w: str) -> bool:
    return w.lower() in {"the", "a", "an", "to", "for", "on", "in", "at", "by", "of", "me", "him", "her", "them"}


def _find_first_number(tokens: List[Dict[str, Any]]) -> Optional[int]:
    for t in tokens:
        if _is_number_token(t):
            return _as_int(str(t.get("word", "")).strip())
    return None


def _find_number_before_param(tokens: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Pattern: NUMBER + PARAM_x
      e.g. "3 steps" -> {"steps": 3}
    """
    bound: Dict[str, int] = {}
    for i in range(len(tokens) - 1):
        if _is_number_token(tokens[i]):
            nxt = tokens[i + 1].get("semantic_type") or ""
            if isinstance(nxt, str) and nxt.startswith("PARAM_"):
                param = nxt.replace("PARAM_", "", 1)
                v = _as_int(str(tokens[i].get("word", "")).strip())
                if v is not None:
                    bound[param] = v
    return bound


def _extract_after_word(tokens: List[Dict[str, Any]], marker_words: List[str]) -> Optional[str]:
    """
    Extract the token(s) after a marker word, e.g. after "to" in "send 100 to bob".
    We grab the next NOUN/UNKNOWN token as a simple recipient.
    """
    markers = {m.lower() for m in marker_words}
    for i, t in enumerate(tokens):
        if str(t.get("word", "")).lower() in markers:
            # find next content token
            j = i + 1
            while j < len(tokens) and tokens[j].get("POS") in ("determiner", "preposition", "conjunction"):
                j += 1
            if j < len(tokens):
                w = str(tokens[j].get("word", "")).strip()
                if w:
                    return w.lower()
    return None


def _extract_first_content_np(tokens: List[Dict[str, Any]]) -> Optional[str]:
    """
    Extract a simple noun phrase / content phrase ignoring determiners and function words.
    Used for speak("bingo") and similar single-string-param actions.
    """
    words = []
    for t in tokens:
        pos = t.get("POS")
        w = str(t.get("word", "")).strip()
        if not w:
            continue
        if _is_number_token(t):
            continue
        if pos in ("punctuation", "determiner", "preposition", "conjunction", "pronoun"):
            continue
        if _is_stop_word(w):
            continue
        # keep nouns/unknown/adjectives as content
        if pos in ("NOUN", "UNKNOWN", "ADJECTIVE"):
            words.append(w.lower())

    if not words:
        return None
    return " ".join(words)


def _guess_param_kinds(params: List[str]) -> Dict[str, str]:
    """
    Heuristic param kind inference:
      - int-like: steps, amount, limit, degrees, temperature, count, num, number
      - str-like: recipient, speech, name, user, target, device
    """
    int_hints = {"steps", "amount", "limit", "degrees", "degree", "temperature", "count", "num", "number", "n"}
    str_hints = {"recipient", "speech", "name", "user", "target", "device", "room"}

    kinds: Dict[str, str] = {}
    for p in params:
        pl = p.lower()
        if pl in int_hints:
            kinds[p] = "int"
        elif pl in str_hints:
            kinds[p] = "str"
        else:
            # default guess: str (safer for speak/recipient-like domains)
            kinds[p] = "str"
    return kinds

def _annotation_to_name(node) -> Optional[str]:
    if node is None:
        return None

    # int / str / float / bool
    if isinstance(node, ast.Name):
        return node.id

    # Optional[int], list[str], typing.Optional[int], etc.
    if isinstance(node, ast.Subscript):
        base = _annotation_to_name(node.value)
        if base:
            return base

    # typing.Optional / module.Type
    if isinstance(node, ast.Attribute):
        parts = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))

    # "int" as string annotation
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value

    return None

# ============================================================
# AST extraction: classes, actions, params, docstrings
# ============================================================

class DomainExtractor(ast.NodeVisitor):
    def __init__(self):
        self.classes: Set[str] = set()
        self.attributes: Set[str] = set()

        self.functions: Set[str] = set()
        self.methods: Set[str] = set()

        # action -> params
        self.action_params: Dict[str, List[str]] = {}
        self.action_param_types: Dict[str, Dict[str, str]] = {}
        self.class_init_param_types: Dict[str, Dict[str, str]] = {}
        
        # constructor params per class
        self.class_init_params: Dict[str, List[str]] = {}

        # docstrings
        self.class_docstrings: Dict[str, str] = {}
        self.action_docstrings: Dict[str, str] = {}

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes.add(node.name)
        ds = ast.get_docstring(node) or ""
        if ds.strip():
            self.class_docstrings[node.name] = ds.strip()

        for body_item in node.body:
            if isinstance(body_item, ast.FunctionDef):
                self.methods.add(body_item.name)
                params = []
                param_types: Dict[str, str] = {}

                for a in body_item.args.args:
                    if a.arg == "self":
                        continue
                    params.append(a.arg)

                    ann = _annotation_to_name(a.annotation)
                    if ann:
                        param_types[a.arg] = ann

                self.action_params[body_item.name] = params
                self.action_param_types[body_item.name] = param_types

                if body_item.name == "__init__":
                    self.class_init_params[node.name] = params
                    self.class_init_param_types[node.name] = param_types

                mds = ast.get_docstring(body_item) or ""
                if mds.strip():
                    self.action_docstrings[body_item.name] = mds.strip()

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # module-level function
        self.functions.add(node.name)
        params = []
        param_types: Dict[str, str] = {}

        for a in node.args.args:
            if a.arg == "self":
                continue
            params.append(a.arg)

            ann = _annotation_to_name(a.annotation)
            if ann:
                param_types[a.arg] = ann

        self.action_params[node.name] = params
        self.action_param_types[node.name] = param_types

        ds = ast.get_docstring(node) or ""
        if ds.strip():
            self.action_docstrings[node.name] = ds.strip()

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        # self.attr = ...
        for target in node.targets:
            if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                if target.value.id == "self":
                    self.attributes.add(target.attr)
        self.generic_visit(node)


def extract_code_structure(py_file: str) -> Dict[str, Any]:
    if not os.path.exists(py_file):
        raise FileNotFoundError(f"{py_file} not found")

    with open(py_file, "r", encoding="utf-8") as f:
        src = f.read()

    tree = ast.parse(src)
    ex = DomainExtractor()
    ex.visit(tree)

    return {
        "classes": ex.classes,
        "attributes": ex.attributes,
        "functions": ex.functions,
        "methods": ex.methods,
        "action_params": ex.action_params,
        "class_docstrings": ex.class_docstrings,
        "class_init_params": ex.class_init_params,
        "action_docstrings": ex.action_docstrings,
        "action_param_types": ex.action_param_types,
        "class_init_param_types": ex.class_init_param_types,
    }


# ============================================================
# Build domain ("symbol table")
# ============================================================

def expand_domain(structure: Dict[str, Any]) -> Dict[str, Any]:
    domain: Dict[str, Any] = {
        "ACTIONS": {},
        "PARAMETERS": {},
        "OBJECTS": {},
        "ATTRIBUTES": {},
        "RAW": structure,  # keep raw docstrings if you want to show professor
    }

    all_actions = set(structure["functions"]) | set(structure["methods"])
    action_params: Dict[str, List[str]] = structure.get("action_params", {})
    action_param_types: Dict[str, Dict[str, str]] = structure.get("action_param_types", {})
    action_docstrings: Dict[str, str] = structure.get("action_docstrings", {})
    class_docstrings: Dict[str, str] = structure.get("class_docstrings", {})

    # actions
    for action in all_actions:
        base_words = split_snake_case(action)
        syns: Set[str] = set()
        param_types = action_param_types.get(action, {})
        for w in base_words:
            syns |= safe_syns(w, "VERB")
            syns |= safe_syns(w, "NOUN")

        params = action_params.get(action, [])
        doc = action_docstrings.get(action, "")
        phrases = extract_phrases_from_docstring(doc)

        # Build a single text blob for similarity matching.
        # Include method name + params + docstring.
        similarity_text = " ".join([
            action.replace("_", " "),
            " ".join(params),
            doc
        ]).strip()

        domain["ACTIONS"][action] = {
            "base_words": set(base_words),
            "synonyms": set(map(normalize, syns)),
            "params": params,
            "param_types": param_types,
            "docstring": doc,
            "phrases": phrases,
            "similarity_text": similarity_text,
        }

    # objects = classes (use class docstring too)
    class_init_params: Dict[str, List[str]] = structure.get("class_init_params", {})
    for cls in structure["classes"]:
        cls_word = cls.lower()
        domain["OBJECTS"][cls] = {
            "base_words": {cls_word},
            "synonyms": set(map(normalize, safe_syns(cls_word, "NOUN"))),
            "docstring": class_docstrings.get(cls, ""),
            "init_params": class_init_params.get(cls, []),
        }

    # parameters = union of all params
    all_params: Set[str] = set()
    for plist in action_params.values():
        all_params |= set(plist)

    for p in all_params:
        p_l = p.lower()
        domain["PARAMETERS"][p] = {
            "base_words": {p_l},
            "synonyms": set(map(normalize, safe_syns(p_l, "NOUN"))),
        }

    # attributes
    for a in structure["attributes"]:
        a_l = a.lower()
        domain["ATTRIBUTES"][a] = {
            "base_words": {a_l},
            "synonyms": set(map(normalize, safe_syns(a_l, "NOUN"))),
        }

    return domain


DOMAIN_MTIME: Dict[str, float] = {}


def load_domain(py_file: str) -> Dict[str, Any]:
    """
    Load + cache domain extracted from a python file.

    Caches by absolute path. Re-loads if the file has been modified.
    """
    py_file = os.path.abspath(py_file)

    current_mtime = os.path.getmtime(py_file)
    cached = DOMAIN_CACHE.get(py_file)
    cached_mtime = DOMAIN_MTIME.get(py_file, 0)
    if cached is not None and current_mtime <= cached_mtime:
        return cached

    t0 = time.time()
    structure = extract_code_structure(py_file)
    domain = expand_domain(structure)

    # Ensure minimal shape exists (avoid KeyError later)
    domain.setdefault("ACTIONS", {})

    DOMAIN_CACHE[py_file] = domain
    DOMAIN_MTIME[py_file] = current_mtime
    elapsed = (time.time() - t0) * 1000
    print(f"[DOMAIN_CACHE] {'RELOAD' if cached else 'MISS'} for {os.path.basename(py_file)}: {elapsed:.0f}ms")
    return domain


# ============================================================
# Similarity ranking (Sentence ↔ Docstring)
# ============================================================

def rank_actions_by_similarity(sentence: str, domain: Dict[str, Any]) -> List[Tuple[str, float]]:
    """
    Returns list of (action_name, score) sorted descending.
    Uses TF-IDF cosine similarity (offline, explainable baseline).
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception as e:
        raise RuntimeError(
            "scikit-learn is required for docstring similarity. "
            "Install with: pip install scikit-learn"
        ) from e

    actions = list(domain["ACTIONS"].keys())
    docs = [domain["ACTIONS"][a]["similarity_text"] for a in actions]

    corpus = [sentence] + docs
    vec = TfidfVectorizer(lowercase=True, stop_words="english")
    X = vec.fit_transform(corpus)

    sent_vec = X[0:1]
    doc_vecs = X[1:]

    sims = cosine_similarity(sent_vec, doc_vecs).flatten()

    ranked = sorted(zip(actions, sims), key=lambda x: x[1], reverse=True)
    return ranked

# ============================================================
# 1) match_action_by_phrases
# ============================================================
def match_action_by_phrases(
    sentence: str,
    domain: Dict[str, Any],
    tokens: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Optional[str], Optional[str], List[Tuple[str, float]]]:
    """
    Match priority:
      1. exact phrase match
      2. ordered phrase match
      3. ordered synonym phrase match
      4. else none

    Returns:
      (best_action, matched_phrase, ranked)
    """
    actions = domain.get("ACTIONS") or {}
    sent_norm = normalize_user_input(sentence)
    sent_words = sent_norm.split()

    if not actions:
        return None, None, []

    scored: List[Tuple[str, str, float, str]] = []
    # (action, phrase, score, match_type)

    for action, info in actions.items():
        for raw_phrase in (info.get("phrases") or []):
            phrase = normalize_user_input(str(raw_phrase))
            if not phrase:
                continue

            pwords = _phrase_words(phrase)

            # -------------------------
            # 1) exact contiguous phrase match
            # -------------------------
            needle = f" {phrase} "
            hay1 = f" {sent_norm} "
            hay2 = f" {' '.join(sent_words)} "

            if needle in hay1 or needle in hay2:
                score = 100.0 + len(pwords)
                scored.append((action, phrase, score, "exact"))
                continue

            # -------------------------
            # 2) ordered exact word match
            # -------------------------
            ordered_score = _ordered_match_score(pwords, sent_words)
            if ordered_score is not None:
                scored.append((action, phrase, ordered_score, "ordered"))
                continue

            # -------------------------
            # 3) ordered synonym match
            # -------------------------
            synonym_score = _ordered_synonym_match_score(pwords, sent_words)
            if synonym_score is not None:
                scored.append((action, phrase, synonym_score, "ordered_synonym"))
                continue

    if not scored:
        return None, None, []

    # sort by score desc, then longer phrase desc
    scored.sort(key=lambda x: (x[2], len(_phrase_words(x[1]))), reverse=True)

    best_action, best_phrase, best_score, best_type = scored[0]

    ranked = [(action, score) for action, phrase, score, match_type in scored]
    return best_action, best_phrase, ranked

# ============================================================
# 2) pick_best_action (pure phrase match)
# ============================================================
def pick_best_action(
    sentence: str,
    domain: Dict[str, Any],
    require_number_if_param_int: bool = False,
    tokens: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Optional[str], List[Tuple[str, float]]]:
    action, matched_phrase, ranked = match_action_by_phrases(sentence, domain, tokens=tokens)

    print("\n========== DOCSTRING MATCH DEBUG ==========")
    print("Sentence:", sentence)
    print("Sentence(norm):", _norm_text(sentence))
    print("Sentence(user_norm):", normalize_user_input(sentence))
    print("Tokens(norm):", " ".join(_token_words(tokens)))
    print("Matched phrase:", matched_phrase)
    print("Selected action:", action)
    print("Top ranked:", ranked[:5])
    print("Phrase count:", sum(len((info.get("phrases") or [])) for info in (domain.get("ACTIONS") or {}).values()))
    print("===========================================\n")

    return action, ranked

# ============================================================
# Your existing token semantic tagging (kept for PARAM/NUMBER)
# ============================================================

def match_param(word: str, domain: Dict[str, Any]) -> Optional[str]:
    w = normalize(word)
    for param, data in domain["PARAMETERS"].items():
        if w == param.lower():
            return param
        if w in data["synonyms"]:
            return param
    return None


def phase2_map_tokens(tokens: List[Dict[str, Any]], domain: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Phase 2 semantic tagging.

    We do NOT force ACTION mapping by synonyms (docstring similarity still decides),
    but we DO:
      - tag NUMBER
      - tag PARAM_* for nouns that match params
      - docstring-driven "verb promotion":
          If the sentence has NO VERB, and the first token matches an action phrase
          from docstrings (e.g., "back 100"), we promote it to VERB so the grammar
          + downstream action selection works.
    """
    actions = (domain.get("ACTIONS") or {})

    # Build phrase -> action map from docstrings (generic, no hardcoding per method)
    phrase_to_action: Dict[str, str] = {}
    for action, info in actions.items():
        for p in (info.get("phrases") or []):
            key = str(p).strip().lower()
            if key:
                phrase_to_action[key] = action

    out: List[Dict[str, Any]] = []
    for t in tokens:
        word = t.get("word", "")
        pos = t.get("POS", "")
        semantic = None

        if pos == "NUMBER":
            semantic = "NUMBER"
        elif pos == "NOUN":
            p = match_param(word, domain)
            if p:
                semantic = f"PARAM_{p}"

        out.append({"word": word, "POS": pos, "semantic_type": semantic})

    # -------------------------
    # Docstring-driven VERB promotion
    # -------------------------
    has_verb = any((x.get("POS") == "VERB") for x in out)
    if (not has_verb) and out:
        first = out[0]
        w = str(first.get("word") or "").strip().lower()

        # exact match for single-word phrases like "back", "forward", "left", "right"
        mapped = phrase_to_action.get(w)
        if mapped:
            first["POS"] = "VERB"
            # keep semantic_type as-is (NUMBER/PARAM tagging still applies elsewhere)
            first["mapped_action"] = mapped  # optional: downstream can prefer this

    return out


# ============================================================
# 3) bind_args_to_params
# ============================================================
def bind_args_to_params(
    semantic_tokens: List[Dict[str, Any]],
    domain: Dict[str, Any],
    action: Optional[str],
) -> Dict[str, Any]:
    """
    Bind args based on:
      - first NUMBER in sentence -> single int param (amount/limit/days/count/...)
      - for category-like / note-like strings:
          * prefer last NOUN/UNKNOWN as category if param exists
          * for note param: take content phrase after marker words like "note"
      - special pattern:
          "set budget 3000 for food" -> amount=3000, category=food
          "set monthly limit rent 10000" -> category=rent, amount=10000
          "spend 1200 rent" -> amount=1200, category=rent
          "add note lunch with friend" -> note="lunch with friend"
    """
    if not action:
        return {"action": None, "args": {}, "bindings_explained": ["No action selected."]}

    params: List[str] = domain.get("ACTIONS", {}).get(action, {}).get("params", []) or []
    if not params:
        return {"action": action, "args": {}, "bindings_explained": ["Action has no parameters."]}

    # ---------- helpers ----------
    def is_number_token(t: Dict[str, Any]) -> bool:
        return t.get("POS") == "NUMBER" or t.get("semantic_type") == "NUMBER"

    def as_int(x: str) -> Optional[int]:
        if not x:
            return None

        # remove punctuation like 100. 100, 100!
        x = x.strip()
        x = re.sub(r"[^\d\-]", "", x)

        if not x:
            return None

        try:
            return int(x)
        except Exception:
            return None

    def first_number() -> Optional[int]:
        for t in semantic_tokens:
            if is_number_token(t):
                return as_int(str(t.get("word", "")).strip())
        return None
    
    def first_n_numbers(n: int) -> List[int]:
        vals = []
        for t in semantic_tokens:
            if is_number_token(t):
                v = as_int(str(t.get("word", "")).strip())
                if v is not None:
                    vals.append(v)
                    if len(vals) == n:
                        break
        return vals

    def all_words_norm() -> List[str]:
        out = []
        for t in semantic_tokens:
            w = str(t.get("word") or "").strip()
            if not w:
                continue
            out.append(_norm_text(w))
        return [x for x in out if x]

    def last_content_word(exclude_numbers: bool = True) -> Optional[str]:
        # take last NOUN/UNKNOWN/ADJECTIVE token as content (common for category)
        for t in reversed(semantic_tokens):
            if exclude_numbers and is_number_token(t):
                continue
            pos = t.get("POS")
            w = _norm_text(str(t.get("word") or ""))
            if not w:
                continue
            if pos in ("NOUN", "UNKNOWN", "ADJECTIVE"):
                return w
        return None

    def after_marker(markers: List[str]) -> Optional[str]:
        markers = {_norm_text(m) for m in markers}
        words = all_words_norm()
        for i, w in enumerate(words):
            if w in markers and i + 1 < len(words):
                # return everything after marker as a phrase
                rest = " ".join(words[i + 1 :]).strip()
                return rest if rest else None
        return None

    def find_after_word(word: str) -> Optional[str]:
        return after_marker([word])

    # ---------- param kind guess ----------
    INT_HINTS = {
        "amount", "limit", "budget", "days", "day", "count", "num", "number", "n",
        "distance", "steps", "degrees", "degree",
        "x", "y", "width", "height", "startx", "starty", "radius", "size",
        "angle", "fullcircle", "stamp_id", "stretch_wid", "stretch_len", "outline"
    }
    STR_HINTS = {
        "category", "note", "recipient", "name", "owner", "owner_name", "target", "device", "room",
        "colour", "color"
    }

    def kind_of(p: str) -> str:
        declared = (
            domain.get("ACTIONS", {})
            .get(action, {})
            .get("param_types", {})
            .get(p)
        )

        if declared:
            declared_l = declared.lower()
            if declared_l in {"int", "float"}:
                return "int"
            if declared_l in {"str", "string"}:
                return "str"

        pl = p.lower()
        if pl in INT_HINTS:
            return "int"
        if pl in STR_HINTS:
            return "str"

        return "str"

    int_params = [p for p in params if kind_of(p) == "int"]
    str_params = [p for p in params if kind_of(p) == "str"]

    args: Dict[str, Any] = {}
    explain: List[str] = []

    words = all_words_norm()
    sent_norm = " ".join(words)

    # ---------- NOTE binding (very important for "add note lunch with friend") ----------
    # If param includes "note", bind everything after the word "note" if present,
    # otherwise bind content phrase excluding leading command words.
    note_param = next((p for p in params if p.lower() == "note"), None)
    if note_param:
        # "add note X" / "note X" / "attach note X"
        rest = after_marker(["note", "memo", "remark", "comment"])
        if rest:
            args[note_param] = rest
            explain.append(f"Bound {note_param}='{rest}' from text after note/memo/remark/comment.")
        elif len(str_params) == 1 and str_params[0] == note_param:
            # fallback: take everything except stop-ish first word
            if len(words) >= 2:
                rest2 = " ".join(words[1:])
                args[note_param] = rest2
                explain.append(f"Bound {note_param}='{rest2}' from remaining words (fallback).")

    # ---------- INT binding ----------
    def bind_named_int_params() -> Dict[str, int]:
        """
        Supports:
        x 10
        y 15
        x = 10
        y = 15
        x10
        y15
        """
        bound: Dict[str, int] = {}
        words_raw = [str(t.get("word") or "").strip().lower() for t in semantic_tokens if str(t.get("word") or "").strip()]

        i = 0
        while i < len(words_raw):
            w = words_raw[i]

            # case: x10 / y15
            m = re.match(r"^([A-Za-z_]+)(-?\d+)$", w)
            if m:
                param_part = m.group(1).lower()
                value_part = int(m.group(2))

                if param_part in [p.lower() for p in int_params]:
                    real_param = next(p for p in int_params if p.lower() == param_part)
                    bound[real_param] = value_part
                    i += 1
                    continue

            if w in [p.lower() for p in int_params]:
                # case: x 10
                if i + 1 < len(words_raw):
                    v = as_int(words_raw[i + 1])
                    if v is not None:
                        real_param = next(p for p in int_params if p.lower() == w)
                        bound[real_param] = v
                        i += 2
                        continue

                # case: x = 10
                if i + 2 < len(words_raw) and words_raw[i + 1] == "=":
                    v = as_int(words_raw[i + 2])
                    if v is not None:
                        real_param = next(p for p in int_params if p.lower() == w)
                        bound[real_param] = v
                        i += 3
                        continue

            i += 1

        return bound

    if len(int_params) == 1:
        named_bound = bind_named_int_params()
        if named_bound:
            args.update(named_bound)
            for k, v in named_bound.items():
                explain.append(f"Bound {k}={v} from named integer parameter.")
        else:
            num = first_number()
            if num is not None and int_params[0] not in args:
                args[int_params[0]] = num
                explain.append(f"Bound {int_params[0]}={num} (first number in sentence).")

    elif len(int_params) == 2:
        named_bound = bind_named_int_params()
        if named_bound:
            args.update(named_bound)
            for k, v in named_bound.items():
                explain.append(f"Bound {k}={v} from named integer parameter.")

        remaining_int_params = [p for p in int_params if p not in args]
        if remaining_int_params:
            nums = first_n_numbers(len(remaining_int_params))
            num_idx = 0
            for p in remaining_int_params:
                if num_idx < len(nums):
                    args[p] = nums[num_idx]
                    num_idx += 1

            if nums:
                explain.append(
                    f"Bound remaining int params by position: { {p: args[p] for p in remaining_int_params if p in args} }."
                )

    # ---------- CATEGORY binding ----------
    # Works for:
    #   spend 1200 rent  -> last noun = rent
    #   set monthly limit rent 10000 -> last noun before number = rent
    category_param = next((p for p in params if p.lower() == "category"), None)
    if category_param and category_param not in args:
        # special: "for X" pattern (set budget 3000 for food)
        val_for = find_after_word("for")
        if val_for:
            # take first word after "for" as category (or full phrase if you want)
            cat = val_for.split()[0].strip()
            if cat:
                args[category_param] = cat
                explain.append(f"Bound {category_param}='{cat}' from 'for {cat}'.")
        else:
            # pick last content word; but for "rent 10000" we want rent not 10000
            # So: find last noun/unknown before the last number token.
            last_cat = None
            # scan right-to-left; stop at first number then continue for noun before it
            seen_number = False
            for t in reversed(semantic_tokens):
                if is_number_token(t):
                    seen_number = True
                    continue
                if seen_number:
                    pos = t.get("POS")
                    w = _norm_text(str(t.get("word") or ""))
                    if w and pos in ("NOUN", "UNKNOWN", "ADJECTIVE"):
                        last_cat = w
                        break
            if not last_cat:
                last_cat = last_content_word(exclude_numbers=True)

            if last_cat:
                args[category_param] = last_cat
                explain.append(f"Bound {category_param}='{last_cat}' from last content word (category heuristic).")

    # ---------- RECIPIENT binding (transfer 500 to mom) ----------
    recipient_param = next((p for p in params if p.lower() == "recipient"), None)
    if recipient_param and recipient_param not in args:
        val_to = find_after_word("to")
        if val_to:
            rec = val_to.split()[0].strip()
            if rec:
                args[recipient_param] = rec
                explain.append(f"Bound {recipient_param}='{rec}' from 'to {rec}'.")

    if not explain:
        explain.append("No binding rules matched; args may be incomplete.")

    # ---------- DEVICE binding (smart home) ----------
    # Scan sentence for known device aliases before generic string binding
    device_param = next((p for p in params if p.lower() == "device"), None)
    if device_param and device_param not in args:
        DEVICE_ALIASES = {
            "lightbulb 1": "lightbulb 1", "lightbulb1": "lightbulb 1",
            "light 1": "lightbulb 1", "light1": "lightbulb 1",
            "lb1": "lightbulb 1", "lb 1": "lightbulb 1",
            "lightbulb one": "lightbulb 1", "light one": "lightbulb 1",
            "lightbulb 2": "lightbulb 2", "lightbulb2": "lightbulb 2",
            "light 2": "lightbulb 2", "light2": "lightbulb 2",
            "lb2": "lightbulb 2", "lb 2": "lightbulb 2",
            "lightbulb two": "lightbulb 2", "light two": "lightbulb 2",
            "air conditioner": "ac", "air con": "ac", "ac": "ac",
            "fan": "fan",
            "tv": "tv", "television": "tv",
        }
        # Sort by length descending so "lightbulb 1" matches before "lightbulb"
        for alias in sorted(DEVICE_ALIASES.keys(), key=len, reverse=True):
            if alias in sent_norm:
                args[device_param] = DEVICE_ALIASES[alias]
                explain.append(f"Bound {device_param}='{DEVICE_ALIASES[alias]}' from device alias '{alias}'.")
                break

    # ---------- GENERIC SINGLE STRING PARAM ----------
    unbound_str_params = [p for p in str_params if p not in args]

    if len(unbound_str_params) == 1:
        p = unbound_str_params[0]
        free_text = _extract_free_string_value(semantic_tokens, action, p, domain)
        if free_text:
            args[p] = free_text
            explain.append(f"Bound {p}='{free_text}' from free text content.")

    print("\n========== ARG BIND DEBUG ==========")
    print("Action:", action)
    print("Params:", params)
    print("Tokens:", [(t.get("word"), t.get("POS"), t.get("semantic_type")) for t in semantic_tokens])
    print("Bound args:", args)
    print("Explanation:", explain)
    print("====================================\n")

    return {"action": action, "args": args, "bindings_explained": explain}

def bind_number_to_param(semantic_tokens: List[Dict[str, Any]],
                         domain: Dict[str, Any],
                         action: Optional[str] = None) -> Dict[str, Any]:
    return bind_args_to_params(semantic_tokens, domain, action)



def to_required_output(sentence: str, semantic_tokens: List[Dict[str, Any]], bind_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    result = list(semantic_tokens)
    result.append({
        "sentence": sentence,
        "code_function": bind_info.get("action"),
        "args": bind_info.get("args", {})
    })
    return result
