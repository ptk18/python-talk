"""
Pre-warming utilities for NLP components to eliminate cold start delays.
"""
import asyncio
from typing import List, Dict, Optional
from app.nlp_v2.extract_catalog_from_source_code.catalog import Catalog


async def prewarm_synonyms_async(catalog: Catalog, class_name: str) -> bool:
    """
    Pre-warm synonym generation for all methods in the given class.
    
    Args:
        catalog: The extracted code catalog
        class_name: Name of the class to pre-warm synonyms for
        
    Returns:
        bool: True if pre-warming succeeded, False otherwise
    """
    try:
        from app.nlp_v2.synonym_service import get_synonym_service
        
        methods = catalog.get_methods(class_name)
        if not methods:
            return False

        synonym_service = get_synonym_service()
        method_dicts = [
            {"name": method.name, "description": method.docstring or method.name.replace('_', ' ')}
            for method in methods
        ]
        
        # Generate synonyms and cache them
        cache_key = f"{class_name}_v3"
        await synonym_service.generate_synonyms_async(method_dicts, cache_key=cache_key)
        
        print(f"Successfully pre-warmed synonyms for {len(method_dicts)} methods in class '{class_name}'")
        return True
        
    except Exception as e:
        print(f"Failed to pre-warm synonyms for class '{class_name}': {e}")
        return False


def prewarm_synonyms_sync(catalog: Catalog, class_name: str) -> bool:
    """
    Synchronous wrapper for pre-warming synonym generation.
    
    Args:
        catalog: The extracted code catalog
        class_name: Name of the class to pre-warm synonyms for
        
    Returns:
        bool: True if pre-warming succeeded, False otherwise
    """
    try:
        return asyncio.run(prewarm_synonyms_async(catalog, class_name))
    except Exception as e:
        print(f"Failed to run synonym pre-warming: {e}")
        return False


async def prewarm_nlp_components_async(catalog: Catalog, class_name: str) -> Dict[str, bool]:
    """
    Pre-warm all NLP components that might cause delays on first use.
    
    Args:
        catalog: The extracted code catalog
        class_name: Name of the class to pre-warm for
        
    Returns:
        Dict[str, bool]: Status of each component pre-warming
    """
    results = {}
    
    # Pre-warm synonyms
    results['synonyms'] = await prewarm_synonyms_async(catalog, class_name)
    
    # Add other component pre-warming here in the future
    # results['semantic_matcher'] = await prewarm_semantic_matcher_async(catalog, class_name)
    # results['llm_interface'] = await prewarm_llm_interface_async(catalog, class_name)
    
    return results


def prewarm_nlp_components_sync(catalog: Catalog, class_name: str) -> Dict[str, bool]:
    """
    Synchronous wrapper for pre-warming all NLP components.
    
    Args:
        catalog: The extracted code catalog
        class_name: Name of the class to pre-warm for
        
    Returns:
        Dict[str, bool]: Status of each component pre-warming
    """
    try:
        return asyncio.run(prewarm_nlp_components_async(catalog, class_name))
    except Exception as e:
        print(f"Failed to run NLP components pre-warming: {e}")
        return {'synonyms': False}
