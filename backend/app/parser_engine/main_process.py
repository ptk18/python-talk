# main_process.py
# ============================================================
# Main Process — CFG Parsing + Structure Detection + Translation
#
# Clean design (domain-independent):
#   - Process 1: lex_alz.analyze_sentence()
#   - Process 2: phase2_domain.load_domain() extracts actions/params/docstrings
#   - Main:
#       * semantic similarity (sentence vs docstring) => best action
#       * parameter binding (NUMBER -> PARAM)
#       * grammar detection (SV/SVO/SVA/SVOA/SVOO/SVOC...)
#       * structure enumeration
#       * generic code generation
# ============================================================

from typing import Dict, List, Any, Optional
import json

from app.parser_engine.lex_alz import setup_nltk, analyze_sentence
from app.parser_engine.phase2_domain import (
    load_domain,
    phase2_map_tokens,
    pick_best_action,
    bind_number_to_param,
    to_required_output,
)

from app.parser_engine.cfg_parser import parse_command

# ------------------------------------------------------------
# POS categories (from your process 1)
# ------------------------------------------------------------
VERB = "VERB"
NOUN = "NOUN"
NUMBER = "NUMBER"
ADVERB = "ADVERB"
ADJECTIVE = "ADJECTIVE"
PRONOUN = "pronoun"
DETERMINER = "determiner"
PREPOSITION = "preposition"
CONJUNCTION = "conjunction"


# ------------------------------------------------------------
# Grammar table (expanded)
# ------------------------------------------------------------
# We detect structure from a simplified symbol sequence:
# V = verb/action
# O = object noun phrase
# IO = indirect object (pronoun)
# A = adverbial (adverb or PP)
# C = complement (adjective)
#
# IMPORTANT: numbers are ignored in structure (value inside NP).
GRAMMAR_TABLE = {
    ("V",): "SV",
    ("V", "O"): "SVO",
    ("V", "A"): "SVA",
    ("V", "O", "A"): "SVOA",
    ("V", "IO", "O"): "SVOO",
    ("V", "O", "C"): "SVOC",
    ("V", "IO", "O", "A"): "SVOOA",
    ("V", "O", "O"): "SVOO",     # rare but possible
    ("A", "V"): "ASV",
    ("A", "V", "O"): "ASVO",
    ("A", "V", "O", "A"): "ASVOA",
}


def detect_grammar(lex_tokens: List[Dict[str, Any]],
                   sem_tokens: List[Dict[str, Any]],
                   best_action: Optional[str] = None,
                   domain: Optional[Dict[str, Any]] = None) -> Optional[str]:


    """
    Grammar detection with semantic fallback:
      - ACTION_* => treat token as V even if POS was tagged NOUN
      - NUMBER ignored (values inside noun phrases)
    """
    seq: List[str] = []
    
    param_words = set()
    
    if domain and best_action and best_action in domain.get("ACTIONS", {}):
        for p in domain["ACTIONS"][best_action].get("params", []):
            param_words.add(p.lower())

    i = 0

    while i < len(lex_tokens):
        pos = lex_tokens[i]["POS"]
        st = sem_tokens[i].get("semantic_type")

        if pos in ("punctuation", "UNKNOWN"):
            i += 1
            continue

        if pos == NUMBER:
            i += 1
            continue
        
        # If we already resolved an action by docstring similarity,
        # force the first meaningful token to be treated as V.
        if best_action and len(seq) == 0 and pos not in (ADVERB, PREPOSITION):
            seq.append("V")
            i += 1
            continue

        if st and isinstance(st, str) and st.startswith("ACTION_"):
            seq.append("V")
            i += 1
            continue
        
        w = str(lex_tokens[i].get("word", "")).lower()
        if w in param_words:
            seq.append("O")
            i += 1
            continue

        if pos == VERB:
            seq.append("V")
            i += 1
            continue

        if pos == PRONOUN:
            seq.append("IO")
            i += 1
            continue

        # adverbial: ADVERB or a PREPOSITIONAL PHRASE head
        if pos == ADVERB or pos == PREPOSITION:
            seq.append("A")
            i += 1

            # if PP, consume its NP part to avoid extra O's
            if pos == PREPOSITION:
                while i < len(lex_tokens) and lex_tokens[i]["POS"] in (
                    DETERMINER, ADJECTIVE, NOUN, PRONOUN, NUMBER
                ):
                    i += 1
            continue

        if pos == ADJECTIVE:
            seq.append("C")
            i += 1
            continue

        # noun phrase => O
        if pos in (NOUN, DETERMINER):
            seq.append("O")
            i += 1
            while i < len(lex_tokens) and lex_tokens[i]["POS"] in (
                NOUN, DETERMINER, ADJECTIVE, NUMBER
            ):
                i += 1
            continue

        i += 1

    return GRAMMAR_TABLE.get(tuple(seq)), seq


# ------------------------------------------------------------
# Slot extraction helpers
# ------------------------------------------------------------
def extract_adverbs(tokens: List[Dict[str, Any]]) -> List[str]:
    return [t["word"].lower() for t in tokens if t["POS"] == ADVERB]


def extract_prep_phrases(tokens: List[Dict[str, Any]]) -> List[str]:
    """
    Very simple PP extractor: PREP + (DT/ADJ/NOUN/PRONOUN/NUMBER)* until boundary.
    """
    pps: List[str] = []
    i = 0
    while i < len(tokens):
        if tokens[i]["POS"] == PREPOSITION:
            start = i
            i += 1
            while i < len(tokens) and tokens[i]["POS"] in (
                DETERMINER, ADJECTIVE, NOUN, PRONOUN, NUMBER
            ):
                i += 1
            phrase = " ".join(t["word"] for t in tokens[start:i])
            pps.append(phrase)
        else:
            i += 1
    return pps


def build_adverbial(adverbs: List[str], prep_phrases: List[str]) -> Optional[str]:
    parts = []
    parts += adverbs
    parts += prep_phrases
    s = " ".join(parts).strip()
    return s if s else None


def extract_first_object_phrase(tokens: List[Dict[str, Any]]) -> Optional[str]:
    """
    First noun phrase (DT/ADJ/NOUN/NUMBER sequence) after the verb.
    Used only as a fallback for enumeration when args are empty.
    """
    verb_i = None
    for i, t in enumerate(tokens):
        if t["POS"] == VERB:
            verb_i = i
            break
    if verb_i is None:
        return None

    i = verb_i + 1
    while i < len(tokens) and tokens[i]["POS"] in (PRONOUN, NUMBER, ADVERB, PREPOSITION, CONJUNCTION):
        i += 1

    if i < len(tokens) and tokens[i]["POS"] in (DETERMINER, ADJECTIVE, NOUN, NUMBER):
        start = i
        i += 1
        while i < len(tokens) and tokens[i]["POS"] in (DETERMINER, ADJECTIVE, NOUN, NUMBER):
            i += 1
        return " ".join(t["word"] for t in tokens[start:i])

    return None


def pick_action_surface(action: Optional[str]) -> Optional[str]:
    """
    Convert method name to a surface verb phrase.
    say_hello -> "say hello"
    """
    if not action:
        return None
    return action.replace("_", " ")


def build_param_np(args: Dict[str, Any]) -> Optional[str]:
    """
    Build a noun phrase from bound args (domain-independent).
    Examples:
      {"steps": 3} -> "3 steps"
      {"amount": 2} -> "2 amount"
      {"amount": 2, "recipient": "Bob"} -> "2 amount Bob"
    (You can refine wording later per-domain via docstrings.)
    """
    if not args:
        return None

    parts: List[str] = []
    for k, v in args.items():
        if isinstance(v, int):
            parts.append(f"{v} {k}")
        else:
            parts.append(str(v))
    return " ".join(parts) if parts else None


def enumerate_structures(action: Optional[str],
                         args: Dict[str, Any],
                         lex_tokens: List[Dict[str, Any]],
                         domain: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grammar-driven enumeration with FULL realizations (for professor demo).

    Produces variants like:
      - walk 3 steps slowly
      - slowly walk 3 steps
      - walk slowly for 3 steps
    """
    verb_phrase = pick_action_surface(action)
    if not verb_phrase:
        return {"count": 0, "variants": []}

    adverbial = build_adverbial(extract_adverbs(lex_tokens), extract_prep_phrases(lex_tokens))

    np = build_param_np(args) or extract_first_object_phrase(lex_tokens)

    # Determine whether action expects params (avoid "say hello hello" type issues)
    expects_np = False
    if action and action in domain.get("ACTIONS", {}):
        expects_np = len(domain["ACTIONS"][action].get("params", [])) > 0
    else:
        expects_np = bool(np)

    variants: List[Dict[str, str]] = []
    seen = set()

    def add(structure: str, sent: str):
        sent = " ".join(sent.split())
        key = (structure, sent.lower())
        if key in seen:
            return
        seen.add(key)
        variants.append({"structure": structure, "sentence": sent})

    # SV
    add("SV", f"{verb_phrase}")

    # SVO
    if expects_np and np:
        add("SVO", f"{verb_phrase} {np}")

    # SVA + ASV
    if adverbial:
        add("SVA", f"{verb_phrase} {adverbial}")
        add("ASV", f"{adverbial} {verb_phrase}")

    # SVOA + ASVO + SVAO + SVAO_FOR
    if expects_np and np and adverbial:
        add("SVOA", f"{verb_phrase} {np} {adverbial}")
        add("ASVO", f"{adverbial} {verb_phrase} {np}")
        add("SVAO", f"{verb_phrase} {adverbial} {np}")
        add("SVAO_FOR", f"{verb_phrase} {adverbial} for {np}")

    return {"count": len(variants), "variants": variants}


# ------------------------------------------------------------
# Domain-independent translation (syntax-directed)
# ------------------------------------------------------------
def pick_instance_name(domain: Dict[str, Any], action: str) -> str:
    """
    Heuristic: use the first discovered class name as instance name.
    Example: Robot -> robot, SmartHome -> smarthome
    """
    classes = list(domain.get("OBJECTS", {}).keys())
    if classes:
        return classes[0].lower()
    return "obj"


def generate_code(action: Optional[str],
                  args: Dict[str, Any],
                  domain: Dict[str, Any]) -> Optional[str]:
    """
    Generic code generator:
      instance.action(positional_args...)
    We pass positional args in the order of the method signature from Process 2.
    """
    if not action:
        return None

    instance = pick_instance_name(domain, action)

    params = domain.get("ACTIONS", {}).get(action, {}).get("params", [])

    if not params:
        return f"{instance}.{action}()"

    # positional arguments in signature order, if available
    arg_values: List[str] = []
    for p in params:
        if p in args:
            v = args[p]
            arg_values.append(repr(v) if isinstance(v, str) else str(v))
        else:
            # if missing, keep placeholder (better for demo than crashing)
            arg_values.append("None")

    return f"{instance}.{action}({', '.join(arg_values)})"


def _clean_string_args(args: Dict[str, Any], action: Optional[str]) -> Dict[str, Any]:
    """
    Remove action words from string parameters.
    Examples:
      action=turn_on
      "turn tv" -> "tv"
      "turn" -> "" (delete => missing)
    """
    if not args or not action:
        return args

    stop = set(action.replace("_", " ").lower().split())  # {"turn","on"}

    cleaned: Dict[str, Any] = {}
    for k, v in args.items():
        if isinstance(v, str):
            toks = [t for t in v.strip().lower().split() if t not in stop]
            new_v = " ".join(toks).strip()
            if new_v:  # keep only if not empty
                cleaned[k] = new_v
        else:
            cleaned[k] = v

    return cleaned


# ------------------------------------------------------------
# Main pipeline
# ------------------------------------------------------------
def run(sentence: str, py_file: str) -> List[Dict[str, Any]]:
    # Process 1
    lex_tokens = analyze_sentence(sentence)

    # Process 2: domain + semantic token tagging
    domain = load_domain(py_file)
    sem_tokens = phase2_map_tokens(lex_tokens, domain)

    # Choose best action by docstring similarity
    best_action, ranked = pick_best_action(
        sentence,
        domain,
        require_number_if_param_int=True,
        tokens=lex_tokens
    )

    # Bind params based on action signature + token evidence
    bind_info = bind_number_to_param(sem_tokens, domain, action=best_action)

    # cleanup string args like "turn tv" -> "tv", "turn" -> missing
    bind_info["args"] = _clean_string_args(bind_info.get("args", {}) or {}, bind_info.get("action"))

    # Main: grammar + slots
    g = parse_command(lex_tokens)
    grammar = g["structure"]
    grammar_seq = g["grammar_seq"]
    result[-1]["parse_tree"] = g["parse_tree"]
    result[-1]["leftover"] = g["leftover"]

    adverbs = extract_adverbs(lex_tokens)
    prep_phrases = extract_prep_phrases(lex_tokens)

    # Code generation (generic)
    code = generate_code(bind_info.get("action"), bind_info.get("args", {}), domain)

    # Enumeration (full realizations)
    enum_info = enumerate_structures(bind_info.get("action"), bind_info.get("args", {}), lex_tokens, domain)

    # Output in your required format
    result = to_required_output(sentence, sem_tokens, bind_info)
    result[-1]["bindings_explained"] = bind_info.get("bindings_explained", [])
    result[-1]["grammar"] = grammar
    result[-1]["grammar_seq"] = grammar_seq
    result[-1]["adverbs"] = adverbs
    result[-1]["prep_phrases"] = prep_phrases
    result[-1]["generated_code"] = code
    result[-1]["enumerated_structures"] = enum_info
    result[-1]["docstring_similarity_ranked"] = [
        {"action": a, "score": float(s)} for a, s in ranked[:5]
    ]

    return result


if __name__ == "__main__":
    setup_nltk()

    # change to your file path
    py_file = "parser/code/robot.py"

    tests = [
        # "Move 3 steps slowly",
        # "Take 3 steps slowly",
        # "walk 3 steps",
        "say hello",
        "say bingo",
        # "quickly walk 2 steps",
        # "walk 4 steps in the kitchen",
    ]

    for s in tests:
        print(json.dumps(run(s, py_file), indent=2))
        print("-" * 60)
