# backend/app/parser_engine/cfg_parser.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Iterator


# =========================
# POS Labels (must match lex_alz)
# =========================
VERB = "VERB"
NOUN = "NOUN"
NUMBER = "NUMBER"
ADVERB = "ADVERB"
ADJECTIVE = "ADJECTIVE"
PRONOUN = "pronoun"
DETERMINER = "determiner"
PREPOSITION = "preposition"
CONJUNCTION = "conjunction"
COMMA = "COMMA"


# =========================
# Separator vocabulary
# =========================
SEPARATOR_ADVERBS = {
    "then",
    "next",
    "afterwards",
    "afterward",
    "later",
}


# ============================================================
# Parse Tree Node
# ============================================================

@dataclass
class Node:
    name: str
    children: List[Any]
    start: int
    end: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "children": [
                c.to_dict() if isinstance(c, Node) else c
                for c in self.children
            ]
        }


class ParseError(Exception):
    pass


# ============================================================
# Recursive Descent Parser
# ============================================================

class RDParser:
    def __init__(self, tokens: List[Dict[str, Any]]):
        # keep same behavior as your original file:
        # remove punctuation/unknown from the CFG stream
        self.tokens = [
            t for t in tokens
            if t.get("POS") not in ("punctuation", "UNKNOWN")
        ]
        self.i = 0

    # -------------------------
    # Helpers
    # -------------------------
    def _peek(self) -> Optional[Dict[str, Any]]:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def _pos(self) -> Optional[str]:
        t = self._peek()
        return t.get("POS") if t else None

    def _word(self) -> str:
        t = self._peek()
        if not t:
            return ""
        return str(t.get("word", "")).strip().lower()

    def _eat(self, pos: str) -> Dict[str, Any]:
        t = self._peek()
        if not t:
            raise ParseError("Unexpected end")
        if t.get("POS") != pos:
            raise ParseError(f"Expected {pos}, got {t.get('POS')}")
        self.i += 1
        return t

    def _try(self, fn):
        saved = self.i
        try:
            return fn()
        except ParseError:
            self.i = saved
            return None

    def _is_separator_adverb_here(self) -> bool:
        """
        True if current token is an adverb-word that should split commands,
        e.g. 'then', 'next', ...
        """
        w = self._word()
        p = self._pos()

        # accept both POS-aware and POS-agnostic matching for robustness
        if w in SEPARATOR_ADVERBS:
            return True
        if p == ADVERB and w in SEPARATOR_ADVERBS:
            return True
        return False

    # -------------------------
    # Grammar
    # -------------------------
    # S -> CommandList
    def parse_S(self) -> Node:
        start = self.i
        cl = self.parse_CommandList()
        return Node("S", [cl], start, self.i)

    # CommandList -> Command (Separator Command)*
    def parse_CommandList(self) -> Node:
        start = self.i
        children = []

        first = self.parse_Command()
        children.append(first)

        while True:
            sep = self._try(self.parse_Separator)
            if not sep:
                break

            cmd = self.parse_Command()
            children.append(sep)
            children.append(cmd)

        return Node("CommandList", children, start, self.i)

    # Command -> VP
    def parse_Command(self) -> Node:
        start = self.i
        vp = self.parse_VP()
        return Node("Command", [vp], start, self.i)

    # Separator -> CONJUNCTION | (separator ADVERB) | COMMA
    def parse_Separator(self) -> Node:
        start = self.i

        # conjunction like "and"
        if self._pos() == CONJUNCTION:
            self.i += 1
            return Node("Separator", [], start, self.i)

        # adverb separators like "then"
        if self._is_separator_adverb_here():
            self.i += 1
            return Node("Separator", [], start, self.i)

        # comma separator
        if self._pos() == COMMA:
            self._eat(COMMA)
            return Node("Separator", [], start, self.i)

        raise ParseError("Expected separator")

    # VP -> V NP? PP* ADV*
    # IMPORTANT FIX:
    #   Do NOT let VP consume separator-adverbs like "then".
    def parse_VP(self) -> Node:
        start = self.i
        children: List[Any] = []

        v = self.parse_V()
        children.append(v)

        np = self._try(self.parse_NP)
        if np:
            children.append(np)

        while True:
            pp = self._try(self.parse_PP)
            if not pp:
                break
            children.append(pp)

        # Only consume adverbs that are NOT separators (so "then" remains for Separator)
        while self._pos() == ADVERB and not self._is_separator_adverb_here():
            children.append(self.parse_ADV())

        return Node("VP", children, start, self.i)

    # V -> VERB | ACTION_* fallback
    def parse_V(self) -> Node:
        t = self._peek()
        if not t:
            raise ParseError("Unexpected end in V")

        start = self.i
        pos = str(t.get("POS", ""))
        word = str(t.get("word", "")).strip().lower()

        # normal VERB
        if pos == VERB:
            tok = self._eat(VERB)
            return Node("V", [tok], start, self.i)

        # fallback for semantic-tagged actions (if ever used)
        if pos.startswith("ACTION"):
            self.i += 1
            return Node("V", [t], start, self.i)

        # IMPORTANT TOLERANCE:
        # Many taggers label imperative verbs like "turn" as NOUN.
        # If we're at the beginning of a VP, force the first meaningful token to V
        # (but don't do it for adverb/preposition or separators like "then").
        if pos not in (ADVERB, PREPOSITION) and (word not in SEPARATOR_ADVERBS) and word != "and":
            self.i += 1
            return Node("V", [t], start, self.i)

        raise ParseError("Expected VERB")


    # NP -> (DET)? (ADJ)* (NOUN|PRONOUN|NUMBER)+
    def parse_NP(self) -> Node:
        start = self.i
        children: List[Any] = []

        det = self._try(self.parse_DET)
        if det:
            children.append(det)

        while self._pos() == ADJECTIVE:
            children.append(self.parse_ADJ())

        # require at least one head (noun/pronoun/number)
        if self._pos() not in (NOUN, PRONOUN, NUMBER):
            raise ParseError("Expected NP head")

        while self._pos() in (NOUN, PRONOUN, NUMBER):
            if self._pos() == NOUN:
                children.append(self.parse_N())
            elif self._pos() == PRONOUN:
                children.append(self.parse_PRO())
            else:
                children.append(self.parse_NUM())

        return Node("NP", children, start, self.i)

    # PP -> PREP NP
    def parse_PP(self) -> Node:
        start = self.i
        prep = self.parse_PREP()
        np = self.parse_NP()
        return Node("PP", [prep, np], start, self.i)

    # ADV -> ADVERB
    def parse_ADV(self) -> Node:
        start = self.i
        tok = self._eat(ADVERB)
        return Node("ADV", [tok], start, self.i)

    # ADJ -> ADJECTIVE
    def parse_ADJ(self) -> Node:
        start = self.i
        tok = self._eat(ADJECTIVE)
        return Node("ADJ", [tok], start, self.i)

    # DET -> DETERMINER
    def parse_DET(self) -> Node:
        start = self.i
        tok = self._eat(DETERMINER)
        return Node("DET", [tok], start, self.i)

    # PREP -> PREPOSITION
    def parse_PREP(self) -> Node:
        start = self.i
        tok = self._eat(PREPOSITION)
        return Node("PREP", [tok], start, self.i)

    # N -> NOUN
    def parse_N(self) -> Node:
        start = self.i
        tok = self._eat(NOUN)
        return Node("N", [tok], start, self.i)

    # PRO -> PRONOUN
    def parse_PRO(self) -> Node:
        start = self.i
        tok = self._eat(PRONOUN)
        return Node("PRO", [tok], start, self.i)

    # NUM -> NUMBER
    def parse_NUM(self) -> Node:
        start = self.i
        tok = self._eat(NUMBER)
        return Node("NUM", [tok], start, self.i)


# ============================================================
# API
# ============================================================

def parse_command(lex_tokens, sem_tokens=None) -> Dict[str, Any]:
    """
    Main API used by main_process.py

    Returns:
      {
        "structure": "SVO" | "SVOA" | ... | None,
        "grammar_seq": ["V","O","A", ...],
        "parse_tree": {...} | None,
        "leftover": ["..."]
      }
    """

    # Merge semantic info (keep your old behavior)
    if sem_tokens:
        merged = []
        for lt, st in zip(lex_tokens, sem_tokens):
            x = dict(lt)
            if "semantic_type" in st:
                x["semantic_type"] = st["semantic_type"]
            merged.append(x)
        tokens = merged
    else:
        tokens = lex_tokens

    parser = RDParser(tokens)

    try:
        tree = parser.parse_S()
    except ParseError:
        return {
            "structure": None,
            "grammar_seq": [],
            "parse_tree": None,
            "leftover": [],
        }

    leftover = parser.tokens[parser.i:] if parser.i < len(parser.tokens) else []

    grammar_seq = _flatten_symbols(tree)

    # Keep your original mapping
    structure_map = {
        ("V",): "SV",
        ("V", "O"): "SVO",
        ("V", "A"): "SVA",
        ("V", "O", "A"): "SVOA",
        ("A", "V"): "ASV",
        ("A", "V", "O"): "ASVO",
        ("A", "V", "O", "A"): "ASVOA",
    }

    structure = structure_map.get(tuple(grammar_seq))

    return {
        "structure": structure,
        "grammar_seq": grammar_seq,
        "parse_tree": to_dict(tree),
        "leftover": [t.get("word") for t in leftover],
    }


# ============================================================
# Tree Utilities
# ============================================================

def iter_nodes(tree: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
    stack = [tree]
    while stack:
        n = stack.pop()
        if not isinstance(n, dict):
            continue
        if "name" in n:
            yield n
        for c in reversed(n.get("children", [])):
            if isinstance(c, dict):
                stack.append(c)


def extract_nodes_by_name(tree: Dict[str, Any], name: str) -> List[Dict[str, Any]]:
    return [n for n in iter_nodes(tree) if n.get("name") == name]


def extract_commands(tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    return extract_nodes_by_name(tree, "Command")


def extract_vps(tree: Dict[str, Any]) -> List[Dict[str, Any]]:
    # main_process imports this
    return extract_nodes_by_name(tree, "VP")


def span_to_text(tokens: List[Dict[str, Any]], start: int, end: int) -> str:
    # main_process imports this
    return " ".join(t.get("word", "") for t in tokens[start:end]).strip()


def to_dict(node: Node) -> Dict[str, Any]:
    out_children = []
    for c in node.children:
        if isinstance(c, Node):
            out_children.append(to_dict(c))
        elif isinstance(c, dict):
            out_children.append(c)
        else:
            out_children.append(c)
    return {
        "name": node.name,
        "start": node.start,
        "end": node.end,
        "children": out_children,
    }


def _flatten_symbols(tree: Node) -> List[str]:
    """
    Convert parse tree to compact grammar symbols:
      - V  -> "V"
      - NP -> "O"
      - PP/ADV -> "A"
    """
    seq: List[str] = []

    def walk(n: Any):
        if not isinstance(n, dict):
            return

        name = n.get("name")
        if name == "V":
            seq.append("V")
        elif name == "NP":
            seq.append("O")
        elif name in ("PP", "ADV"):
            seq.append("A")

        for c in n.get("children", []):
            if isinstance(c, dict):
                walk(c)

    walk(to_dict(tree))
    return seq
