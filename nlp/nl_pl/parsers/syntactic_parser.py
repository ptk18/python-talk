import spacy
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

@dataclass
class Token:
    text: str
    lemma: str
    pos: str
    tag: str
    dep: str
    head_text: str
    head_pos: str
    children: List[str]

@dataclass
class SyntacticParse:
    tokens: List[Token]
    noun_phrases: List[str]
    verb_phrases: List[Tuple[str, List[str]]]
    dependencies: Dict[str, List[str]]
    conjunctions: List[str]
    conditionals: List[str]
    raw_text: str

class SyntacticParser:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")

    def parse(self, text: str) -> SyntacticParse:
        doc = self.nlp(text)

        tokens = []
        for token in doc:
            children = [child.text for child in token.children]
            tokens.append(Token(
                text=token.text,
                lemma=token.lemma_,
                pos=token.pos_,
                tag=token.tag_,
                dep=token.dep_,
                head_text=token.head.text,
                head_pos=token.head.pos_,
                children=children
            ))

        noun_phrases = [chunk.text for chunk in doc.noun_chunks]

        verb_phrases = self._extract_verb_phrases(doc)

        dependencies = self._extract_dependencies(doc)

        conjunctions = [token.text for token in doc if token.pos_ == "CCONJ" or token.dep_ == "cc"]

        conditionals = [token.text for token in doc if token.lemma_ in ["if", "when", "while", "unless", "until"]]

        return SyntacticParse(
            tokens=tokens,
            noun_phrases=noun_phrases,
            verb_phrases=verb_phrases,
            dependencies=dependencies,
            conjunctions=conjunctions,
            conditionals=conditionals,
            raw_text=text
        )

    def _extract_verb_phrases(self, doc) -> List[Tuple[str, List[str]]]:
        verb_phrases = []
        for token in doc:
            if token.pos_ == "VERB":
                dependents = []
                for child in token.children:
                    if child.dep_ in ["dobj", "pobj", "attr", "prep", "advmod"]:
                        dependents.append(child.text)
                        for grandchild in child.children:
                            dependents.append(grandchild.text)
                verb_phrases.append((token.lemma_, dependents))
        return verb_phrases

    def _extract_dependencies(self, doc) -> Dict[str, List[str]]:
        deps = {}
        for token in doc:
            if token.dep_ not in deps:
                deps[token.dep_] = []
            deps[token.dep_].append(token.text)
        return deps

    def get_verb_objects(self, parse: SyntacticParse) -> List[Tuple[str, Optional[str], Optional[str]]]:
        results = []
        for token in parse.tokens:
            if token.pos == "VERB":
                subj = None
                obj = None

                for child_text in token.children:
                    child_token = next((t for t in parse.tokens if t.text == child_text), None)
                    if child_token:
                        if child_token.dep in ["nsubj", "nsubjpass"]:
                            subj = child_token.text
                        elif child_token.dep in ["dobj", "pobj", "attr"]:
                            obj = child_token.text

                results.append((token.lemma, subj, obj))

        return results
