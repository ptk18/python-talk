#!/usr/bin/env python3
"""
Quick integration test to verify the pre-warming solution works correctly.
"""

import sys
import os
sys.path.append('/Users/ptk/ptk/kmitl-senior-yr/py-talk')
sys.path.append('/Users/ptk/ptk/kmitl-senior-yr/py-talk/backend')

def test_prewarming_integration():
    """Test that the pre-warming integration works end-to-end"""
    from app.nlp_v2.extract_catalog_from_source_code.ast_extractor import extract_from_file
    from app.nlp_v2.prewarming import prewarm_nlp_components_sync
    from app.nlp_v2.paraphrase_matcher import process_command_with_paraphrases_sync
    
    # Test with the smart home source
    source_file = "/Users/ptk/ptk/kmitl-senior-yr/py-talk/source_kbs/smarthome.py"
    
    print("=== Testing Pre-warming Integration ===")
    
    # Extract catalog
    catalog = extract_from_file(source_file)
    class_name = list(catalog.classes.keys())[0]
    print(f"Found class: {class_name}")
    
    # Test pre-warming
    print("\n1. Testing pre-warming...")
    results = prewarm_nlp_components_sync(catalog, class_name)
    print(f"Pre-warming results: {results}")
    
    # Test problematic commands
    test_commands = [
        "turn tv on",
        "open tv", 
        "open the ac",
        "turn on the air conditioning"
    ]
    
    print(f"\n2. Testing commands after pre-warming...")
    for command in test_commands:
        print(f"\nTesting: '{command}'")
        result = process_command_with_paraphrases_sync(
            text=command,
            catalog=catalog,
            class_name=class_name,
            verbose=False,
            use_semantic=True,
            hf_token=None,
            confidence_threshold=50.0,  # Lower threshold
            use_llm_fallback=True,
            source_file=source_file,
            paraphrase_threshold=60.0,  # Lower threshold
            max_paraphrases=5
        )
        
        if result and isinstance(result, dict):
            if result.get('executable'):
                executable = result.get('executable', 'unknown')
                confidence = result.get('confidence', 0)
                source = result.get('source', 'unknown')
                print(f"  → SUCCESS: {executable} (confidence: {confidence:.1f}%) [via {source}]")
            elif result.get('error'):
                error = result.get('error', 'unknown error')
                print(f"  → FAILED: {error}")
            else:
                print(f"  → UNKNOWN: {result}")
        else:
            print(f"  → FAILED: No result returned")
    
    print("\n=== Integration Test Complete ===")

if __name__ == "__main__":
    test_prewarming_integration()
