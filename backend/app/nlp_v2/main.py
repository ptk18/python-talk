import os
from typing import Dict, Any, Optional
from app.nlp_v2.semantic_parsing.intent_parser import parse_intent
from app.nlp_v2.semantic_parsing.parameter_extractor import extract_parameters
from app.nlp_v2.method_matching.matcher import find_matching_methods, MatchResult
from app.nlp_v2.method_matching.resolver import resolve_parameters, validate_parameters, generate_function_call
from app.nlp_v2.extract_catalog_from_source_code.catalog import Catalog
from app.nlp_v2.extract_catalog_from_source_code.ast_extractor import extract_from_file

from app.nlp_v2.semantic_parsing.complex_sentence_parser import ComplexSentenceParser, print_command_tree
from app.nlp_v2.semantic_parsing.command_executor import CommandExecutor, ExecutionContext, format_executable_code


try:
    from semantic_matcher import HFSemanticMatcher
    SEMANTIC_MATCHER_AVAILABLE = True
except (ImportError, Exception) as e:
    SEMANTIC_MATCHER_AVAILABLE = False

try:
    from app.nlp_v2.auto_nl_interface_llm import NaturalLanguageInterface
    LLM_INTERFACE_AVAILABLE = True
except (ImportError, Exception) as e:
    LLM_INTERFACE_AVAILABLE = False
    print(f"LLM interface not available: {e}")


def find_matching_methods_semantic(
    text: str,
    catalog: Catalog,
    class_name: str,
    hf_token: Optional[str] = None
) -> list[MatchResult]:
    methods = catalog.get_methods(class_name)

    if not methods:
        return []

    method_dicts = [
        {
            "name": method.name,
            "description": method.docstring or method.name.replace('_', ' '),
            "parameters": method.parameters,
            "method_info": method
        }
        for method in methods
    ]

    matcher = HFSemanticMatcher(hf_token=hf_token)
    semantic_matches = matcher.find_best_match(
        command=text,
        methods=method_dicts,
        top_k=5,
        min_confidence=0.2
    )

    results = []
    for method_dict, confidence in semantic_matches:
        results.append(MatchResult(
            method_info=method_dict["method_info"],
            score=confidence * 100,  
            matched_component="semantic_similarity"
        ))

    return results


def process_command(
    text: str,
    catalog: Catalog,
    class_name: str,
    verbose: bool = False,
    use_semantic: bool = True,
    hf_token: Optional[str] = None,
    confidence_threshold: float = 30.0,
    use_llm_fallback: bool = False,
    source_file: Optional[str] = None
) -> Dict[str, Any]:
    trace = []

    if verbose:
        trace.append("STEP 1: INTENT PARSING")
    intent = parse_intent(text)
    if verbose:
        trace.append(f"Input: '{text}'")
        trace.append(f"Verb: '{intent.verb}', Subject: '{intent.subject}', Type: '{intent.intent_type}'")

    if verbose:
        trace.append("\nSTEP 2: PARAMETER EXTRACTION")
    parameters = extract_parameters(intent)
    if verbose:
        trace.append(f"Numbers: {parameters.get('numbers', [])}, Strings: {parameters.get('strings', [])}, Boolean: {parameters.get('boolean')}")

    if verbose:
        trace.append("\nSTEP 3: METHOD MATCHING")

    if use_semantic and SEMANTIC_MATCHER_AVAILABLE:
        if verbose:
            trace.append("Using semantic matching")
        try:
            matches = find_matching_methods_semantic(text, catalog, class_name, hf_token)
        except Exception as e:
            if verbose:
                trace.append(f"Semantic matching failed: {e}")
            matches = find_matching_methods(intent, catalog, class_name)
    else:
        if verbose:
            trace.append("Using pattern matching")
        matches = find_matching_methods(intent, catalog, class_name)

    if not matches:
        # Try LLM fallback if enabled
        if use_llm_fallback and LLM_INTERFACE_AVAILABLE and source_file:
            if verbose:
                trace.append("No matches found, trying LLM fallback...")
            try:
                llm_interface = NaturalLanguageInterface(
                    python_file=source_file,
                    class_name=class_name
                )
                llm_result = llm_interface.process(text)

                if llm_result.commands:
                    if verbose:
                        trace.append(f"LLM generated {len(llm_result.commands)} command(s)")
                        for line in trace:
                            print(line)

                    # Format executable from first command
                    first_cmd = llm_result.commands[0]
                    params_str = ', '.join(f'{k}={v}' for k, v in first_cmd.params.items())
                    executable = f"{first_cmd.name}({params_str})" if first_cmd.params else f"{first_cmd.name}()"

                    return {
                        "method": "llm_fallback",
                        "parameters": first_cmd.params,
                        "confidence": 100.0,
                        "executable": executable,
                        "intent_type": "llm_generated",
                        "source": "llm",
                        "trace": "\n".join(trace)
                    }
            except Exception as e:
                if verbose:
                    trace.append(f"LLM fallback failed: {e}")

        if verbose:
            for line in trace:
                print(line)
        return {"error": "No matching method found", "trace": "\n".join(trace)}

    if verbose:
        trace.append(f"Found {len(matches)} candidates:")
        for i, match in enumerate(matches[:3], 1):
            trace.append(f"  {i}. {match.method_info.name} (score={match.score:.1f})")

    best_match = matches[0]
    if verbose:
        trace.append(f"\nSelected: {best_match.method_info.name}")
        trace.append(f"Confidence: {best_match.score:.1f}")

    # Check if confidence is below 100 and LLM fallback is enabled
    if best_match.score < 100 and use_llm_fallback:
        if verbose:
            trace.append(f"\nConfidence {best_match.score:.1f} < threshold {confidence_threshold}")
            trace.append("Falling back to LLM interface...")

        if LLM_INTERFACE_AVAILABLE and source_file:
            try:
                llm_interface = NaturalLanguageInterface(
                    python_file=source_file,
                    class_name=class_name
                )
                llm_result = llm_interface.process(text)

                if llm_result.commands:
                    if verbose:
                        trace.append(f"LLM generated {len(llm_result.commands)} command(s)")
                        for line in trace:
                            print(line)

                    # Format executable from first command
                    first_cmd = llm_result.commands[0]
                    params_str = ', '.join(f'{k}={v}' for k, v in first_cmd.params.items())
                    executable = f"{first_cmd.name}({params_str})" if first_cmd.params else f"{first_cmd.name}()"

                    return {
                        "method": "llm_fallback",
                        "parameters": first_cmd.params,
                        "confidence": 100.0,
                        "executable": executable,
                        "intent_type": "llm_generated",
                        "source": "llm",
                        "trace": "\n".join(trace),
                        "nlp_score": best_match.score
                    }
                else:
                    if verbose:
                        trace.append("LLM returned no commands, continuing with NLP result")
            except Exception as e:
                if verbose:
                    trace.append(f"LLM fallback failed: {e}")
        elif verbose:
            if not LLM_INTERFACE_AVAILABLE:
                trace.append("LLM interface not available")
            if not source_file:
                trace.append("Source file path not provided")

    if verbose:
        trace.append("\nSTEP 4: PARAMETER RESOLUTION")

    resolved_params = resolve_parameters(intent, best_match.method_info, parameters)
    if verbose:
        trace.append(f"Resolved: {resolved_params}")
        trace.append("\nSTEP 5: PARAMETER VALIDATION")

    is_valid, error_msg = validate_parameters(resolved_params, best_match.method_info)

    if not is_valid:
        if verbose:
            trace.append(f"Validation failed: {error_msg}")
            for line in trace:
                print(line)
        return {"error": error_msg, "trace": "\n".join(trace)}

    if verbose:
        trace.append("Validation passed")
        trace.append("\nSTEP 6: GENERATE EXECUTABLE")

    executable = generate_function_call(best_match.method_info, resolved_params)
    if verbose:
        trace.append(f"Executable: {executable}")
        for line in trace:
            print(line)

    return {
        "method": best_match.method_info.name,
        "parameters": resolved_params,
        "confidence": best_match.score,
        "executable": executable,
        "intent_type": intent.intent_type,
        "source": "nlp",
        "trace": "\n".join(trace),
        "all_matches": [{"method": m.method_info.name, "score": m.score} for m in matches[:3]]
    }


def process_complex_command(
    text: str,
    catalog: Catalog,
    class_name: str,
    verbose: bool = False,
    use_semantic: bool = True,
    hf_token: Optional[str] = None,
    confidence_threshold: float = 30.0,
    use_llm_fallback: bool = False,
    source_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process commands that may contain loops, conditionals, or conjunctions
    Returns structured result with generated code
    """

    parser = ComplexSentenceParser()
    command_tree = parser.parse(text)

    if verbose:
        print_command_tree(command_tree)
        print()

    if command_tree.type == 'action':
        return process_command(
            text, catalog, class_name, verbose, use_semantic, hf_token,
            confidence_threshold, use_llm_fallback, source_file
        )

    def simple_processor(text: str, cat: Any, cls: str) -> Dict[str, Any]:
        return process_command(
            text, cat, cls, False, use_semantic, hf_token,
            confidence_threshold, use_llm_fallback, source_file
        )

    executor = CommandExecutor(simple_processor)
    context = ExecutionContext()
    executables = executor.execute(command_tree, context, catalog, class_name)
    code = format_executable_code(executables)

    # Check if executables are empty or contain any errors
    has_errors = any(
        '# Error:' in executable or '# Warning:' in executable
        for executable in executables
    )

    has_valid_executable = any(
        executable.strip() and
        not executable.strip().startswith('#')
        for executable in executables
    )

    # Trigger LLM fallback if there are errors or no valid executables
    if has_errors or not has_valid_executable:
        if verbose:
            print("Complex parser returned empty/error result, trying LLM fallback...")

        # Try LLM fallback
        if use_llm_fallback and LLM_INTERFACE_AVAILABLE and source_file:
            try:
                llm_interface = NaturalLanguageInterface(
                    python_file=source_file,
                    class_name=class_name
                )
                llm_result = llm_interface.process(text)

                if llm_result.commands:
                    if verbose:
                        print(f"LLM generated {len(llm_result.commands)} command(s)")

                    # Format executable from first command
                    first_cmd = llm_result.commands[0]
                    params_str = ', '.join(f'{k}={v}' for k, v in first_cmd.params.items())
                    executable = f"{first_cmd.name}({params_str})" if first_cmd.params else f"{first_cmd.name}()"

                    return {
                        "method": "llm_fallback",
                        "parameters": first_cmd.params,
                        "confidence": 100.0,
                        "executable": executable,
                        "intent_type": "llm_generated",
                        "source": "llm"
                    }
            except Exception as e:
                if verbose:
                    print(f"LLM fallback failed: {e}")

    if verbose:
        for log_entry in context.execution_log:
            print(log_entry)
        print()

    return {
        "type": "complex",
        "command_tree_type": command_tree.type,
        "executables": executables,
        "code": code,
        "execution_log": context.execution_log
    }


if __name__ == "__main__":
    import sys

    SOURCE_FILE = "./source_kbs/myturtle.py"
    CLASS_NAME = "SimpleTurtle"

    TEST_CASES = [
        "move forward by 10 and turn right by 90 degrees",
        "move backward by 5 then turn left by 45 degrees",
        "turn 29 degrees and move 15 steps back",
        "turn off tv"
    ]

    if not os.path.exists(SOURCE_FILE):
        print(f"Error: Source file not found: {SOURCE_FILE}")
        sys.exit(1)

    catalog = extract_from_file(SOURCE_FILE)

    print(f"Testing: {SOURCE_FILE}")
    print(f"Class: {CLASS_NAME}\n")

    for i, command in enumerate(TEST_CASES, 1):
        print(f"\nTest {i}: {command}")

        result = process_complex_command(command, catalog, CLASS_NAME, verbose=False)

        if "error" in result:
            print(f"  ERROR: {result['error']}\n")
        elif result.get("type") == "complex":
            print(f"  Complex command ({result.get('command_tree_type')})")
            for line in result['code'].split('\n'):
                print(f"    {line}")
        else:
            print(f"  Simple command")
            print(f"  Method: {result['method']}")
            print(f"  Parameters: {result['parameters']}")
            print(f"  Executable: {result['executable']}")
            print(f"  Confidence: {result['confidence']:.1f}")
        print()
