# phase2_domain.py
import ast
import os
from typing import Dict, List, Set, Optional, Any, Tuple
import re

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

def _token_words(tokens: Optional[List[Dict[str, Any]]]) -> List[str]:
    out = []
    if not tokens:
        return out
    for t in tokens:
        w = str(t.get("word") or "").strip()
        if w:
            out.append(_norm_text(w))
    return [w for w in out if w]


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
                params = [a.arg for a in body_item.args.args if a.arg != "self"]
                self.action_params[body_item.name] = params

                if body_item.name == "__init__":
                    self.class_init_params[node.name] = params

                mds = ast.get_docstring(body_item) or ""
                if mds.strip():
                    self.action_docstrings[body_item.name] = mds.strip()

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # module-level function
        self.functions.add(node.name)
        params = [a.arg for a in node.args.args if a.arg != "self"]
        self.action_params[node.name] = params

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
    action_docstrings: Dict[str, str] = structure.get("action_docstrings", {})
    class_docstrings: Dict[str, str] = structure.get("class_docstrings", {})

    # actions
    for action in all_actions:
        base_words = split_snake_case(action)
        syns: Set[str] = set()
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


def load_domain(py_file: str) -> Dict[str, Any]:
    """
    Load + cache domain extracted from a python file.

    Caches by absolute path.
    """
    py_file = os.path.abspath(py_file)

    cached = DOMAIN_CACHE.get(py_file)
    if cached is not None:
        return cached

    structure = extract_code_structure(py_file)
    domain = expand_domain(structure)

    # Ensure minimal shape exists (avoid KeyError later)
    domain.setdefault("ACTIONS", {})

    DOMAIN_CACHE[py_file] = domain
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
    Returns:
      (best_action, matched_phrase, ranked)

    ranked is a lightweight list like [(action, 1.0)] for compatibility
    """
    phrase_to_action = build_phrase_index(domain)

    sent_norm = _norm_text(sentence)
    token_norm = " ".join(_token_words(tokens))
    # use both representations for robustness
    hay = f" {sent_norm} "
    hay2 = f" {token_norm} "

    if not phrase_to_action:
        # no phrases extracted => impossible to match
        return None, None, []

    # longest phrase wins
    phrases_sorted = sorted(phrase_to_action.keys(), key=lambda x: len(x), reverse=True)

    for ph in phrases_sorted:
        needle = f" {ph} "
        if needle in hay or needle in hay2:
            action = phrase_to_action[ph]
            return action, ph, [(action, 1.0)]

    return None, None, []

# ============================================================
# 2) pick_best_action (pure phrase match)
# ============================================================
def pick_best_action(
    sentence: str,
    domain: Dict[str, Any],
    require_number_if_param_int: bool = False,  # kept for signature compatibility
    tokens: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Optional[str], List[Tuple[str, float]]]:
    """
    Pure docstring phrase matching.

    Rule:
      - If any phrase from docstrings appears in user input, choose that method.
      - Prefer LONGEST phrase match (e.g., 'set monthly limit' > 'set').
      - If nothing matches, return None.
    """
    action, matched_phrase, ranked = match_action_by_phrases(sentence, domain, tokens=tokens)

    print("\n========== DOCSTRING MATCH DEBUG ==========")
    print("Sentence:", sentence)
    print("Sentence(norm):", _norm_text(sentence))
    print("Tokens(norm):", " ".join(_token_words(tokens)))
    print("Matched phrase:", matched_phrase)
    print("Selected action:", action)
    # helpful: show how many phrases exist
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
        "amount", "limit", "budget", "days", "day", "count", "num", "number", "n", "distance", "steps", "degrees", "degree"
    }
    STR_HINTS = {
        "category", "note", "recipient", "name", "owner", "owner_name", "target", "device", "room"
    }

    def kind_of(p: str) -> str:
        pl = p.lower()
        if pl in INT_HINTS:
            return "int"
        if pl in STR_HINTS:
            return "str"
        # default
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
    num = first_number()
    if num is not None and len(int_params) == 1 and int_params[0] not in args:
        args[int_params[0]] = num
        explain.append(f"Bound {int_params[0]}={num} (first number in sentence).")

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
