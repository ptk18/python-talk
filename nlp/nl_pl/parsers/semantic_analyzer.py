from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from .syntactic_parser import SyntacticParse, Token

class SemanticRole(Enum):
    AGENT = "agent"
    ACTION = "action"
    PATIENT = "patient"
    THEME = "theme"
    INSTRUMENT = "instrument"
    LOCATION = "location"
    TIME = "time"
    MANNER = "manner"
    QUANTITY = "quantity"

@dataclass
class SemanticFrame:
    action: str
    roles: Dict[SemanticRole, Any]
    confidence: float

@dataclass
class ParseNode:
    node_type: str
    value: Any
    children: List['ParseNode'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SemanticAnalysis:
    frames: List[SemanticFrame]
    parse_tree: ParseNode
    entities: Dict[str, str]
    raw_text: str

class SemanticAnalyzer:
    def __init__(self, known_actions=None):
        self.dependency_role_map = {
            "nsubj": SemanticRole.AGENT,
            "nsubjpass": SemanticRole.PATIENT,
            "dobj": SemanticRole.PATIENT,
            "pobj": SemanticRole.THEME,
            "attr": SemanticRole.THEME,
            "prep": SemanticRole.INSTRUMENT,
            "advmod": SemanticRole.MANNER,
            "nummod": SemanticRole.QUANTITY
        }
        self.known_actions = set(known_actions) if known_actions else set()

    def analyze(self, syntactic_parse: SyntacticParse) -> SemanticAnalysis:
        frames = self._extract_semantic_frames(syntactic_parse)
        parse_tree = self._build_parse_tree(syntactic_parse)
        entities = self._extract_entities(syntactic_parse)

        return SemanticAnalysis(
            frames=frames,
            parse_tree=parse_tree,
            entities=entities,
            raw_text=syntactic_parse.raw_text
        )

    def _extract_semantic_frames(self, parse: SyntacticParse) -> List[SemanticFrame]:
        frames = []

        for token in parse.tokens:
            is_action = (token.pos == "VERB" or
                        (token.dep == "ROOT" and token.lemma.lower() in self.known_actions))

            if is_action:
                roles = {}
                confidence = 1.0

                for child_text in token.children:
                    child = next((t for t in parse.tokens if t.text == child_text), None)
                    if child and child.dep in self.dependency_role_map:
                        role = self.dependency_role_map[child.dep]
                        roles[role] = self._extract_entity_value(child, parse)

                if token.dep == "ROOT":
                    roles[SemanticRole.ACTION] = token.lemma
                    frames.append(SemanticFrame(
                        action=token.lemma,
                        roles=roles,
                        confidence=confidence
                    ))

        return frames

    def _extract_entity_value(self, token: Token, parse: SyntacticParse) -> Any:
        if token.pos == "NUM":
            try:
                return float(token.text) if '.' in token.text else int(token.text)
            except ValueError:
                return token.text

        if token.children:
            parts = [token.text]
            for child_text in token.children:
                child = next((t for t in parse.tokens if t.text == child_text), None)
                if child and child.dep in ["compound", "amod", "det"]:
                    parts.insert(0, child.text)
            return " ".join(parts)

        return token.text

    def _build_parse_tree(self, parse: SyntacticParse) -> ParseNode:
        root_token = next((t for t in parse.tokens if t.dep == "ROOT"), parse.tokens[0])

        root_node = ParseNode(
            node_type="ROOT",
            value=root_token.lemma,
            metadata={"pos": root_token.pos, "text": root_token.text}
        )

        visited = set()
        self._build_tree_recursive(root_token, root_node, parse, visited)

        return root_node

    def _build_tree_recursive(self, token: Token, node: ParseNode, parse: SyntacticParse, visited: set):
        token_id = id(token)
        if token_id in visited:
            return
        visited.add(token_id)

        for child_text in token.children:
            child_token = next((t for t in parse.tokens if t.text == child_text), None)
            if child_token and id(child_token) not in visited:
                child_node = ParseNode(
                    node_type=child_token.dep,
                    value=child_token.lemma,
                    metadata={"pos": child_token.pos, "text": child_token.text}
                )
                node.children.append(child_node)
                self._build_tree_recursive(child_token, child_node, parse, visited)

    def _extract_entities(self, parse: SyntacticParse) -> Dict[str, str]:
        entities = {}

        for token in parse.tokens:
            if token.pos in ["NOUN", "PROPN"]:
                entity_value = self._extract_entity_value(token, parse)
                entities[token.text] = str(entity_value)

            if token.pos == "NUM":
                entities[token.text] = token.text

        return entities

    def get_action_structure(self, analysis: SemanticAnalysis) -> List[Dict[str, Any]]:
        structures = []

        for frame in analysis.frames:
            structure = {
                "action": frame.action,
                "agent": frame.roles.get(SemanticRole.AGENT),
                "patient": frame.roles.get(SemanticRole.PATIENT),
                "theme": frame.roles.get(SemanticRole.THEME),
                "confidence": frame.confidence
            }
            structures.append(structure)

        return structures
