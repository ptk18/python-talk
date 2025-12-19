"""Dependency parsing using spaCy for action/object extraction"""

from typing import List, Tuple


class DependencyParser:
    def __init__(self):
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_trf")
            self.available = True
        except (ImportError, OSError):
            self.available = False

    def extract_actions(self, text: str) -> List[Tuple[str, List[str], List[str], str]]:
        if not self.available:
            raise RuntimeError("spaCy not available - no fallbacks allowed in POC")

        doc = self.nlp(text)
        actions = []

        for token in doc:
            if token.pos_ == "VERB":
                particles = [child.text for child in token.children if child.dep_ == "prt"]
                objects = [child.text for child in token.children if child.dep_ in ("dobj", "obj", "attr", "pobj")]

                all_noun_chunks = []
                for chunk in doc.noun_chunks:
                    if chunk.root.head == token:
                        all_noun_chunks.append(chunk.text)

                verb = token.text
                if particles:
                    verb = f"{verb}_{particles[0]}"

                action_span = self._extract_verb_span(token, doc)
                actions.append((verb, objects, all_noun_chunks, action_span))

        return actions if actions else [(text, [], [], text)]

    def _extract_verb_span(self, verb_token, doc):
        """Extract the text span that belongs to this specific verb"""
        verb_children = list(verb_token.subtree)

        if not verb_children:
            return verb_token.text

        start_idx = min(child.i for child in verb_children)
        end_idx = max(child.i for child in verb_children)

        return doc[start_idx:end_idx + 1].text
