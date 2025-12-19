"""Claude-based synonym generation with caching"""

import os
import json
import re
from typing import List, Dict
from dotenv import load_dotenv
from .models import MethodInfo

# Load .env from nlp_v3 directory
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))


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

        # Single LLM call to generate ALL synonyms at once (optimized prompt)
        prompt = f"""Generate compact synonym maps for these method names:
{', '.join(m.name for m in methods[:20])}

Create JSON with 3 categories:
1. verbs: {', '.join(list(sorted(verbs))[:10])}
2. phrasal_verbs: {', '.join(list(sorted(phrasal_verbs))[:10])}
3. entities: {', '.join(list(sorted(entities))[:10])}

For each term, provide 5-8 common synonyms only.
Return ONLY JSON:
{{"verbs":{{"turn":["switch","flip"]}},"phrasal_verbs":{{"turn_on":["switch on","activate"]}},"entities":{{"light":["lamp","lights"]}}}}"""

        print(f"  Calling LLM once to generate synonym dictionary for:")
        print(f"    - {len(verbs)} verbs")
        print(f"    - {len(phrasal_verbs)} phrasal verbs")
        print(f"    - {len(entities)} entities")

        try:
            message = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,  # Reduced for faster generation
                temperature=0.3,  # Lower temp for more focused, faster responses
                messages=[{"role": "user", "content": prompt}]
            )

            response = message.content[0].text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if '```' in response:
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)

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
