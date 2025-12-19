#!/usr/bin/env python3
"""
NLP Command Testing Tool
Debug individual commands against a smart home class to verify NLP processing.
"""

import sys
import os
import tempfile

# Add the parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

from app.nlp_v2.extract_catalog_from_source_code.ast_extractor import extract_from_file
from app.nlp_v2.main import process_command


def test_command(command, source_file):
    """Test a single command against the provided source file"""
    print(f"\n{'='*60}")
    print(f"TESTING COMMAND: '{command}'")
    print(f"{'='*60}")
    
    try:
        catalog = extract_from_file(source_file)
        if not catalog.classes:
            print("ERROR: No class found in source file")
            return
            
        class_name = list(catalog.classes.keys())[0]
        print(f"Using class: {class_name}")
        
        methods = catalog.get_methods(class_name)
        print(f"Available methods: {[m.name for m in methods]}")
        
        result = process_command(
            text=command,
            catalog=catalog,
            class_name=class_name,
            verbose=True,
            use_semantic=True,
            hf_token=os.environ.get('HUGGINGFACE_TOKEN'),
            confidence_threshold=30.0,
            use_llm_fallback=False,
            source_file=source_file
        )
        
        print(f"\nFINAL RESULT:")
        print(f"Method: {result.get('method', 'None')}")
        print(f"Confidence: {result.get('confidence', 0):.1f}%")
        print(f"Error: {result.get('error', 'None')}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


def create_test_smart_home():
    """Create a test SmartHome class for testing"""
    source_code = '''
class SmartHome:
    def turn_tv_on(self):
        """Turn the television on"""
        pass
        
    def turn_tv_off(self):
        """Turn the television off"""
        pass
        
    def turn_ac_on(self):
        """Turn the air conditioner on"""
        pass
        
    def turn_ac_off(self):
        """Turn the air conditioner off"""  
        pass
        
    def are_all_devices_off(self):
        """Check if all devices are off"""
        pass
'''
    return source_code


def main():
    """Run tests on common problematic commands"""
    # Create test file
    source_code = create_test_smart_home()
    temp_file = "/tmp/test_smart_home.py"
    
    with open(temp_file, "w") as f:
        f.write(source_code)
    
    try:
        # Test problematic commands that were previously failing
        test_commands = [
            "turn tv on",      # Should work - exact match
            "open tv",         # Should work - synonym
            "open the ac",     # Should work - synonym with article
            "close the tv",    # Should work - antonym -> turn_tv_off
            "switch on ac",    # Should work - synonym
        ]
        
        for cmd in test_commands:
            test_command(cmd, temp_file)
    
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)


if __name__ == "__main__":
    main()
