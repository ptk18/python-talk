#!/usr/bin/env python3

import sys
import os

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

os.environ['ANTHROPIC_API_KEY'] = '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'

def test_open_ac():
    from app.nlp_v2.semantic_matcher import HFSemanticMatcher
    from app.nlp_v2.synonym_service import SynonymService
    
    methods = [
        {"name": "turn_ac_on", "description": "Turn the air conditioner on"},
        {"name": "turn_ac_off", "description": "Turn the air conditioner off"}
    ]
    
    service = SynonymService()
    synonym_data = service.generate_synonyms(methods)
    synonyms = synonym_data.get('synonyms', {})
    antonyms = synonym_data.get('antonyms', {})
    
    print(f"AC synonyms: {synonyms}")
    
    matcher = HFSemanticMatcher()
    
    command = "open the ac"
    matches = matcher.find_best_match(
        command=command,
        methods=methods,
        synonyms=synonyms,
        antonyms=antonyms,
        min_confidence=0.0
    )
    
    print(f"\nResults for '{command}':")
    for method, score in matches:
        print(f"  {method['name']}: {score:.3f}")

if __name__ == "__main__":
    test_open_ac()
