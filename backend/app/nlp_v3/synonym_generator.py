"""Synonym generation with static base + optional async LLM fallback"""

import os
import json
import re
import hashlib
import threading
from datetime import datetime
from typing import List, Dict, Tuple
from pathlib import Path
from dotenv import load_dotenv
from .models import MethodInfo

# Load .env from nlp_v3 directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Path to static synonym base
SYNONYMS_BASE_PATH = Path(__file__).parent / "synonyms_base.json"

# Path to dynamic synonym cache (generated from method docstrings)
DYNAMIC_CACHE_PATH = Path(__file__).parent / "dynamic_synonyms_cache.json"

# Feature flag to enable dynamic LLM synonym generation
# When enabled: ONE batch LLM call per conversation for unknown verbs
# Results persist to synonyms_base.json (cost: ~$0.001 per new method set, then free)
FEATURE_LLM_SYNONYMS = os.getenv("FEATURE_LLM_SYNONYMS", "true").lower() == "true"

# Domain-specific verb mappings (smart home context)
# These map user verbs to canonical method verbs with HIGH PRIORITY
# Checked BEFORE general synonyms for domain-aware matching
DOMAIN_VERB_MAP = {
    # on/off actions - critical for smart home
    "open": ["turn_on", "activate", "enable", "switch_on", "power_on"],
    "close": ["turn_off", "deactivate", "disable", "switch_off", "power_off"],
    "shut": ["turn_off", "close", "power_off"],
    "switch": ["turn", "toggle", "change"],
    "power": ["turn", "switch"],
    "activate": ["turn_on", "enable", "start"],
    "deactivate": ["turn_off", "disable", "stop"],
    # brightness/intensity
    "dim": ["decrease", "lower", "reduce", "darken"],
    "brighten": ["increase", "raise", "boost", "lighter"],
    # temperature
    "cool": ["decrease_temperature", "lower_temperature", "colder"],
    "warm": ["increase_temperature", "raise_temperature", "heat", "hotter"],
    "heat": ["increase_temperature", "warm", "hotter"],
    # general device control
    "adjust": ["set", "change", "modify", "configure"],
    "toggle": ["switch", "turn", "flip"],
}


class ClaudeSynonymGenerator:
    """
    Synonym generator with instant static loading + optional async LLM fallback.

    By default, loads synonyms from synonyms_base.json instantly (no network).
    If FEATURE_LLM_SYNONYMS=true, unknown words trigger async LLM call.
    """

    def __init__(self):
        self.cache = {}  # Cache for synonym lookups
        self.synonym_dict = {}  # Structured synonym dictionary
        self.dynamic_method_synonyms = {}  # Dynamic synonyms from method docstrings
        self.prewarmed = False
        self._lock = threading.Lock()

        # Load static synonyms immediately (instant, no network)
        self._load_static_synonyms()

        # Available is True if we have static synonyms loaded
        # (we can provide synonyms even without LLM)
        self.available = self.prewarmed and len(self.cache) > 0

        # Initialize LLM client only if feature is enabled (for fallback)
        self.client = None
        self.llm_available = False

        if FEATURE_LLM_SYNONYMS:
            try:
                from anthropic import Anthropic
                api_key = os.getenv('ANTHROPIC_API_KEY')
                if api_key:
                    self.client = Anthropic(api_key=api_key)
                    self.llm_available = True
                    print("[SynonymGenerator] LLM fallback enabled for unknown words")
            except ImportError:
                pass

    def _load_static_synonyms(self) -> None:
        """Load synonyms from static JSON file (instant, no network)."""
        try:
            if SYNONYMS_BASE_PATH.exists():
                with open(SYNONYMS_BASE_PATH, 'r') as f:
                    self.synonym_dict = json.load(f)

                # Flatten into cache format for fast lookup
                total_synonyms = 0
                for category in ['verbs', 'phrasal_verbs', 'entities']:
                    if category in self.synonym_dict:
                        for term, syns in self.synonym_dict[category].items():
                            # Cache with empty context for verbs, "device or object name" for entities
                            context = "device or object name" if category == 'entities' else ""
                            cache_key = f"{term.replace('_', ' ')}:{context}"
                            self.cache[cache_key] = [s.lower() for s in syns]
                            total_synonyms += len(syns)

                self.prewarmed = True
                print(f"[SynonymGenerator] Loaded {total_synonyms} synonyms from static base")
            else:
                print(f"[SynonymGenerator] Warning: {SYNONYMS_BASE_PATH} not found")
        except Exception as e:
            print(f"[SynonymGenerator] Error loading static synonyms: {e}")

    def get_synonyms(self, word: str, context: str = "") -> List[str]:
        """
        Get synonyms for a word. Uses dynamic method synonyms first, then domain mapping, then cache.

        Args:
            word: The word to find synonyms for
            context: Optional context (e.g., "device or object name")

        Returns:
            List of synonyms (may be empty if word is unknown and LLM disabled)
        """
        word_lower = word.lower()

        # PRIORITY 0: Check dynamic method synonyms (generated from docstrings)
        if word_lower in self.dynamic_method_synonyms:
            return self.dynamic_method_synonyms[word_lower]

        # PRIORITY 1: Check domain-specific mapping (smart home verbs)
        if word_lower in DOMAIN_VERB_MAP:
            return DOMAIN_VERB_MAP[word_lower]

        # PRIORITY 2: Check cache (includes static synonyms from JSON)
        cache_key = f"{word}:{context}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Also check without context
        cache_key_no_context = f"{word}:"
        if cache_key_no_context in self.cache:
            return self.cache[cache_key_no_context]

        # Check if word matches any synonym (reverse lookup)
        for key, synonyms in self.cache.items():
            if word.lower() in [s.lower() for s in synonyms]:
                # Return the canonical term + other synonyms
                canonical = key.split(':')[0]
                return [canonical] + [s for s in synonyms if s.lower() != word.lower()]

        # If LLM fallback is disabled, return empty
        if not self.llm_available or not FEATURE_LLM_SYNONYMS:
            return []

        # LLM fallback for unknown words (blocking, but rare)
        return self._fetch_synonyms_from_llm(word, context)

    def _fetch_synonyms_from_llm(self, word: str, context: str = "") -> List[str]:
        """Fetch synonyms from LLM (blocking call, use sparingly)."""
        try:
            prompt = f"List 5-10 synonyms or alternative ways to say '{word}' in programming/voice commands"
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

            # Cache the result for future use
            cache_key = f"{word}:{context}"
            with self._lock:
                self.cache[cache_key] = synonyms

            # Optionally persist to JSON for future startups
            self._persist_new_synonyms(word, synonyms, context)

            return synonyms
        except Exception as e:
            print(f"[SynonymGenerator] LLM fallback failed for '{word}': {e}")
            return []

    def _persist_new_synonyms(self, word: str, synonyms: List[str], context: str = "") -> None:
        """Persist newly discovered synonyms to JSON file for future use."""
        try:
            # Determine category based on context
            if context and "device" in context.lower():
                category = "entities"
            elif '_' in word or ' ' in word:
                category = "phrasal_verbs"
            else:
                category = "verbs"

            # Load current file
            with self._lock:
                if SYNONYMS_BASE_PATH.exists():
                    with open(SYNONYMS_BASE_PATH, 'r') as f:
                        data = json.load(f)
                else:
                    data = {"verbs": {}, "phrasal_verbs": {}, "entities": {}}

                # Add new synonyms
                normalized_word = word.replace(' ', '_')
                if category not in data:
                    data[category] = {}
                if normalized_word not in data[category]:
                    data[category][normalized_word] = synonyms

                    # Write back
                    with open(SYNONYMS_BASE_PATH, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"[SynonymGenerator] Persisted new synonyms for '{word}'")
        except Exception as e:
            print(f"[SynonymGenerator] Failed to persist synonyms: {e}")

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
        """
        Build synonym dictionary from method list.

        With static base, this is mostly a no-op since synonyms are pre-loaded.
        Only makes LLM call if FEATURE_LLM_SYNONYMS=true and methods have unknown verbs.
        """
        if not FEATURE_LLM_SYNONYMS or not self.llm_available:
            # Just return what we have from static base
            return self.synonym_dict

        # Extract verbs from methods that aren't in our cache
        unknown_verbs = set()
        for method in methods:
            tokens = method.name.split('_')
            if tokens:
                verb = tokens[0]
                cache_key = f"{verb}:"
                if cache_key not in self.cache:
                    unknown_verbs.add(verb)

        if not unknown_verbs:
            return self.synonym_dict

        # Make single LLM call for unknown verbs
        print(f"[SynonymGenerator] Fetching synonyms for {len(unknown_verbs)} unknown verbs via LLM...")

        try:
            prompt = f"""Generate synonyms for these programming verbs:
{', '.join(sorted(unknown_verbs))}

Return JSON format:
{{"verb1": ["syn1", "syn2"], "verb2": ["syn1", "syn2"]}}"""

            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response = message.content[0].text.strip()

            # Extract JSON from response
            if '```' in response:
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)

            new_synonyms = json.loads(response)

            # Add to cache and persist
            for verb, syns in new_synonyms.items():
                cache_key = f"{verb}:"
                self.cache[cache_key] = [s.lower() for s in syns]
                self._persist_new_synonyms(verb, syns)

            print(f"[SynonymGenerator] Added {len(new_synonyms)} new verbs to cache")

        except Exception as e:
            print(f"[SynonymGenerator] LLM batch call failed: {e}")

        return self.synonym_dict

    def prewarm_cache(self, methods: List[MethodInfo]):
        """
        Pre-warm synonym cache from methods.

        With static base, this is mostly instant since synonyms are pre-loaded.
        Only makes LLM call if FEATURE_LLM_SYNONYMS=true.
        """
        if self.prewarmed and not FEATURE_LLM_SYNONYMS:
            print("[SynonymGenerator] Cache already pre-warmed from static base")
            return

        self.synonym_dict = self.build_method_synonym_dict(methods)
        self.prewarmed = True

    # =========================================================================
    # Dynamic Synonym Generation (from method docstrings)
    # =========================================================================

    def _load_dynamic_cache(self) -> Dict:
        """Load dynamic synonym cache from file."""
        try:
            if DYNAMIC_CACHE_PATH.exists():
                with open(DYNAMIC_CACHE_PATH, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[SynonymGenerator] Error loading dynamic cache: {e}")
        return {"cache_version": 1, "methods": {}}

    def _save_dynamic_cache(self, cache: Dict) -> None:
        """Save dynamic synonym cache to file."""
        try:
            with self._lock:
                with open(DYNAMIC_CACHE_PATH, 'w') as f:
                    json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"[SynonymGenerator] Error saving dynamic cache: {e}")

    def _compute_method_hash(self, method: MethodInfo) -> str:
        """Hash method name + docstring for cache key."""
        content = f"{method.name}:{method.docstring or ''}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _flatten_dynamic_cache(self, cache: Dict) -> Dict[str, List[str]]:
        """Convert cache structure to flat method_name -> synonyms mapping."""
        result = {}
        for entry in cache.get("methods", {}).values():
            method_name = entry.get("method_name", "")
            synonyms = entry.get("synonyms", [])
            if method_name and synonyms:
                result[method_name.lower()] = synonyms
        return result

    def build_dynamic_synonyms(self, methods: List[MethodInfo]) -> Dict[str, List[str]]:
        """
        Generate synonyms for methods based on their docstrings using LLM.
        Results are cached to file and reused if method signature unchanged.

        Args:
            methods: List of MethodInfo with names and docstrings

        Returns:
            Dict mapping method names to their synonyms
        """
        if not self.llm_available:
            print("[SynonymGenerator] LLM not available, skipping dynamic synonym generation")
            return {}

        # 1. Load existing cache
        cache = self._load_dynamic_cache()

        # 2. Find methods that need synonym generation
        methods_to_generate: List[Tuple[MethodInfo, str]] = []
        for method in methods:
            sig_hash = self._compute_method_hash(method)
            if sig_hash not in cache.get("methods", {}):
                methods_to_generate.append((method, sig_hash))

        # 3. If all methods cached, return early
        if not methods_to_generate:
            print(f"[SynonymGenerator] All {len(methods)} methods found in dynamic cache")
            return self._flatten_dynamic_cache(cache)

        print(f"[SynonymGenerator] Generating dynamic synonyms for {len(methods_to_generate)} methods...")

        # 4. Batch LLM call for uncached methods
        new_synonyms = self._generate_synonyms_from_docstrings(methods_to_generate)

        # 5. Update cache and persist
        for i, (method, sig_hash) in enumerate(methods_to_generate):
            syns = new_synonyms[i] if i < len(new_synonyms) else []
            cache["methods"][sig_hash] = {
                "method_name": method.name,
                "docstring": method.docstring,
                "synonyms": syns,
                "generated_at": datetime.now().isoformat()
            }

        self._save_dynamic_cache(cache)
        print(f"[SynonymGenerator] Dynamic synonyms cached to {DYNAMIC_CACHE_PATH.name}")

        return self._flatten_dynamic_cache(cache)

    def _generate_synonyms_from_docstrings(self, methods: List[Tuple[MethodInfo, str]]) -> List[List[str]]:
        """
        Call LLM to generate synonyms based on method name + docstring.

        Args:
            methods: List of (MethodInfo, hash) tuples

        Returns:
            List of synonym lists, one per method
        """
        if not methods or not self.llm_available:
            return [[] for _ in methods]

        # Build prompt with method info
        prompt = """Generate natural language synonyms for these Python methods.
For each method, provide 5-8 different ways a user might verbally request this action.
Include casual phrases, formal commands, and alternative verbs.

Methods:
"""
        for method, _ in methods:
            prompt += f"\n- {method.name}"
            if method.docstring:
                prompt += f": {method.docstring}"

        prompt += """

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{"method_name1": ["synonym1", "synonym2", ...], "method_name2": ["synonym1", ...]}
"""

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )

            response = message.content[0].text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if '```' in response:
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)

            synonyms_dict = json.loads(response)

            # Map back to method order
            result = []
            for method, _ in methods:
                method_syns = synonyms_dict.get(method.name, [])
                # Lowercase all synonyms
                result.append([s.lower() for s in method_syns])

            print(f"[SynonymGenerator] Generated synonyms for {len(synonyms_dict)} methods")
            return result

        except Exception as e:
            print(f"[SynonymGenerator] LLM call failed for dynamic synonyms: {e}")
            return [[] for _ in methods]

    def merge_dynamic_synonyms(self, dynamic_syns: Dict[str, List[str]]) -> None:
        """
        Merge dynamic synonyms into the lookup dictionary.

        Args:
            dynamic_syns: Dict mapping method names to synonyms
        """
        self.dynamic_method_synonyms = dynamic_syns
        print(f"[SynonymGenerator] Merged {len(dynamic_syns)} dynamic method synonyms")
