#!/usr/bin/env python3

import sys
import os

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

os.environ['HUGGINGFACE_TOKEN'] = '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'

def test_semantic_matcher():
    from app.nlp_v2.semantic_matcher import HFSemanticMatcher
    
    # Create simple test methods
    methods = [
        {
            "name": "turn_tv_on",
            "description": "Turn the television on"
        },
        {
            "name": "turn_tv_off", 
            "description": "Turn the television off"
        },
        {
            "name": "turn_ac_on",
            "description": "Turn the air conditioner on"
        },
        {
            "name": "turn_ac_off",
            "description": "Turn the air conditioner off"
        }
    ]
    
    matcher = HFSemanticMatcher(hf_token=os.environ['HUGGINGFACE_TOKEN'])
    
    # Test problematic commands
    commands = ['turn tv on', 'open tv', 'open the ac']
    
    for command in commands:
        print(f"\n{'='*50}")
        print(f"Testing: '{command}'")
        print(f"{'='*50}")
        
        # Generate synonyms for testing
        from app.nlp_v2.synonym_service import SynonymService
        service = SynonymService()
        synonym_data = service.generate_synonyms(methods)
        synonyms = synonym_data.get('synonyms', {})
        antonyms = synonym_data.get('antonyms', {})
        
        print(f"Using synonyms: {synonyms}")
        print(f"Using antonyms: {antonyms}")
        
        try:
            matches = matcher.find_best_match(
                command=command,
                methods=methods,
                top_k=3,
                min_confidence=0.0,
                synonyms=synonyms,
                antonyms=antonyms
            )
            
            print(f"Found {len(matches)} matches:")
            for method, confidence in matches:
                print(f"  {method['name']}: {confidence:.3f}")
                
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_semantic_matcher()
