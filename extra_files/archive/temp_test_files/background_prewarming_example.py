## Alternative: Background Synonym Generation

# Add to conversation creation endpoint
from threading import Thread

def pregenerate_synonyms_background(class_name, methods):
    """Generate synonyms in background thread"""
    try:
        from app.nlp_v2.synonym_service import get_synonym_service
        import asyncio
        
        synonym_service = get_synonym_service()
        method_dicts = [
            {"name": method.name, "description": method.docstring or method.name.replace('_', ' ')}
            for method in methods
        ]
        
        asyncio.run(synonym_service.generate_synonyms_async(
            method_dicts, 
            cache_key=f"{class_name}_v3"
        ))
        print(f"Background synonym generation completed for {class_name}")
    except Exception as e:
        print(f"Background synonym generation failed: {e}")

# In file upload endpoint:
# Thread(target=pregenerate_synonyms_background, args=(class_name, methods)).start()
