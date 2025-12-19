#!/usr/bin/env python3

import sys
import os

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

os.environ['ANTHROPIC_API_KEY'] = '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'

def test_synonym_generation():
    from app.nlp_v2.synonym_service import SynonymService
    
    # Simple test methods
    methods = [
        {"name": "turn_tv_on", "description": "Turn the television on"},
        {"name": "turn_tv_off", "description": "Turn the television off"},
        {"name": "turn_ac_on", "description": "Turn the air conditioner on"},
        {"name": "turn_ac_off", "description": "Turn the air conditioner off"}
    ]
    
    service = SynonymService()
    
    try:
        print("Testing synonym generation...")
        result = service.generate_synonyms(methods)
        print(f"SUCCESS:")
        print(f"Synonyms: {result.get('synonyms', {})}")
        print(f"Antonyms: {result.get('antonyms', {})}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_synonym_generation()
