import ast
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from datetime import datetime as time

load_dotenv('backend/app/nlp_v2/.env')


@dataclass
class MethodInfo:
    name: str
    params: List[str]
    docstring: Optional[str]

    def to_searchable_text(self) -> str:
        text = self.name.replace('_', ' ')
        if self.docstring:
            text += f" {self.docstring}"
        return text


def extract_methods_from_file(filepath: str) -> List[MethodInfo]:
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())

    methods = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if item.name.startswith('_'):
                        continue

                    params = [arg.arg for arg in item.args.args if arg.arg != 'self']
                    docstring = ast.get_docstring(item)

                    methods.append(MethodInfo(
                        name=item.name,
                        params=params,
                        docstring=docstring
                    ))

            break

    return methods


class LocalSemanticMatcher:
    def __init__(self):
        try:
            from sentence_transformers import SentenceTransformer, util
            # Use faster model with similar performance
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.util = util
            self.available = True
            self.use_codebert = False

            # Try to load CodeBERT for code-specific matching
            try:
                self.code_model = SentenceTransformer('microsoft/codebert-base')
                self.use_codebert = True
                print("  CodeBERT loaded for code-aware similarity")
            except Exception:
                self.use_codebert = False

        except ImportError:
            self.available = False
            self.use_codebert = False

    def compute_similarity(self, text1: str, text2: str) -> float:
        if not self.available:
            raise RuntimeError("Sentence Transformer not available - no fallbacks allowed in POC")

        embeddings = self.model.encode([text1, text2])
        similarity = self.util.cos_sim(embeddings[0], embeddings[1])
        return float(similarity[0][0])

    def compute_code_similarity(self, command: str, method_name: str) -> float:
        """Compute similarity using code-aware model"""
        if not self.use_codebert:
            return 0.0

        try:
            # Format for CodeBERT (works better with natural + code pairs)
            embeddings = self.code_model.encode([command, method_name])
            similarity = self.util.cos_sim(embeddings[0], embeddings[1])
            return float(similarity[0][0])
        except Exception:
            return 0.0



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


class ClaudeSynonymGenerator:
    def __init__(self):
        try:
            from anthropic import Anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            self.client = Anthropic(api_key=api_key) if api_key else None
            self.available = self.client is not None
            self.cache = {}  # Cache to avoid repeated API calls
            self.synonym_dict = {}  # Structured synonym dictionary from methods
            self.prewarmed = False
        except ImportError:
            self.available = False
            self.cache = {}
            self.synonym_dict = {}
            self.prewarmed = False

    def get_synonyms(self, word: str, context: str = "") -> List[str]:
        if not self.available:
            return []

        # Check cache first
        cache_key = f"{word}:{context}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            prompt = f"List 5-10 synonyms or alternative ways to say '{word}' in smart home voice commands"
            if context:
                prompt += f" when referring to '{context}'"
            prompt += ". Include phrasal verbs and casual language. Return only comma-separated words/phrases, no explanations."

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )

            response = message.content[0].text.strip()
            synonyms = [s.strip().lower() for s in response.split(',')]

            # Cache the result
            self.cache[cache_key] = synonyms
            return synonyms
        except Exception:
            return []

    def are_synonyms(self, word1: str, word2: str) -> bool:
        """Check if two words are synonyms of each other"""
        word1_syns = self.get_synonyms(word1)
        word2_syns = self.get_synonyms(word2)

        word1_lower = word1.lower().replace('_', ' ')
        word2_lower = word2.lower().replace('_', ' ')

        # Check bidirectional synonym relationship
        return (word2_lower in word1_syns or
                word1_lower in word2_syns or
                bool(set(word1_syns) & set(word2_syns)))

    def build_method_synonym_dict(self, methods: List[MethodInfo]) -> Dict[str, List[str]]:
        """Build comprehensive synonym dictionary from method list using single LLM call"""
        if not self.available:
            raise RuntimeError("LLM not available - cannot build synonym dictionary")

        # Extract structured patterns from methods
        verbs = set()
        phrasal_verbs = set()
        entities = set()

        for method in methods:
            tokens = method.name.split('_')

            if len(tokens) >= 1:
                verbs.add(tokens[0])

            if len(tokens) >= 2:
                # Phrasal verbs: turn_on, turn_off, set_temperature
                if tokens[1] in ['on', 'off', 'up', 'down']:
                    phrasal_verbs.add(f"{tokens[0]}_{tokens[1]}")
                else:
                    # verb + noun: set_temperature, increase_temperature
                    phrasal_verbs.add(f"{tokens[0]}_{tokens[1]}")

            # Extract entities (middle tokens, last tokens)
            for i in range(1, len(tokens)):
                if tokens[i] not in ['on', 'off', 'up', 'down']:
                    entities.add(tokens[i])

        # Single LLM call to generate ALL synonyms at once
        prompt = f"""Generate synonym dictionaries for a Python API with these methods:
{chr(10).join(f"- {m.name}" for m in methods)}

Create 3 synonym maps in JSON format:

1. VERBS (actions): {', '.join(sorted(verbs))}
2. PHRASAL_VERBS (compound actions): {', '.join(sorted(phrasal_verbs))}
3. ENTITIES (objects/nouns): {', '.join(sorted(entities))}

For each term, provide 10-20 natural language synonyms users might say.
Return ONLY valid JSON, no explanations:

{{
  "verbs": {{"turn": ["switch", "flip", ...], ...}},
  "phrasal_verbs": {{"turn_on": ["switch on", "activate", ...], ...}},
  "entities": {{"light": ["lamp", "lights", ...], ...}}
}}"""

        print(f"  Calling LLM once to generate synonym dictionary for:")
        print(f"    - {len(verbs)} verbs")
        print(f"    - {len(phrasal_verbs)} phrasal verbs")
        print(f"    - {len(entities)} entities")

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            response = message.content[0].text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if '```' in response:
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)

            import json
            synonym_dict = json.loads(response)

            # Flatten into cache format
            total_synonyms = 0
            for category in ['verbs', 'phrasal_verbs', 'entities']:
                if category in synonym_dict:
                    for term, syns in synonym_dict[category].items():
                        # Cache with empty context for verbs, "device or object name" for entities
                        context = "device or object name" if category == 'entities' else ""
                        cache_key = f"{term.replace('_', ' ')}:{context}"
                        self.cache[cache_key] = [s.lower() for s in syns]
                        total_synonyms += len(syns)

            print(f"  ✓ Generated {total_synonyms} synonyms in single LLM call")
            return synonym_dict

        except Exception as e:
            print(f"  Failed to parse LLM response: {e}")
            print(f"  Response was: {response[:200]}...")
            raise

    def prewarm_cache(self, methods: List[MethodInfo]):
        """Build synonym dictionary from methods using single LLM call"""
        if self.prewarmed or not self.available:
            return

        self.synonym_dict = self.build_method_synonym_dict(methods)
        self.prewarmed = True


class ZeroShotIntentClassifier:
    def __init__(self):
        try:
            from transformers import pipeline
            self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            self.available = True
        except (ImportError, Exception):
            self.available = False

    def classify_intent(self, text: str, candidate_labels: List[str]) -> Dict[str, float]:
        if not self.available or not candidate_labels:
            raise RuntimeError("Zero-shot classifier not available - no fallbacks allowed in POC")

        result = self.classifier(text, candidate_labels)
        return dict(zip(result['labels'], result['scores']))


@dataclass
class MatchScore:
    method_name: str
    total_score: float
    semantic_score: float
    intent_score: float
    synonym_boost: float
    param_relevance: float
    phrasal_verb_match: float
    extracted_params: Dict[str, str]

    def get_method_call(self) -> str:
        if not self.extracted_params:
            return f"{self.method_name}()"
        params_str = ", ".join(f"{k}={repr(v)}" for k, v in self.extracted_params.items())
        return f"{self.method_name}({params_str})"

    def explain(self) -> str:
        explanation = [
            f"Method: {self.get_method_call()}",
            f"Total Confidence: {self.total_score:.1%}",
            "",
            "Breakdown:",
            f"  Semantic similarity: {self.semantic_score:.1%}",
            f"  Intent classification: {self.intent_score:.1%}",
            f"  Synonym boost: {self.synonym_boost:.1%}",
            f"  Parameter relevance: {self.param_relevance:.1%}",
            f"  Phrasal verb match: {self.phrasal_verb_match:.1%}",
        ]
        return "\n".join(explanation)


class EntityNormalizer:
    """Normalizes entities (nouns/devices) by learning from method names and using LLM"""

    def __init__(self, methods: List[MethodInfo], synonym_generator=None):
        self.entity_map = {}
        self.synonym_generator = synonym_generator
        self._build_from_methods(methods)

    def _build_from_methods(self, methods: List[MethodInfo]):
        """Extract device/entity names from method signatures and build normalization map"""
        if not self.synonym_generator or not self.synonym_generator.available:
            raise RuntimeError("EntityNormalizer requires LLM synonym generator - no fallbacks allowed in POC")

        # Extract entities from synonym_dict (already built by prewarm_cache)
        if 'entities' in self.synonym_generator.synonym_dict:
            entities_from_dict = self.synonym_generator.synonym_dict['entities']

            print(f"  Building entity map from {len(entities_from_dict)} entities in synonym dictionary")

            # Build identity mappings first
            for entity in entities_from_dict.keys():
                self.entity_map[entity] = entity

            # Map all synonyms to canonical names
            for entity, synonyms in entities_from_dict.items():
                for syn in synonyms:
                    syn_normalized = syn.replace(' ', '_').replace('-', '_')
                    self.entity_map[syn_normalized] = entity
                    syn_compact = syn.replace(' ', '').replace('-', '')
                    if syn_compact != syn_normalized:
                        self.entity_map[syn_compact] = entity

            print(f"  ✓ Entity map built: {len(self.entity_map)} mappings")
        else:
            raise RuntimeError("Synonym dictionary not initialized - call prewarm_cache first")

    def normalize(self, text: str) -> str:
        """Normalize entities in text"""
        words = text.lower().replace('-', '_').split()
        normalized = []

        for word in words:
            # Try exact match first
            if word in self.entity_map:
                normalized.append(self.entity_map[word])
            else:
                # Try without special chars
                clean_word = word.replace('_', '').replace('-', '')
                normalized.append(self.entity_map.get(clean_word, word))

        return ' '.join(normalized)


class HonestNLPPipeline:
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
        top_k: int = 1
    ) -> List[Tuple[str, MatchScore]]:
        actions = self.dependency_parser.extract_actions(command)

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
        """Extract numeric parameters using dependency parsing"""
        doc = self.dependency_parser.nlp(command)
        params = {}
        
        numbers = []
        for token in doc:
            if token.like_num or token.pos_ == "NUM":
                try:
                    value = float(token.text) if '.' in token.text else int(token.text)
                    numbers.append(value)
                except ValueError:
                    try:
                        from word2number import w2n
                        word_value = w2n.word_to_num(token.text)
                        numbers.append(word_value)
                    except (ValueError, ImportError):
                        continue
        
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
                # Direct matching (original)
                matched_objects = sum(1 for obj in object_nouns if obj in method_name_lower)
                object_match_score = matched_objects / len(object_nouns) if object_nouns else 0

                # Normalized entity matching (NEW)
                if object_nouns_normalized:
                    matched_normalized = sum(1 for obj in object_nouns_normalized if obj in method_name_lower)
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
            verb_match = 0.0
            if not '_' in action_verb:
                if action_verb.lower() in method_name_lower:
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
            from difflib import SequenceMatcher
            # Compare action + objects with method name
            action_text = f"{action_verb} {' '.join(object_nouns_normalized)}".replace(' ', '_')
            fuzzy_score = SequenceMatcher(None, action_text, method.name).ratio()

            # REBALANCED scoring weights - prioritize deterministic matches
            total = (
                exact_match_score * 0.35 +      # NEW - Exact verb+object match (highest priority)
                synonym_verb_match * 0.22 +     # LLM-powered synonym matching
                object_match_score * 0.18 +     # Entity/object matching with normalization
                phrasal_match * 0.10 +          # Phrasal verb patterns
                code_similarity * 0.08 +        # NEW - CodeBERT similarity (code-aware)
                semantic_score * 0.04 +         # Semantic similarity (safety net only)
                param_score * 0.02 +            # Parameter extraction bonus
                fuzzy_score * 0.01              # NEW - Fuzzy matching for typos
            )

            scores.append(MatchScore(
                method_name=method.name,
                total_score=total,
                semantic_score=semantic_score,
                intent_score=object_match_score,  # Reusing this field for object match
                synonym_boost=synonym_verb_match, # Now actually storing synonym match score
                param_relevance=param_score,
                phrasal_verb_match=phrasal_match, # Storing actual phrasal match
                extracted_params=extracted_params
            ))

        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores


def run_poc(filepath: str, test_commands: List[str]):
    print("="*70)
    print("HONEST NLP PIPELINE POC - MULTI-STAGE ARCHITECTURE")
    print("="*70)
    print()

    print("Analyzing uploaded Python file...")
    methods = extract_methods_from_file(filepath)

    print(f"Found {len(methods)} public methods:")
    for i, method in enumerate(methods, 1):
        params_str = f"({', '.join(method.params)})" if method.params else "()"
        print(f"  {i}. {method.name}{params_str}")
    print()

    print("Initializing NLP pipeline...")
    pipeline = HonestNLPPipeline()
    pipeline.initialize(methods)
    print()

    print("Processing commands...")
    print("="*70)
    print(time.now())
    print()

    for cmd_idx, command in enumerate(test_commands, 1):
        print(f"Command {cmd_idx}: \"{command}\"")
        print("-" * 70)

        results = pipeline.process_command(command, methods)

        if not results:
            print("No matches found")
            print()
            continue

        for action_verb, match_score in results:
            print(f"\nAction: {action_verb}")
            print(match_score.explain())
            print()

            confidence = match_score.total_score
            if confidence >= 0.7:
                print("HIGH CONFIDENCE")
            elif confidence >= 0.4:
                print("MEDIUM CONFIDENCE")
            else:
                print("LOW CONFIDENCE")
            print()

        print("="*70)
        print()
        print(time.now())


if __name__ == "__main__":
    sample_code = '''
class Calculator:
    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b

    def multiply(self, a, b):
        return a * b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

'''

    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample_code)
        temp_file = f.name

    try:
        test_commands = [
            "add 100 and 250 then divide 10 by 5",
            "multiply 12 with 4 and add 5 to 10",
            "subtract five from twenty, then multiply nine by 0",
        ]

        run_poc(temp_file, test_commands)

    finally:
        os.unlink(temp_file)
