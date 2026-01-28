"""Dependency parsing using spaCy for action/object extraction - Multi-language support"""

import os
import time
import threading
from typing import List, Tuple, Optional

# Feature flag for Thai NLP support
FEATURE_THAI_NLP = os.getenv("FEATURE_THAI_NLP", "true").lower() == "true"


class DependencyParser:
    """
    Multi-language dependency parser using spaCy.

    Supports:
    - English: en_core_web_md (balanced) via global model registry
    - Thai: pythainlp with spaCy integration (if available)
    """

    # Base set of common verbs (fallback only)
    # Includes smart home domain verbs that spaCy often misclassifies
    _BASE_VERBS = {
        # math operations
        "add", "subtract", "multiply", "divide", "sum", "calculate",
        # CRUD operations
        "create", "delete", "remove", "update", "insert", "append",
        # general actions
        "get", "set", "move", "turn", "draw", "show", "hide",
        "start", "stop", "save", "load",
        "print", "display", "run", "execute", "call",
        # movement
        "forward", "backward", "left", "right", "rotate",
        # shapes
        "circle", "square", "triangle", "line", "dot",
        # adjustments
        "increase", "decrease", "raise", "lower",
        # SMART HOME DOMAIN - critical verbs often misclassified as ADJ/NOUN
        "open", "close", "shut",  # on/off actions
        "dim", "brighten",  # brightness
        "cool", "warm", "heat",  # temperature
        "activate", "deactivate",  # device control
        "switch", "toggle", "power",  # power control
        "adjust", "configure",  # settings
    }

    def __init__(self):
        self._spacy = None
        self._en_nlp = None
        self._th_nlp = None
        self._th_lock = threading.Lock()
        self.available = False
        # Dynamic verb set - populated from user's uploaded code
        self._method_verbs = set()

        # Try to import spaCy
        try:
            import spacy
            self._spacy = spacy
            self.available = True
        except ImportError:
            pass

    def initialize_with_methods(self, methods: list):
        """
        Extract verbs from user's uploaded methods.
        This allows the parser to recognize user-specific verbs that
        spaCy might misclassify as PROPN.

        Args:
            methods: List of MethodInfo objects from user's uploaded code
        """
        self._method_verbs = set()
        for method in methods:
            # Split method name by underscore (e.g., "turn_on" -> ["turn", "on"])
            tokens = method.name.lower().split('_')
            # First token is typically the verb (e.g., "turn" from "turn_on_light")
            if tokens:
                self._method_verbs.add(tokens[0])
            # Also add full method name in case it's a single-word verb
            self._method_verbs.add(method.name.lower())

        print(f"[DependencyParser] Initialized with {len(self._method_verbs)} verbs from user methods: {sorted(self._method_verbs)[:10]}...")

    def _get_english_model(self):
        """Get English model from global registry (shared singleton)."""
        if self._en_nlp is not None:
            return self._en_nlp

        # Use shared model from global registry (loaded once at app startup)
        from . import get_spacy_model

        self._en_nlp = get_spacy_model()
        if self._en_nlp is None:
            raise RuntimeError("No English spaCy model available. Install with: python -m spacy download en_core_web_md")
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
        parse_start = time.perf_counter()
        doc = nlp(text)
        parse_time = (time.perf_counter() - parse_start) * 1000
        print(f"[TIMING] spaCy parsing: {parse_time:.2f}ms")

        # Print token analysis table
        print(f"[DEBUG] Token analysis:")
        print(f"  {'Token':<12} {'POS':<8} {'DEP':<10} {'HEAD':<12} {'Detected As'}")
        print(f"  {'-'*60}")

        actions = []

        # Pre-check: Is first token a known verb? (handles "open tv" where spaCy misses it)
        first_token_is_known_verb = (
            len(doc) > 0 and
            doc[0].text.lower() in self._get_common_verbs()
        )

        for token in doc:
            # Handle regular verbs AND imperative commands (first word as ROOT)
            is_verb = token.pos_ == "VERB"
            is_imperative_root = (token.dep_ == "ROOT" and token.i == 0)

            # CRITICAL FIX: Detect known verb at sentence start even if spaCy misclassifies
            # This handles "open tv" where spaCy tags "open" as ADJ instead of VERB
            is_known_verb_at_start = (
                token.i == 0 and
                first_token_is_known_verb and
                token.pos_ in ("ADJ", "NOUN", "PROPN", "VERB")  # Accept any POS if it's a known verb
            )

            # Catch conjoined verbs (e.g., "add X then multiply Y" - "multiply" has dep_="conj")
            is_conjoined_verb = (token.dep_ == "conj" and token.head.pos_ == "VERB")
            # Handle secondary verbs that spaCy misclassifies as PROPN with dep_="dep"
            # This happens with "add X then multiply Y" - spaCy tags "multiply" as PROPN/dep
            is_secondary_verb = (
                token.dep_ == "dep" and
                token.head.pos_ == "VERB" and
                token.pos_ in ("VERB", "PROPN", "NOUN") and
                token.text.lower() in self._get_common_verbs()
            )

            # Build detection string for debug output
            detection = []
            if is_verb: detection.append("VERB")
            if is_imperative_root: detection.append("IMPERATIVE")
            if is_known_verb_at_start: detection.append("KNOWN_VERB_START")
            if is_conjoined_verb: detection.append("CONJOINED")
            if is_secondary_verb: detection.append("SECONDARY")
            detected_str = ", ".join(detection) if detection else "-"

            print(f"  {token.text:<12} {token.pos_:<8} {token.dep_:<10} {token.head.text:<12} {detected_str}")

            if is_verb or is_imperative_root or is_known_verb_at_start or is_conjoined_verb or is_secondary_verb:
                # Detect particles - spaCy may tag them as "prt" OR as "prep" (ADP)
                # Common phrasal verb particles: on, off, up, down, in, out, away, back, over
                PHRASAL_PARTICLES = {"on", "off", "up", "down", "in", "out", "away", "back", "over"}

                particles = []
                for child in token.children:
                    if child.dep_ == "prt":
                        # Standard particle detection
                        particles.append(child.text)
                    elif child.dep_ == "prep" and child.text.lower() in PHRASAL_PARTICLES:
                        # Phrasal verb particle misclassified as preposition
                        # Only treat as particle if it has no prepositional object
                        # (e.g., "turn on" vs "turn on the light" - both should detect "on" as particle)
                        particles.append(child.text)

                # Extract direct objects AND objects through prepositions (e.g., "subtract 4 from 6")
                objects = self._extract_objects(token)

                # SPECIAL CASE: When we detected a known verb at start but spaCy misclassified it
                # The "objects" are actually what spaCy made the ROOT or following tokens
                # e.g., "open tv" -> spaCy sees "tv" as ROOT, "open" as modifier
                if is_known_verb_at_start and not objects:
                    # Look at head token (which spaCy wrongly made ROOT)
                    if token.head != token and token.head.pos_ in ("NOUN", "PROPN"):
                        objects.append(token.head.text)
                    # Also check following tokens for nouns
                    for following in doc[token.i + 1:]:
                        if following.pos_ in ("NOUN", "PROPN") and following.text not in objects:
                            objects.append(following.text)
                        elif following.pos_ == "CCONJ":  # Stop at "and"
                            break

                all_noun_chunks = []
                for chunk in doc.noun_chunks:
                    if chunk.root.head == token or (is_known_verb_at_start and chunk.root == token.head):
                        all_noun_chunks.append(chunk.text)

                verb = token.text
                if particles:
                    verb = f"{verb}_{particles[0]}"

                action_span = self._extract_verb_span(token, doc)
                actions.append((verb, objects, all_noun_chunks, action_span))
                print(f"  → Extracted: verb='{verb}', objects={objects}")

        print(f"[DEBUG] Total actions extracted: {len(actions)}")
        return actions if actions else [(text, [], [], text)]

    def _extract_objects(self, token) -> List[str]:
        """Extract objects including those accessed through prepositions."""
        objects = []
        for child in token.children:
            # Direct objects
            if child.dep_ in ("dobj", "obj", "attr", "pobj", "npadvmod"):
                objects.append(child.text)
            # Objects after prepositions (e.g., "subtract 4 from 6" - "6" is child of "from")
            elif child.dep_ == "prep":
                for subchild in child.children:
                    if subchild.dep_ in ("pobj", "obj"):
                        objects.append(subchild.text)
        return objects

    def _get_common_verbs(self) -> set:
        """
        Get verbs to check for secondary verb detection.

        Combines:
        1. Dynamic verbs extracted from user's uploaded methods (primary)
        2. Base common verbs as fallback

        This ensures the system works with ANY user-uploaded code,
        not just hardcoded verb lists.
        """
        # Combine dynamic method verbs with base fallback
        return self._method_verbs | self._BASE_VERBS

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
