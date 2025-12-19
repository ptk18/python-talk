#!/usr/bin/env python3
"""
Production-like test to match exact behavior seen in chat interface
"""

import sys
import os
sys.path.append('/Users/ptk/ptk/kmitl-senior-yr/py-talk')
sys.path.append('/Users/ptk/ptk/kmitl-senior-yr/py-talk/backend')

def test_production_scenario():
    """Test exactly like the production API call"""
    
    try:
        from app.nlp_v2.extract_catalog_from_source_code.ast_extractor import extract_from_file
        from app.nlp_v2.paraphrase_matcher import process_command_with_paraphrases_sync
        
        # Test with the smart home source
        source_file = "/Users/ptk/ptk/kmitl-senior-yr/py-talk/source_kbs/smarthome.py"
        
        print("=== Production Scenario Test ===")
        
        # Extract catalog exactly like production
        catalog = extract_from_file(source_file)
        class_name = list(catalog.classes.keys())[0]
        print(f"Found class: {class_name}")
        
        # Test the exact commands from the chat screenshots  
        production_commands = [
            "get the tv turned on",
            "open the ac", 
            "open the air conditioner"
        ]
        
        for command in production_commands:
            print(f"\n=== Testing: '{command}' ===")
            try:
                # Use EXACT production settings
                result = process_command_with_paraphrases_sync(
                    text=command,
                    catalog=catalog,
                    class_name=class_name,
                    verbose=False,  # Same as production
                    use_semantic=True,
                    hf_token=None,
                    confidence_threshold=50.0,  # Updated threshold
                    use_llm_fallback=False,  # Disabled LLM fallback
                    source_file=source_file,
                    paraphrase_threshold=60.0,  # Updated threshold
                    max_paraphrases=5
                )
                
                if result and isinstance(result, dict):
                    if result.get('executable'):
                        executable = result.get('executable', 'unknown')
                        confidence = result.get('confidence', 0)
                        method = result.get('method', {})
                        method_name = method.get('name', 'unknown') if isinstance(method, dict) else str(method)
                        print(f"✅ SUCCESS: {executable}")
                        print(f"   Method: {method_name}")
                        print(f"   Confidence: {confidence:.1f}%")
                        
                        # Check if it matches expected behavior
                        if command == "get the tv turned on" and "turn_tv_on" in executable:
                            print("   ✅ CORRECT - TV command mapped correctly")
                        elif "open" in command and "ac" in command and "turn_ac_on" in executable:
                            print("   ✅ CORRECT - AC command mapped correctly") 
                        elif "status" in executable:
                            print("   ❌ WRONG - Mapped to status() instead of proper action")
                        else:
                            print(f"   ❓ REVIEW - Unexpected mapping")
                            
                    elif result.get('error'):
                        error = result.get('error', 'unknown error')
                        print(f"❌ ERROR: {error}")
                    else:
                        print(f"❓ UNKNOWN: {result}")
                else:
                    print(f"❌ NO RESULT")
                    
            except Exception as e:
                print(f"💥 EXCEPTION: {e}")
        
        print("\n=== Production Test Complete ===")
        
    except Exception as e:
        print(f"Failed to run production test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_production_scenario()
