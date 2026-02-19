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

    def _eat(self, pos: str) -> Dict[str, Any]:
        t = self._peek()
        if not t or t.get("POS") != pos:
            raise ParseError(f"Expected {pos}, got {t.get('POS') if t else None}")
        self.i += 1
        return t

    def _try(self, fn):
        save = self.i
        try:
            return fn()
        except ParseError:
            self.i = save
            return None

    # ============================================================
    # Grammar
    # ============================================================

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

    # Separator -> CONJUNCTION | COMMA
    def parse_Separator(self) -> Node:
        start = self.i

        if self._pos() == CONJUNCTION:
            self._eat(CONJUNCTION)
            return Node("Separator", [], start, self.i)

        if self._pos() == COMMA:
            self._eat(COMMA)
            return Node("Separator", [], start, self.i)

        raise ParseError("Expected separator")

    # VP -> V NP? PP* ADV*
    def parse_VP(self) -> Node:
        start = self.i
        children = []

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

        while self._pos() == ADVERB:
            children.append(self.parse_ADV())

        return Node("VP", children, start, self.i)

    # V -> VERB | ACTION_* fallback
    def parse_V(self) -> Node:
        t = self._peek()
        if not t:
            raise ParseError("Unexpected end in V")

        start = self.i

        if t.get("POS") == VERB:
            self.i += 1
            return Node("V", [], start, self.i)

        st = t.get("semantic_type")
        if isinstance(st, str) and st.startswith("ACTION_"):
            self.i += 1
            return Node("V", [], start, self.i)

        if self.i == 0 and t.get("POS") in (NOUN,):
            self.i += 1
            return Node("V", [], start, self.i)

        raise ParseError(f"Expected VERB, got {t.get('POS')}")

    # ADV -> ADVERB
    def parse_ADV(self) -> Node:
        start = self.i
        self._eat(ADVERB)
        return Node("ADV", [], start, self.i)

    # NP -> DET? ADJ* (NOUN|PRONOUN|NUMBER)+
    def parse_NP(self) -> Node:
        start = self.i
        children = []

        if self._pos() == DETERMINER:
            self._eat(DETERMINER)
            children.append(Node("DET", [], self.i - 1, self.i))

        while self._pos() == ADJECTIVE:
            self._eat(ADJECTIVE)
            children.append(Node("ADJ", [], self.i - 1, self.i))

        if self._pos() not in (NOUN, PRONOUN, NUMBER):
            raise ParseError("NP requires head")

        head_start = self.i
        while self._pos() in (NOUN, PRONOUN, NUMBER):
            self.i += 1

        children.append(Node("HEAD", [], head_start, self.i))

        return Node("NP", children, start, self.i)

    # PP -> PREPOSITION NP
    def parse_PP(self) -> Node:
        start = self.i
        self._eat(PREPOSITION)
        np = self.parse_NP()
        return Node("PP", [np], start, self.i)


# ============================================================
# Flatten Grammar Symbols
# ============================================================

def _flatten_symbols(node: Node) -> List[str]:
    symbols = []

    def walk(n: Node):
        if n.name == "V":
            symbols.append("V")
            return
        if n.name == "NP":
            symbols.append("O")
            return
        if n.name in ("PP", "ADV"):
            symbols.append("A")
            return

        for c in n.children:
            if isinstance(c, Node):
                walk(c)

    walk(node)
    return symbols


# ============================================================
# Public API
# ============================================================

def parse_command(lex_tokens, sem_tokens=None) -> Dict[str, Any]:

    # Merge semantic info
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
        "parse_tree": tree.to_dict(),
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
    return extract_nodes_by_name(tree, "VP")


def span_to_text(tokens: List[Dict[str, Any]], start: int, end: int) -> str:
    return " ".join(t.get("word", "") for t in tokens[start:end]).strip()
