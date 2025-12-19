#!/usr/bin/env python3

import time
import sys
import os

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

os.environ['ANTHROPIC_API_KEY'] = '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'

def simulate_conversation():
    from app.nlp_v2.extract_catalog_from_source_code.ast_extractor import extract_from_file
    from app.nlp_v2.paraphrase_matcher import process_command_with_paraphrases_sync
    
    # Create test file
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
'''
    
    temp_file = "/tmp/test_smart_home.py"
    with open(temp_file, "w") as f:
        f.write(source_code)
    
    try:
        print("=== SIMULATING CONVERSATION START ===")
        
        # Step 1: Extract catalog (happens when conversation starts)
        print("1. Extracting catalog...")
        start_time = time.time()
        catalog = extract_from_file(temp_file)
        class_name = list(catalog.classes.keys())[0]
        extraction_time = time.time() - start_time
        print(f"   Catalog extraction: {extraction_time:.2f}s")
        
        # Step 2: Pre-warm synonyms (NEW - happens at conversation start)
        print("2. Pre-warming synonyms...")
        start_time = time.time()
        try:
            from app.nlp_v2.synonym_service import get_synonym_service
            import asyncio
            
            methods = catalog.get_methods(class_name)
            synonym_service = get_synonym_service()
            method_dicts = [
                {"name": method.name, "description": method.docstring or method.name.replace('_', ' ')}
                for method in methods
            ]
            
            asyncio.run(synonym_service.generate_synonyms_async(
                method_dicts, 
                cache_key=f"{class_name}_v3"
            ))
            prewarm_time = time.time() - start_time
            print(f"   Synonym pre-warming: {prewarm_time:.2f}s")
        except Exception as e:
            print(f"   Pre-warming failed: {e}")
            prewarm_time = 0
        
        print("\n=== SIMULATING USER COMMANDS ===")
        
        # Step 3: First command (should be fast - no synonyms needed)
        print("3. Command: 'turn tv on'")
        start_time = time.time()
        result1 = process_command_with_paraphrases_sync(
            text="turn tv on",
            catalog=catalog,
            class_name=class_name,
            verbose=False,
            use_semantic=True,
            confidence_threshold=60.0,
            source_file=temp_file,
        )
        cmd1_time = time.time() - start_time
        print(f"   Result: {result1.get('method')} ({result1.get('confidence', 0):.1f}%)")
        print(f"   Processing time: {cmd1_time:.2f}s")
        
        # Step 4: Second command (should now be fast - synonyms pre-warmed)
        print("\n4. Command: 'open the ac'")
        start_time = time.time()
        result2 = process_command_with_paraphrases_sync(
            text="open the ac",
            catalog=catalog,
            class_name=class_name,
            verbose=False,
            use_semantic=True,
            confidence_threshold=60.0,
            source_file=temp_file,
        )
        cmd2_time = time.time() - start_time
        print(f"   Result: {result2.get('method')} ({result2.get('confidence', 0):.1f}%)")
        print(f"   Processing time: {cmd2_time:.2f}s")
        
        print(f"\n=== PERFORMANCE SUMMARY ===")
        print(f"Catalog extraction: {extraction_time:.2f}s")
        print(f"Synonym pre-warming: {prewarm_time:.2f}s")
        print(f"First command: {cmd1_time:.2f}s")
        print(f"Second command: {cmd2_time:.2f}s")
        print(f"Total conversation setup: {extraction_time + prewarm_time:.2f}s")
        print(f"Average command time: {(cmd1_time + cmd2_time) / 2:.2f}s")
        
    finally:
        os.remove(temp_file)

if __name__ == "__main__":
    simulate_conversation()
