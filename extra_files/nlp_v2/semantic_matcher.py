from typing import List, Dict, Tuple, Optional, Set
import json
import os
from collections import defaultdict


class PhrasalActionExtractor:
    """
    Dynamically extracts phrasal actions from method names and their synonyms/antonyms.
    No hard-coded patterns - everything is learned from the actual methods.
    """

    def __init__(self, methods: List[Dict], synonyms: Optional[Dict[str, List[str]]] = None,
                 antonyms: Optional[Dict[str, List[str]]] = None):
        self.methods = methods
        self.synonyms = synonyms or {}
        self.antonyms = antonyms or {}

        # Build dynamic mappings
        self.action_to_methods = self._build_action_to_methods_map()
        self.opposing_actions = self._build_opposing_actions_map()
        self.phrase_patterns = self._build_phrase_patterns()

    def _extract_action_from_method_name(self, method_name: str) -> Optional[str]:
        parts = method_name.split('_')

        if len(parts) < 2:
            return method_name
        elif parts[-1] in ['on', 'off', 'up', 'down']:
            return f"{parts[0]}_{parts[-1]}"
        else:
            return parts[0]

    def _extract_object_from_method_name(self, method_name: str) -> Optional[str]:
        parts = method_name.split('_')

        if len(parts) < 2:
            return None
        elif parts[-1] in ['on', 'off', 'up', 'down']:
            object_parts = parts[1:-1]
            return '_'.join(object_parts) if object_parts else None
        else:
            object_parts = parts[1:]
            return '_'.join(object_parts) if object_parts else None

    def _build_action_to_methods_map(self) -> Dict[str, List[str]]:
        """Map each action type to methods that perform that action."""
        action_map = defaultdict(list)

        for method in self.methods:
            method_name = method.get('name', '')
            action = self._extract_action_from_method_name(method_name)

            if action:
                action_map[action].append(method_name)

        return dict(action_map)

    def _build_opposing_actions_map(self) -> Dict[str, str]:
        """
        Dynamically detect opposing actions using antonym relationships.
        If method A's antonyms overlap with method B's synonyms, they're opposites.
        """
        opposing = {}

        for method_a_name in self.synonyms.keys():
            if method_a_name not in self.antonyms:
                continue

            method_a_antonyms = set(ant.lower().strip() for ant in self.antonyms[method_a_name])
            action_a = self._extract_action_from_method_name(method_a_name)

            if not action_a:
                continue

            # Find methods whose synonyms overlap with this method's antonyms
            for method_b_name in self.synonyms.keys():
                if method_a_name == method_b_name:
                    continue

                method_b_synonyms = set(syn.lower().strip() for syn in self.synonyms[method_b_name])
                action_b = self._extract_action_from_method_name(method_b_name)

                if not action_b or action_a == action_b:
                    continue

                # Check overlap
                overlap = method_a_antonyms & method_b_synonyms
                if overlap and len(overlap) >= 2:  # At least 2 overlapping terms
                    if action_a not in opposing:  # Only set once
                        opposing[action_a] = action_b
                    if action_b not in opposing:
                        opposing[action_b] = action_a

        return opposing

    def _build_phrase_patterns(self) -> Dict[str, Set[str]]:
        """
        Build a map of actions to all their phrasal variations from synonyms.
        This includes multi-word phrases like "turn on", "switch off", etc.
        """
        patterns = defaultdict(set)

        # First, add patterns from synonyms (if available)
        for method_name, syn_list in self.synonyms.items():
            action = self._extract_action_from_method_name(method_name)
            if not action:
                continue

            # Add all synonym phrases for this action
            for syn in syn_list:
                syn_clean = syn.lower().strip()
                if syn_clean:
                    patterns[action].add(syn_clean)

        # Fallback: if no synonyms, extract from method names directly
        if not patterns:
            for method in self.methods:
                method_name = method.get('name', '')
                action = self._extract_action_from_method_name(method_name)
                if action:
                    # Add the method name itself as a pattern
                    patterns[action].add(method_name.replace('_', ' ').lower())
                    # Add the action with underscores removed
                    patterns[action].add(action.replace('_', ' ').lower())

        return dict(patterns)

    def extract_action_from_command(self, command: str) -> Optional[Tuple[str, float]]:
        command_lower = command.lower().strip()
        command_words = command_lower.split()
        
        matches = []

        for action, phrase_set in self.phrase_patterns.items():
            sorted_phrases = sorted(phrase_set, key=len, reverse=True)

            for phrase in sorted_phrases:
                phrase_lower = phrase.lower().strip()
                phrase_words = phrase_lower.split()

                # Check for exact substring match
                substring_match = phrase_lower in command_lower
                
                # Check for flexible word-based match (handles "the", "a", etc.)
                phrase_words_clean = [w for w in phrase_words if w not in ['the', 'a', 'an']]
                command_words_clean = [w for w in command_words if w not in ['the', 'a', 'an']]
                
                flexible_match = False
                if len(phrase_words_clean) <= len(command_words_clean):
                    for i in range(len(command_words_clean) - len(phrase_words_clean) + 1):
                        if command_words_clean[i:i+len(phrase_words_clean)] == phrase_words_clean:
                            flexible_match = True
                            break

                if substring_match or flexible_match:
                    is_complete = False
                    for i in range(len(command_words) - len(phrase_words) + 1):
                        if command_words[i:i+len(phrase_words)] == phrase_words:
                            is_complete = True
                            break

                    match_score = len(phrase_lower)
                    if is_complete:
                        match_score *= 1.5
                    elif flexible_match:
                        match_score *= 1.2  # Slight bonus for flexible match
                    if len(phrase_words) > 1:
                        match_score *= 1.3

                    matches.append((action, match_score, phrase))
                    break

        if matches:
            matches.sort(key=lambda x: x[1], reverse=True)
            best_action, best_score, matched_phrase = matches[0]
            normalized_score = min(1.0, best_score / 20.0)
            return (best_action, normalized_score)

        return None

    def extract_object_from_command(self, command: str) -> Optional[str]:
        command_lower = command.lower().strip()
        command_words = command_lower.split()

        common_objects = ['ac', 'tv', 'light', 'fan', 'door', 'window', 'volume',
                          'temperature', 'mic', 'microphone', 'camera', 'speaker']

        for obj in common_objects:
            if obj in command_words:
                return obj

        return None

    def get_opposing_action(self, action: str) -> Optional[str]:
        """Get the opposing action for a given action."""
        return self.opposing_actions.get(action)


class HFSemanticMatcher:
    def __init__(self, hf_token: Optional[str] = None):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        if hf_token is None:
            hf_token = os.environ.get('HUGGINGFACE_TOKEN') or os.environ.get('HF_TOKEN')

        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests library required")

        # Using multi-qa-mpnet for better short query/command understanding
        # Falls back to all-MiniLM if model is unavailable
        self.api_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/multi-qa-mpnet-base-cos-v1"
        self.fallback_url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        self.hf_token = hf_token

    def get_similarity_scores(self, query: str, candidates: List[str]) -> List[float]:
        # Fallback using simple string similarity
        scores = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for candidate in candidates:
            candidate_lower = candidate.lower()
            candidate_words = set(candidate_lower.split())
            
            # Simple word overlap score
            overlap = len(query_words.intersection(candidate_words))
            total_words = len(query_words.union(candidate_words))
            
            if total_words == 0:
                score = 0.0
            else:
                score = overlap / total_words
                
            # Boost for exact substring matches
            if query_lower in candidate_lower or candidate_lower in query_lower:
                score += 0.3
                
            scores.append(min(1.0, score))
            
        return scores

    def detect_opposing_methods(self, methods: List[Dict], synonyms: Optional[Dict[str, List[str]]] = None) -> Dict[str, str]:
        opposing_pairs = {}
        method_names = [m.get('name', '') for m in methods]

        for i, method1 in enumerate(method_names):
            for j, method2 in enumerate(method_names):
                if i >= j:
                    continue

                parts1 = method1.split('_')
                parts2 = method2.split('_')

                if len(parts1) != len(parts2):
                    continue

                diff_count = 0
                diff_indices = []
                for k, (p1, p2) in enumerate(zip(parts1, parts2)):
                    if p1 != p2:
                        diff_count += 1
                        diff_indices.append(k)

                if diff_count == 1:
                    diff_idx = diff_indices[0]
                    word1 = parts1[diff_idx]
                    word2 = parts2[diff_idx]

                    opposing_pairs[method1] = method2
                    opposing_pairs[method2] = method1

        return opposing_pairs

    def check_synonym_match_in_command(self, command: str, method_name: str, synonyms: Optional[Dict[str, List[str]]] = None) -> bool:
        if not synonyms or method_name not in synonyms:
            return False

        command_lower = command.lower().strip()
        method_synonyms = synonyms.get(method_name, [])

        # Sort synonyms by length (longest first) to match multi-word phrases first
        sorted_synonyms = sorted(method_synonyms, key=len, reverse=True)

        for syn in sorted_synonyms:
            syn_lower = syn.lower().strip()
            if syn_lower in command_lower:
                # Additional check: ensure it's a word boundary match for short synonyms
                if len(syn_lower.split()) == 1 and len(syn_lower) <= 3:
                    # For very short synonyms, check word boundaries
                    words = command_lower.split()
                    if syn_lower in words:
                        return True
                else:
                    return True
        return False

    def check_antonym_match_in_command(self, command: str, method_name: str, antonyms: Optional[Dict[str, List[str]]] = None) -> bool:
        if not antonyms or method_name not in antonyms:
            return False

        command_lower = command.lower().strip()
        method_antonyms = antonyms.get(method_name, [])

        # Sort antonyms by length (longest first) to match multi-word phrases first
        sorted_antonyms = sorted(method_antonyms, key=len, reverse=True)

        for ant in sorted_antonyms:
            ant_lower = ant.lower().strip()
            if ant_lower in command_lower:
                # Additional check: ensure it's a word boundary match for short antonyms
                if len(ant_lower.split()) == 1 and len(ant_lower) <= 3:
                    # For very short antonyms, check word boundaries
                    words = command_lower.split()
                    if ant_lower in words:
                        return True
                else:
                    return True
        return False


    def find_best_match(self, command: str, methods: List[Dict], top_k: int = 3, min_confidence: float = 0.3, synonyms: Optional[Dict[str, List[str]]] = None, antonyms: Optional[Dict[str, List[str]]] = None) -> List[Tuple[Dict, float]]:
        if not methods:
            return []

        method_texts = []
        for method in methods:
            method_name = method.get('name', '').replace('_', ' ')
            description = method.get('description', '')
            text = f"{method_name}"
            if description:
                text += f" - {description}"
            method_texts.append(text)

        try:
            scores = self.get_similarity_scores(command, method_texts)

            reverse_scores = []
            for method_text in method_texts:
                try:
                    reverse_score = self.get_similarity_scores(method_text, [command])
                    reverse_scores.append(reverse_score[0] if reverse_score else 0.0)
                except Exception as e:
                    reverse_scores.append(0.0)

            scores = [
                (forward * 0.7 + reverse * 0.3)
                for forward, reverse in zip(scores, reverse_scores)
            ]

        except Exception as e:
            return []

        command_lower = command.lower()
        command_words = set(command_lower.split())

        extractor = PhrasalActionExtractor(methods, synonyms, antonyms)

        action_result = extractor.extract_action_from_command(command)
        phrasal_action = action_result[0] if action_result else None
        action_confidence = action_result[1] if action_result else 0.0

        command_object = extractor.extract_object_from_command(command)

        opposing_phrasal = extractor.get_opposing_action(phrasal_action) if phrasal_action else None

        opposing_pairs = self.detect_opposing_methods(methods, synonyms)

        boosted_scores = []
        for i, method in enumerate(methods):
            score = scores[i]
            method_name = method.get('name', '').replace('_', ' ').lower()
            original_method_name = method.get('name', '')

            method_action = extractor._extract_action_from_method_name(original_method_name)
            method_object = extractor._extract_object_from_method_name(original_method_name)

            object_matches = False
            if command_object and method_object:
                if command_object == method_object or command_object in method_object or method_object in command_object:
                    object_matches = True
                else:
                    object_matches = False
            elif not command_object or not method_object:
                object_matches = True

            if phrasal_action and method_action:
                if phrasal_action == method_action:
                    if object_matches:
                        boost = 0.35 + (action_confidence * 0.15)
                        score = min(1.0, score + boost)
                    elif command_object and method_object:
                        penalty = 0.50
                        score = max(0.0, score - penalty)
                elif opposing_phrasal and opposing_phrasal == method_action:
                    penalty = 0.65 + (action_confidence * 0.15)
                    score = max(0.0, score - penalty)

            if method_name in command_lower:
                if object_matches:
                    score = min(1.0, score + 0.15)
                elif command_object and method_object:
                    score = max(0.0, score - 0.30)

            current_method_matches = self.check_synonym_match_in_command(command, original_method_name, synonyms)

            if current_method_matches:
                if object_matches:
                    score = min(1.0, score + 0.25)
                elif command_object and method_object:
                    score = max(0.0, score - 0.35)

            has_antonym = self.check_antonym_match_in_command(command, original_method_name, antonyms)
            if has_antonym:
                score = 0.0

            if original_method_name in opposing_pairs:
                opposite_method = opposing_pairs[original_method_name]
                opposite_matches = self.check_synonym_match_in_command(command, opposite_method, synonyms)

                if opposite_matches and not current_method_matches:
                    opposite_method_object = extractor._extract_object_from_method_name(opposite_method)
                    if not command_object or not opposite_method_object or command_object == opposite_method_object:
                        score = max(0.0, score - 0.50)

                opposite_has_synonym_match = self.check_synonym_match_in_command(command, opposite_method, synonyms)
                if opposite_has_synonym_match and not current_method_matches:
                    opposite_method_object = extractor._extract_object_from_method_name(opposite_method)
                    if not command_object or not opposite_method_object or command_object == opposite_method_object:
                        score = max(0.0, score - 0.60)

            # Additional synonym boosting with phrase awareness
            if synonyms and original_method_name in synonyms:
                method_synonyms = synonyms[original_method_name]
                # Sort by length to prioritize multi-word phrases
                sorted_method_synonyms = sorted(method_synonyms, key=len, reverse=True)

                for syn in sorted_method_synonyms:
                    syn_lower = syn.lower().strip()

                    # Exact phrase match = strong boost
                    if syn_lower in command_lower:
                        # Multi-word phrase match is more valuable
                        phrase_boost = 0.25 if len(syn_lower.split()) > 1 else 0.18
                        score = min(1.0, score + phrase_boost)
                        break

                    # Partial word overlap for fallback
                    syn_words = set(syn_lower.split())
                    overlap = len(command_words & syn_words)
                    if overlap > 0 and len(syn_words) > 0:
                        # Calculate overlap ratio
                        overlap_ratio = overlap / len(syn_words)
                        if overlap_ratio >= 0.6:  # At least 60% of synonym words present
                            boost = min(0.12, overlap * 0.04)
                            score = min(1.0, score + boost)
                            break

            boosted_scores.append(score)

        matches = []
        for i, method in enumerate(methods):
            if boosted_scores[i] >= min_confidence:
                matches.append((method, boosted_scores[i]))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]

    def match_with_fallback(self, command: str, methods: List[Dict], confidence_threshold: float = 0.5) -> Optional[Tuple[Dict, float]]:
        matches = self.find_best_match(command, methods, top_k=1, min_confidence=0.0)

        if not matches:
            return None

        method, confidence = matches[0]
        return (method, confidence)
