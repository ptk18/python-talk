"""Dependency parsing using spaCy for action/object extraction - Multi-language support"""

import os
import threading
from typing import List, Tuple, Optional

# Feature flag for Thai NLP support
FEATURE_THAI_NLP = os.getenv("FEATURE_THAI_NLP", "true").lower() == "true"


class DependencyParser:
    """
    Multi-language dependency parser using spaCy.

    Supports:
    - English: en_core_web_trf (transformer-based)
    - Thai: pythainlp with spaCy integration (if available)
    """

    def __init__(self):
        self._spacy = None
        self._en_nlp = None
        self._th_nlp = None
        self._en_lock = threading.Lock()
        self._th_lock = threading.Lock()
        self.available = False

        # Try to import spaCy
        try:
            import spacy
            self._spacy = spacy
            self.available = True
        except ImportError:
            pass

    def _get_english_model(self):
        """Lazy load English model with thread safety."""
        if self._en_nlp is not None:
            return self._en_nlp

        with self._en_lock:
            if self._en_nlp is None:
                print("[DependencyParser] Loading English spaCy model...")
                try:
                    self._en_nlp = self._spacy.load("en_core_web_trf")
                except OSError:
                    # Fallback to smaller model if trf not available
                    try:
                        self._en_nlp = self._spacy.load("en_core_web_sm")
                        print("[DependencyParser] Using en_core_web_sm fallback")
                    except OSError:
                        raise RuntimeError("No English spaCy model available")
        return self._en_nlp

    def _get_thai_model(self):
        """Lazy load Thai model with thread safety."""
        if not FEATURE_THAI_NLP:
            return self._get_english_model()

        if self._th_nlp is not None:
            return self._th_nlp

        with self._th_lock:
            if self._th_nlp is None:
                print("[DependencyParser] Loading Thai NLP model...")
                try:
                    # Try pythainlp's spaCy wrapper
                    from pythainlp import word_tokenize
                    from pythainlp.tag import pos_tag

                    # Create a simple Thai NLP wrapper
                    self._th_nlp = ThaiNLPWrapper(word_tokenize, pos_tag)
                    print("[DependencyParser] Thai NLP loaded via pythainlp")
                except ImportError:
                    print("[DependencyParser] pythainlp not available, using English fallback for Thai")
                    self._th_nlp = self._get_english_model()
        return self._th_nlp

    @property
    def nlp(self):
        """Backward compatibility - returns English model."""
        return self._get_english_model()

    def detect_language(self, text: str) -> str:
        """
        Detect if text is Thai or English based on character analysis.

        Thai Unicode range: U+0E00 to U+0E7F
        """
        if not text:
            return "en"

        thai_chars = sum(1 for c in text if '\u0E00' <= c <= '\u0E7F')
        total_alpha = sum(1 for c in text if c.isalpha())

        if total_alpha == 0:
            return "en"

        thai_ratio = thai_chars / total_alpha
        return "th" if thai_ratio > 0.3 else "en"

    def get_nlp(self, language: str = "en"):
        """Get the appropriate NLP model for a language."""
        if language.lower() in ("th", "thai", "ไทย"):
            return self._get_thai_model()
        return self._get_english_model()

    def extract_actions(self, text: str, language: str = None) -> List[Tuple[str, List[str], List[str], str]]:
        """
        Extract actions from text.

        Args:
            text: Input text to analyze
            language: Language code ('en', 'th') or None for auto-detect

        Returns:
            List of tuples: (verb, objects, noun_chunks, action_span)
        """
        if not self.available:
            raise RuntimeError("spaCy not available - cannot parse")

        # Auto-detect language if not specified
        if language is None:
            language = self.detect_language(text)

        nlp_model = self.get_nlp(language)

        # Handle Thai with custom wrapper
        if isinstance(nlp_model, ThaiNLPWrapper):
            return self._extract_actions_thai(text, nlp_model)

        # Handle English/spaCy models
        return self._extract_actions_spacy(text, nlp_model)

    def _extract_actions_spacy(self, text: str, nlp) -> List[Tuple[str, List[str], List[str], str]]:
        """Extract actions using spaCy model."""
        doc = nlp(text)
        actions = []

        for token in doc:
            # Handle regular verbs AND imperative commands (first word as ROOT)
            is_verb = token.pos_ == "VERB"
            is_imperative_root = (token.dep_ == "ROOT" and token.i == 0)

            if is_verb or is_imperative_root:
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

    def _extract_actions_thai(self, text: str, thai_nlp: 'ThaiNLPWrapper') -> List[Tuple[str, List[str], List[str], str]]:
        """Extract actions from Thai text using pythainlp."""
        # Tokenize and POS tag
        tokens = thai_nlp.tokenize(text)
        pos_tags = thai_nlp.pos_tag(tokens)

        actions = []

        # Thai POS tags: VACT (action verb), VSTA (stative verb)
        for i, (word, pos) in enumerate(pos_tags):
            if pos in ('VACT', 'VSTA', 'VERB'):
                # Collect objects (nouns following the verb)
                objects = []
                noun_chunks = []

                for j in range(i + 1, len(pos_tags)):
                    next_word, next_pos = pos_tags[j]
                    if next_pos in ('NCMN', 'NPRP', 'NOUN', 'NUM'):
                        objects.append(next_word)
                        noun_chunks.append(next_word)
                    elif next_pos in ('VACT', 'VSTA', 'VERB', 'PUNCT'):
                        break

                # Build action span
                end_idx = i + 1 + len(objects)
                action_span = ''.join(tokens[i:end_idx])

                actions.append((word, objects, noun_chunks, action_span))

        # If no verbs found, treat first word as action (imperative)
        if not actions and tokens:
            return [(tokens[0], tokens[1:], tokens[1:], text)]

        return actions if actions else [(text, [], [], text)]

    def _extract_verb_span(self, verb_token, doc):
        """Extract the text span that belongs to this specific verb"""
        verb_children = list(verb_token.subtree)

        if not verb_children:
            return verb_token.text

        start_idx = min(child.i for child in verb_children)
        end_idx = max(child.i for child in verb_children)

        return doc[start_idx:end_idx + 1].text


class ThaiNLPWrapper:
    """
    Wrapper for pythainlp to provide a consistent interface.
    """

    def __init__(self, tokenize_func, pos_tag_func):
        self._tokenize = tokenize_func
        self._pos_tag = pos_tag_func

    def tokenize(self, text: str) -> List[str]:
        """Tokenize Thai text."""
        return self._tokenize(text, engine='newmm')

    def pos_tag(self, tokens: List[str]) -> List[Tuple[str, str]]:
        """POS tag tokenized text."""
        return self._pos_tag(tokens, engine='perceptron')
