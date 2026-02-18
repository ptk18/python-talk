# backend/app/parser_engine/cfg_parser.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# Your POS labels
VERB = "VERB"
NOUN = "NOUN"
NUMBER = "NUMBER"
ADVERB = "ADVERB"
ADJECTIVE = "ADJECTIVE"
PRONOUN = "pronoun"
DETERMINER = "determiner"
PREPOSITION = "preposition"
CONJUNCTION = "conjunction"

# GRAMMAR
# S  -> VP
# VP -> V NP? PP* ADV*
# NP -> DET? ADJ* N (N)*
# PP -> PREP NP

@dataclass
class Node:
    name: str
    children: List[Any]
    start: int
    end: int


class ParseError(Exception):
    pass


class RDParser:
    """
    Recursive-descent CFG-ish parser (imperative commands).
    Produces a parse tree + grammar_seq + structure label.
    """

    def __init__(self, tokens: List[Dict[str, Any]]):
        # strip punctuation/unknown
        self.tokens = [t for t in tokens if t.get("POS") not in ("punctuation", "UNKNOWN")]
        self.i = 0

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

    # ---------- Grammar ----------
    # S  -> VP
    def parse_S(self) -> Node:
        start = self.i
        vp = self.parse_VP()
        end = self.i
        return Node("S", [vp], start, end)

    # VP -> V NP? PP* ADV*
    def parse_VP(self) -> Node:
        start = self.i
        v = self.parse_V()

        np = self._try(self.parse_NP)  # optional

        pps: List[Node] = []
        while True:
            pp = self._try(self.parse_PP)
            if not pp:
                break
            pps.append(pp)

        advs: List[Node] = []
        while self._pos() == ADVERB:
            advs.append(self.parse_ADV())

        end = self.i
        kids = [v] + ([np] if np else []) + pps + advs
        return Node("VP", kids, start, end)

    # V -> VERB
    def parse_V(self) -> Node:
        start = self.i
        self._eat(VERB)
        end = self.i
        return Node("V", [], start, end)

    # ADV -> ADVERB
    def parse_ADV(self) -> Node:
        start = self.i
        self._eat(ADVERB)
        end = self.i
        return Node("ADV", [], start, end)

    # NP -> DET? ADJ* (NOUN|PRONOUN|NUMBER)+
    def parse_NP(self) -> Node:
        start = self.i
        kids: List[Node] = []

        if self._pos() == DETERMINER:
            self._eat(DETERMINER)
            kids.append(Node("DET", [], self.i - 1, self.i))

        while self._pos() == ADJECTIVE:
            self._eat(ADJECTIVE)
            kids.append(Node("ADJ", [], self.i - 1, self.i))

        # head(s)
        if self._pos() not in (NOUN, PRONOUN, NUMBER):
            raise ParseError("NP needs a head")

        head_start = self.i
        while self._pos() in (NOUN, PRONOUN, NUMBER):
            self.i += 1
        kids.append(Node("HEAD", [], head_start, self.i))

        end = self.i
        return Node("NP", kids, start, end)

    # PP -> PREP NP
    def parse_PP(self) -> Node:
        start = self.i
        self._eat(PREPOSITION)
        np = self.parse_NP()
        end = self.i
        return Node("PP", [np], start, end)


def _flatten_symbols(node: Node) -> List[str]:
    """
    Convert parse tree -> your symbols:
    V, O, A
    - NP => O
    - PP/ADV => A
    """
    out: List[str] = []

    def walk(n: Node):
        if n.name == "V":
            out.append("V")
            return
        if n.name == "NP":
            out.append("O")
            return
        if n.name in ("PP", "ADV"):
            out.append("A")
            return
        for c in n.children:
            if isinstance(c, Node):
                walk(c)

    walk(node)
    return out


def parse_command(tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main API:
    returns {structure, grammar_seq, parse_tree}
    """
    p = RDParser(tokens)
    tree = p.parse_S()

    # if leftover tokens, we still return tree but flag it
    leftover = p.tokens[p.i:] if p.i < len(p.tokens) else []

    grammar_seq = _flatten_symbols(tree)
    structure = {
        ("V",): "SV",
        ("V", "O"): "SVO",
        ("V", "A"): "SVA",
        ("V", "O", "A"): "SVOA",
        ("A", "V"): "ASV",
        ("A", "V", "O"): "ASVO",
        ("A", "V", "O", "A"): "ASVOA",
    }.get(tuple(grammar_seq))

    return {
        "structure": structure,
        "grammar_seq": grammar_seq,
        "parse_tree": tree.__dict__,
        "leftover": [t.get("word") for t in leftover],
    }
