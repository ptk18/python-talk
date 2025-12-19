from typing import Dict, Any, List, Optional
import asyncio
from app.routers.paraphrase import generate_paraphrases
from app.nlp_v2.main import process_command
from app.nlp_v2.extract_catalog_from_source_code.catalog import Catalog


async def process_command_with_paraphrases(
    text: str,
    catalog: Catalog,
    class_name: str,
    verbose: bool = False,
    use_semantic: bool = True,
    hf_token: Optional[str] = None,
    confidence_threshold: float = 60.0,
    use_llm_fallback: bool = True,
    source_file: Optional[str] = None,
    paraphrase_threshold: float = 70.0,
    max_paraphrases: int = 5
) -> Dict[str, Any]:

    if verbose:
        print(f"\n[Paraphrase Matcher] Trying original: '{text}'")

    original_result = process_command(
        text=text,
        catalog=catalog,
        class_name=class_name,
        verbose=verbose,
        use_semantic=use_semantic,
        hf_token=hf_token,
        confidence_threshold=confidence_threshold,
        use_llm_fallback=False,
        source_file=source_file
    )

    original_confidence = original_result.get('confidence', 0)

    if 'error' in original_result:
        original_confidence = 0

    if verbose:
        print(f"[Paraphrase Matcher] Original confidence: {original_confidence:.1f}%")

    if original_confidence >= paraphrase_threshold:
        if verbose:
            print(f"[Paraphrase Matcher] Confidence sufficient, using original")
        original_result['matching_strategy'] = 'original_command'

        # Additional validation: check if result seems semantically wrong
        # If method name suggests opposite action, still try paraphrases
        method_name = original_result.get('method', '').lower()
        command_lower = text.lower()

        # Check for obvious mismatches (e.g., "open" with "turn_off", "close" with "turn_on")
        suspicious = False
        if ('open' in command_lower or 'start' in command_lower or 'activate' in command_lower or 'enable' in command_lower):
            if '_off' in method_name or 'stop' in method_name or 'close' in method_name or 'disable' in method_name or 'deactivate' in method_name:
                suspicious = True
                if verbose:
                    print(f"[Paraphrase Matcher] Suspicious match detected: '{text}' -> {method_name}")

        if ('close' in command_lower or 'stop' in command_lower or 'deactivate' in command_lower or 'disable' in command_lower or 'off' in command_lower):
            if '_on' in method_name or 'start' in method_name or 'open' in method_name or 'enable' in method_name or 'activate' in method_name:
                suspicious = True
                if verbose:
                    print(f"[Paraphrase Matcher] Suspicious match detected: '{text}' -> {method_name}")

        if not suspicious:
            return original_result

        if verbose:
            print(f"[Paraphrase Matcher] Trying paraphrases despite high confidence due to suspicious match")

    if verbose:
        print(f"[Paraphrase Matcher] Confidence < {paraphrase_threshold}%, generating paraphrases...")

    try:
        paraphrases = await generate_paraphrases(text, max_variants=max_paraphrases)

        if verbose:
            print(f"[Paraphrase Matcher] Generated {len(paraphrases)} paraphrases:")
            for i, p in enumerate(paraphrases, 1):
                print(f"  {i}. {p}")

    except Exception as e:
        if verbose:
            print(f"[Paraphrase Matcher] Failed to generate paraphrases: {e}")
        original_result['matching_strategy'] = 'original_command_only'
        return original_result

    best_result = original_result
    best_confidence = original_confidence
    best_variant = "original"

    for i, paraphrase in enumerate(paraphrases, 1):
        if verbose:
            print(f"\n[Paraphrase Matcher] Trying paraphrase {i}/{len(paraphrases)}: '{paraphrase}'")

        try:
            result = process_command(
                text=paraphrase,
                catalog=catalog,
                class_name=class_name,
                verbose=False,
                use_semantic=use_semantic,
                hf_token=hf_token,
                confidence_threshold=confidence_threshold,
                use_llm_fallback=False,
                source_file=source_file
            )

            confidence = result.get('confidence', 0)

            if 'error' in result:
                confidence = 0

            if verbose:
                print(f"[Paraphrase Matcher]   Confidence: {confidence:.1f}%")

            if confidence > best_confidence and 'error' not in result:
                best_result = result
                best_confidence = confidence
                best_variant = paraphrase

                if verbose:
                    print(f"[Paraphrase Matcher]   New best match!")

                if confidence >= 90:
                    if verbose:
                        print(f"[Paraphrase Matcher]   Excellent match, stopping search")
                    break

        except Exception as e:
            if verbose:
                print(f"[Paraphrase Matcher]   Error: {e}")
            continue

    if best_variant != "original":
        best_result['matched_via_paraphrase'] = best_variant
        best_result['original_command'] = text
        best_result['matching_strategy'] = 'paraphrase_matching'
        if verbose:
            print(f"\n[Paraphrase Matcher] Best match via paraphrase: '{best_variant}'")
            print(f"[Paraphrase Matcher] Final confidence: {best_confidence:.1f}%")
    else:
        best_result['matching_strategy'] = 'original_command'
        if verbose:
            print(f"\n[Paraphrase Matcher] Original command was best")

    if best_confidence < confidence_threshold and use_llm_fallback:
        if verbose:
            print(f"[Paraphrase Matcher] Confidence still < {confidence_threshold}%, triggering LLM fallback...")
        return process_command(
            text=text,
            catalog=catalog,
            class_name=class_name,
            verbose=verbose,
            use_semantic=use_semantic,
            hf_token=hf_token,
            confidence_threshold=confidence_threshold,
            use_llm_fallback=True,
            source_file=source_file
        )

    return best_result


def process_command_with_paraphrases_sync(
    text: str,
    catalog: Catalog,
    class_name: str,
    **kwargs
) -> Dict[str, Any]:
    return asyncio.run(process_command_with_paraphrases(
        text=text,
        catalog=catalog,
        class_name=class_name,
        **kwargs
    ))
