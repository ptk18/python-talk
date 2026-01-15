"""Main NLP v3 pipeline - Honest architecture with transparent scoring"""

from typing import List, Tuple, Dict
from datetime import datetime as time
from difflib import SequenceMatcher

from .models import MethodInfo, MatchScore
from .semantic_matcher import LocalSemanticMatcher
from .dependency_parser import DependencyParser
from .synonym_generator import ClaudeSynonymGenerator
from .entity_normalizer import EntityNormalizer


class NLPPipeline:
    # Measurement units that should be filtered from object matching
    # These are descriptive words, not method indicators
    MEASUREMENT_UNITS = {
        'steps', 'step', 'degrees', 'degree', 'pixels', 'pixel',
        'units', 'unit', 'times', 'time', 'seconds', 'second'
    }

    def __init__(self):
        self.semantic_matcher = LocalSemanticMatcher()
        self.dependency_parser = DependencyParser()
        self.synonym_generator = ClaudeSynonymGenerator()
        self.entity_normalizer = None

    def initialize(self, methods: List[MethodInfo]):
        """Initialize pipeline with methods - call this after creating pipeline"""
        print("\n[1/2] Building synonym dictionary via LLM (single call)...")
        start = time.now()
        self.synonym_generator.prewarm_cache(methods)
        elapsed = (time.now() - start).total_seconds()
        print(f"  ✓ Completed in {elapsed:.1f}s")

        print("\n[2/2] Building entity normalization map...")
        start = time.now()
        self.entity_normalizer = EntityNormalizer(methods, self.synonym_generator)
        elapsed = (time.now() - start).total_seconds()
        print(f"  ✓ Completed in {elapsed:.1f}s")

        print("\n✓ Pipeline ready for processing commands!\n")

    def process_command(
        self,
        command: str,
        methods: List[MethodInfo],
        top_k: int = 1,
        language: str = None
    ) -> List[Tuple[str, MatchScore]]:
        """
        Process a command and return top_k matches.

        Args:
            command: Natural language command
            methods: List of available methods
            top_k: Number of top matches to return
            language: Language code ('en', 'th') or None for auto-detect
        """
        actions = self.dependency_parser.extract_actions(command, language=language)

        all_results = []

        for action_verb, action_objects, noun_chunks, action_span in actions:
            scores = self._match_action_to_methods(
                action_verb,
                action_objects,
                noun_chunks,
                action_span,
                methods
            )

            if scores:
                all_results.append((action_verb, scores[0]))

        return all_results

    def _extract_numeric_params(self, command: str, method: MethodInfo) -> Dict[str, any]:
        """Extract numeric parameters using dependency parsing and word2number"""
        doc = self.dependency_parser.nlp(command)
        params = {}

        # Group consecutive number tokens into phrases
        number_groups = []
        current_group = []

        for token in doc:
            if token.pos_ == "NUM":
                current_group.append(token)
            elif token.text in ['-'] and current_group:
                # Hyphen within a number (e.g., "ninety-eight")
                current_group.append(token)
            elif token.text.lower() == 'and' and current_group:
                # "and" can be within a number or between numbers
                # Within: "four hundred AND ninety"
                # Between: "ninety-eight AND eight hundred"

                # Look ahead to see if next is a number
                next_idx = token.i + 1
                if next_idx < len(doc) and doc[next_idx].pos_ == 'NUM':
                    # Check if previous number is a scale word (hundred, thousand, million)
                    if current_group and current_group[-1].text.lower() in ['hundred', 'thousand', 'million']:
                        # "hundred AND ninety" - within number
                        current_group.append(token)
                    else:
                        # "ninety-eight AND eight" - between numbers
                        if current_group:
                            number_groups.append(current_group)
                        current_group = []
                else:
                    current_group.append(token)
            else:
                if current_group:
                    number_groups.append(current_group)
                    current_group = []

        # Don't forget the last group
        if current_group:
            number_groups.append(current_group)

        # Convert each number group to a numeric value
        numbers = []
        for group in number_groups:
            phrase = ' '.join([t.text for t in group])

            # Try to parse as direct number first
            try:
                # Remove all commas from numbers (e.g., "9,89" -> "989", "78,956" -> "78956")
                # Only treat "." as decimal separator
                clean_phrase = phrase.replace(',', '')

                value = float(clean_phrase) if '.' in clean_phrase else int(clean_phrase)
                numbers.append(value)
                continue
            except ValueError:
                pass

            # Use word2number to convert text to number
            try:
                from word2number import w2n
                # Clean up the phrase (remove hyphens, normalize spacing)
                clean_phrase = phrase.replace('-', ' ').replace('  ', ' ').strip()
                word_value = w2n.word_to_num(clean_phrase)
                numbers.append(word_value)
            except (ValueError, ImportError, AttributeError):
                # If word2number fails, skip this group
                continue

        # Map extracted numbers to method parameters
        for i, param_name in enumerate(method.params):
            if i < len(numbers):
                params[param_name] = numbers[i]

        return params

    def _match_action_to_methods(
        self,
        action_verb: str,
        action_objects: List[str],
        noun_chunks: List[str],
        action_span: str,
        methods: List[MethodInfo]
    ) -> List[MatchScore]:
        scores = []

        # Extract object nouns from noun chunks (remove determiners)
        object_nouns = []
        for chunk in noun_chunks:
            words = chunk.lower().split()
            object_nouns.extend(words)

        # Also add direct objects
        object_nouns.extend([obj.lower() for obj in action_objects])
        object_nouns = list(set(object_nouns))  # deduplicate

        # Filter out measurement units - these are descriptive words, not method indicators
        # e.g., "move 50 steps forward" - "steps" should not match against "st" method
        object_nouns = [obj for obj in object_nouns if obj not in self.MEASUREMENT_UNITS]

        action_verb_normalized = action_verb.replace('_', ' ')

        # Normalize entities in object nouns
        if self.entity_normalizer:
            normalized_objects = [self.entity_normalizer.normalize(obj) for obj in object_nouns]
            # Flatten normalized results (may contain multi-word entities)
            object_nouns_normalized = []
            for norm_obj in normalized_objects:
                object_nouns_normalized.extend(norm_obj.split())
            object_nouns_normalized = list(set(object_nouns_normalized))
        else:
            object_nouns_normalized = object_nouns

        # Get synonyms for the action verb (cached)
        verb_synonyms = self.synonym_generator.get_synonyms(
            action_verb_normalized,
            context=" ".join(object_nouns_normalized) if object_nouns_normalized else ""
        )

        for method in methods:
            method_text = method.to_searchable_text()
            method_name_lower = method.name.lower()
            method_words = set(method.name.replace('_', ' ').lower().split())
            method_tokens = method.name.lower().split('_')

            # Semantic similarity (general text model)
            semantic_score = self.semantic_matcher.compute_similarity(
                action_verb_normalized,
                method_text.lower()
            )

            # Code-aware similarity (CodeBERT if available)
            code_similarity = self.semantic_matcher.compute_code_similarity(
                action_span,
                method.name
            )

            # IMPROVED: Synonym-based verb matching with fuzzy token matching
            synonym_verb_match = 0.0
            if verb_synonyms:
                # Split method name into tokens
                method_token_set = set(method_tokens)

                # Check each synonym phrase
                for syn in verb_synonyms:
                    syn_tokens = set(syn.lower().replace(' ', '_').split('_'))

                    # Token overlap matching
                    overlap = len(syn_tokens & method_token_set)
                    if overlap > 0:
                        # Boost by overlap ratio (stronger if more tokens match)
                        overlap_ratio = overlap / max(len(syn_tokens), 1)
                        synonym_verb_match = max(synonym_verb_match, overlap_ratio)

                    # Also check substring matching for partial matches
                    syn_text = syn.replace(' ', '').replace('_', '')
                    method_text_compact = method.name.replace('_', '')
                    if syn_text in method_text_compact or method_text_compact in syn_text:
                        synonym_verb_match = max(synonym_verb_match, 0.6)

            # IMPROVED: Object-noun matching with entity normalization
            object_match_score = 0.0
            normalized_entity_match = 0.0

            if object_nouns:
                # Direct matching - check if object word appears in method name
                # Require minimum length of 3 to avoid false positives from short strings
                # e.g., "st" in "steps" should NOT match, but "forward" in "forward" should
                matched_objects = sum(
                    1 for obj in object_nouns
                    if obj in method_name_lower and len(obj) >= 3
                )
                object_match_score = matched_objects / len(object_nouns) if object_nouns else 0

                # Normalized entity matching
                if object_nouns_normalized:
                    matched_normalized = sum(
                        1 for obj in object_nouns_normalized
                        if obj in method_name_lower and len(obj) >= 3
                    )
                    normalized_entity_match = matched_normalized / len(object_nouns_normalized) if object_nouns_normalized else 0

                # Take the better of the two
                object_match_score = max(object_match_score, normalized_entity_match)

            # Phrasal verb + object pattern matching
            phrasal_match = 0.0
            if '_' in action_verb:
                # e.g., "turn_off" -> ["turn", "off"]
                verb_parts = action_verb.split('_')

                # Check if all verb parts appear in method name
                all_parts_match = all(part in method_name_lower for part in verb_parts)

                if all_parts_match:
                    # Perfect match if object noun also in method name
                    if object_nouns and any(obj in method_name_lower for obj in object_nouns):
                        phrasal_match = 1.0
                    else:
                        # Partial match if just the phrasal verb matches
                        phrasal_match = 0.6
                else:
                    # Check synonym-based phrasal matching
                    # e.g., "close" might be synonym of "turn off"
                    if verb_synonyms and synonym_verb_match > 0:
                        for syn in verb_synonyms:
                            syn_parts = syn.replace(' ', '_').split('_')
                            if all(p in method_name_lower for p in syn_parts):
                                phrasal_match = 0.7
                                break

            # Verb-only matching (for non-phrasal verbs)
            # CRITICAL: Direct verb-to-method name match (e.g., "left" -> left())
            verb_match = 0.0
            if '_' not in action_verb:
                if action_verb.lower() == method_name_lower:
                    # Exact match: verb IS the method name
                    verb_match = 1.0
                elif action_verb.lower() in method_name_lower:
                    # Partial match: verb is part of method name
                    verb_match = 0.5

            # IMPROVED: Parameter extraction with numeric values
            param_score = 0.0
            extracted_params = {}

            # Extract numeric parameters
            numeric_params = self._extract_numeric_params(action_span, method)
            extracted_params.update(numeric_params)

            # Extract text-based parameters from noun chunks
            if noun_chunks and method.params:
                for chunk in noun_chunks:
                    chunk_lower = chunk.lower()
                    for param in method.params:
                        param_lower = param.lower()
                        # Skip if already extracted as numeric
                        if param not in extracted_params:
                            if param_lower in chunk_lower or chunk_lower in param_lower:
                                param_score = 0.5
                                extracted_params[param] = chunk
                                break

            # Boost score if we extracted numeric params
            if numeric_params:
                param_score = 1.0

            # Exact verb + object combination matching (highest priority)
            exact_match_score = 0.0
            if object_nouns_normalized:
                # Check if verb + object both appear in method name
                verb_in_method = action_verb.lower() in method_name_lower or any(
                    part in method_tokens for part in action_verb.split('_')
                )
                object_in_method = any(obj in method_name_lower for obj in object_nouns_normalized)

                if verb_in_method and object_in_method:
                    exact_match_score = 1.0

            # Word overlap boost (catches missed patterns) - using normalized entities
            action_full = f"{action_verb_normalized} {' '.join(object_nouns_normalized)}"
            action_words = set(action_full.split())
            word_overlap = len(action_words & method_words) / max(len(action_words), len(method_words))

            # Fuzzy string matching (for typo tolerance)
            fuzzy_score = 0.0
            # Compare action + objects with method name
            action_text = f"{action_verb} {' '.join(object_nouns_normalized)}".replace(' ', '_')
            fuzzy_score = SequenceMatcher(None, action_text, method.name).ratio()

            # SIMPLIFIED scoring - 4 clear factors (easier to debug)
            # Factor 1: Direct match (50%) - verb/phrasal verb matches method name
            direct_match = max(verb_match, phrasal_match, exact_match_score)

            # Factor 2: Synonym match (25%) - LLM-generated synonyms
            synonym_match = synonym_verb_match

            # Factor 3: Object/Entity match (15%) - objects in command match method
            entity_match = object_match_score

            # Factor 4: Semantic similarity (10%) - embedding-based fallback
            semantic_fallback = max(semantic_score, code_similarity)

            total = (
                direct_match * 0.50 +           # Direct verb/phrasal match
                synonym_match * 0.25 +          # Synonym-based match
                entity_match * 0.15 +           # Object/entity match
                semantic_fallback * 0.10        # Semantic similarity fallback
            )

            # Bonus for parameter extraction (small boost, not a primary factor)
            if param_score > 0:
                total = min(total + 0.05, 1.0)

            scores.append(MatchScore(
                method_name=method.name,
                total_score=total,
                semantic_score=semantic_fallback,  # Combined semantic score
                intent_score=entity_match,         # Object/entity match
                synonym_boost=synonym_match,       # Synonym-based match
                param_relevance=param_score,
                phrasal_verb_match=direct_match,   # Direct match (verb/phrasal/exact)
                extracted_params=extracted_params
            ))

        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores


def process_command(command: str, methods: List[MethodInfo], pipeline: NLPPipeline = None, language: str = None) -> dict:
    """
    Convenience function to process a command.
    If pipeline is None, creates a new one (use for one-off commands).
    For multiple commands, reuse the same pipeline instance.

    Args:
        command: Natural language command
        methods: List of available methods
        pipeline: Reusable pipeline instance (optional)
        language: Language code ('en', 'th') or None for auto-detect
    """
    if pipeline is None:
        pipeline = NLPPipeline()
        pipeline.initialize(methods)

    results = pipeline.process_command(command, methods, language=language)

    if not results:
        return {
            "success": False,
            "message": "No matching methods found"
        }

    # Return the top match
    action_verb, match_score = results[0]

    return {
        "success": True,
        "method_call": match_score.get_method_call(),
        "confidence": match_score.total_score,
        "explanation": match_score.explain(),
        "extracted_params": match_score.extracted_params
    }
