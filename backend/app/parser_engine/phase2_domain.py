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

def build_phrase_index(domain: Dict[str, Any]) -> Dict[str, str]:
    """
    phrase -> action
    If multiple actions share a phrase, first one wins (you can later make tie rules).
    """
    idx: Dict[str, str] = {}
    actions = domain.get("ACTIONS") or {}
    for action, info in actions.items():
        for p in (info.get("phrases") or []):
            key = str(p).strip().lower()
            if key and key not in idx:
                idx[key] = action
    return idx

def safe_syns(word: str, pos: str) -> Set[str]:
    try:
        return set(get_synonyms(word, pos))
    except Exception:
        return set()
    
def _is_number_token(t: Dict[str, Any]) -> bool:
    return t.get("POS") == "NUMBER" or t.get("semantic_type") == "NUMBER"


def _as_int(s: str) -> Optional[int]:
    try:
        return int(s)
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
    for cls in structure["classes"]:
        cls_word = cls.lower()
        domain["OBJECTS"][cls] = {
            "base_words": {cls_word},
            "synonyms": set(map(normalize, safe_syns(cls_word, "NOUN"))),
            "docstring": class_docstrings.get(cls, ""),
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


def pick_best_action(sentence: str,
                     domain: Dict[str, Any],
                     require_number_if_param_int: bool = False,
                     tokens: Optional[List[Dict[str, Any]]] = None
                     ) -> Tuple[Optional[str], List[Tuple[str, float]]]:
    """
    Pure docstring phrase matching.

    Rule:
      - If any phrase from docstrings appears in user input, choose that method.
      - Prefer LONGEST phrase match (e.g., 'go back' > 'back').
      - If nothing matches, return None.
    """
    phrase_to_action = build_phrase_index(domain)

    # normalize sentence
    s = " " + (sentence or "").strip().lower() + " "

    # also consider token words (more robust than raw sentence spacing)
    words = []
    if tokens:
        for t in tokens:
            w = str(t.get("word") or "").strip().lower()
            if w:
                words.append(w)
    token_text = " " + " ".join(words) + " "

    # longest phrase wins
    phrases = sorted(phrase_to_action.keys(), key=len, reverse=True)

    for ph in phrases:
        needle = " " + ph + " "
        if needle in s or needle in token_text:
            action = phrase_to_action[ph]
            # ---------------- DEBUG BLOCK ----------------
            print("\n========== DOCSTRING MATCH DEBUG ==========")
            print("Sentence:", sentence)
            print("Matched phrase:", ph)
            print("Selected action:", action)
            print("===========================================\n")
            # ------------------------------------------------

            return action, [(action, 1.0)]

    print("\n========== DOCSTRING MATCH DEBUG ==========")
    print("Sentence:", sentence)
    print("Matched phrase: None")
    print("Selected action: None")
    print("===========================================\n")

    return None, []

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


from typing import Dict, Any, List, Optional

def bind_args_to_params(semantic_tokens: List[Dict[str, Any]],
                        domain: Dict[str, Any],
                        action: Optional[str]) -> Dict[str, Any]:
    args: Dict[str, Any] = {}
    explain: List[str] = []

    if not action:
        return {"action": None, "args": {}, "bindings_explained": ["No action selected."]}

    params: List[str] = domain.get("ACTIONS", {}).get(action, {}).get("params", []) or []
    if not params:
        return {"action": action, "args": {}, "bindings_explained": ["Action has no parameters."]}

    # ---- helpers ----
    def is_number_token(t: Dict[str, Any]) -> bool:
        return t.get("POS") == "NUMBER" or t.get("semantic_type") == "NUMBER"

    def as_int(x: str) -> Optional[int]:
        try:
            return int(x)
        except Exception:
            return None

    def find_first_number() -> Optional[int]:
        for t in semantic_tokens:
            if is_number_token(t):
                return as_int(str(t.get("word", "")).strip())
        return None

    def find_number_before_param() -> Dict[str, int]:
        bound: Dict[str, int] = {}
        for i in range(len(semantic_tokens) - 1):
            if is_number_token(semantic_tokens[i]):
                nxt = semantic_tokens[i + 1].get("semantic_type") or ""
                if isinstance(nxt, str) and nxt.startswith("PARAM_"):
                    p = nxt.replace("PARAM_", "", 1)
                    v = as_int(str(semantic_tokens[i].get("word", "")).strip())
                    if v is not None:
                        bound[p] = v
        return bound

    def extract_after_word(markers: List[str]) -> Optional[str]:
        markers = {m.lower() for m in markers}
        for i, t in enumerate(semantic_tokens):
            if str(t.get("word", "")).lower() in markers:
                j = i + 1
                while j < len(semantic_tokens) and semantic_tokens[j].get("POS") in (
                    "determiner", "preposition", "conjunction"
                ):
                    j += 1
                if j < len(semantic_tokens):
                    w = str(semantic_tokens[j].get("word", "")).strip()
                    return w.lower() if w else None
        return None

    def extract_content_phrase() -> Optional[str]:
        words: List[str] = []
        for t in semantic_tokens:
            pos = t.get("POS")
            w = str(t.get("word", "")).strip()
            if not w:
                continue
            if is_number_token(t):
                continue
            if pos in ("punctuation", "determiner", "preposition", "conjunction", "pronoun"):
                continue
            if pos in ("NOUN", "UNKNOWN", "ADJECTIVE"):
                words.append(w.lower())
        return " ".join(words) if words else None

    def guess_param_kinds(params_: List[str]) -> Dict[str, str]:
        # add "angle" so right(angle=...) never gets "turn"
        int_hints = {
            "steps", "amount", "limit", "degrees", "degree", "temperature",
            "count", "num", "number", "n", "angle", "distance"
        }
        str_hints = {"recipient", "speech", "name", "user", "target", "device", "room"}
        kinds_: Dict[str, str] = {}
        for p in params_:
            pl = p.lower()
            if pl in int_hints:
                kinds_[p] = "int"
            elif pl in str_hints:
                kinds_[p] = "str"
            else:
                kinds_[p] = "str"
        return kinds_

    kinds = guess_param_kinds(params)

    # ---- rule 1: NUMBER + PARAM_x (strongest) ----
    strong = find_number_before_param()
    for p, v in strong.items():
        if p in params:
            args[p] = v
            explain.append(f"Bound {p}={v} from pattern NUMBER + PARAM_{p}.")

    # ---- rule 2: int-like params: bind numbers only ----
    num = find_first_number()
    if num is not None:
        int_params = [p for p in params if kinds.get(p) == "int"]
        # your hardcode: if there is a number, put it into the numeric param(s)
        if len(int_params) == 1 and int_params[0] not in args:
            args[int_params[0]] = num
            explain.append(f"Bound {int_params[0]}={num} (first number in sentence).")

    # ---- rule 3: 'to X' binds recipient/target/name-like params ----
    to_value = extract_after_word(["to"])
    if to_value:
        str_params = [p for p in params if kinds.get(p) == "str"]
        preferred = None
        for cand in str_params:
            if cand.lower() in {"recipient", "target", "name", "user"}:
                preferred = cand
                break
        if preferred and preferred not in args:
            args[preferred] = to_value
            explain.append(f"Bound {preferred}='{to_value}' from 'to {to_value}'.")
        elif len(str_params) == 1 and str_params[0] not in args:
            args[str_params[0]] = to_value
            explain.append(f"Bound {str_params[0]}='{to_value}' from 'to {to_value}'.")

    # ---- rule 4: ONLY for str-like params (never for int-like) ----
    str_params = [p for p in params if kinds.get(p) == "str"]
    if len(str_params) == 1 and str_params[0] not in args:
        content = extract_content_phrase()
        if content:
            args[str_params[0]] = content
            explain.append(f"Bound {str_params[0]}='{content}' from content phrase.")

    if not explain:
        explain.append("No binding rules matched; args may be incomplete.")

    print("\n========== ARG BIND DEBUG ==========")
    print("Action:", action)
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
