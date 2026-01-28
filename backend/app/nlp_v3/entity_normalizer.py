"""Entity normalization using LLM-generated synonym mappings"""

from typing import List
from .models import MethodInfo


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
        """Normalize entities in text, handling multi-word entities like 'air conditioner' -> 'ac'"""
        text_lower = text.lower().replace('-', '_')

        # Try full text match first (for multi-word entities like "air conditioner")
        text_normalized = text_lower.replace(' ', '_')
        if text_normalized in self.entity_map:
            return self.entity_map[text_normalized]

        # Try without underscores/spaces (e.g., "airconditioner")
        text_compact = text_lower.replace(' ', '').replace('_', '')
        if text_compact in self.entity_map:
            return self.entity_map[text_compact]

        # Fall back to word-by-word normalization
        words = text_lower.split()
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
