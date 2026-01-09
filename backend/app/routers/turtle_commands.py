from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor

from app.nlp_v3.turtle_introspector import (
    get_turtle_methods,
    get_introspector,
    refresh_turtle_methods
)
from app.nlp_v3.main import NLPPipeline

router = APIRouter(tags=["Turtle Commands"])

_executor = ThreadPoolExecutor(max_workers=2)
_turtle_pipeline: Optional[NLPPipeline] = None
_pipeline_initialized: bool = False
_direct_commands: Optional[Dict[str, List[str]]] = None
_no_arg_commands: Optional[set] = None


def _build_direct_command_maps():
    """Build command maps from introspector (called once, cached)."""
    global _direct_commands, _no_arg_commands
    if _direct_commands is not None:
        return

    introspector = get_introspector()
    introspector.introspect()

    _direct_commands = {}
    _no_arg_commands = set()

    for method in introspector._methods:
        detail = introspector._detailed_methods.get(method.name)
        if not detail:
            continue

        names = [method.name] + (detail.aliases if detail.aliases else [])

        if not method.params:
            _no_arg_commands.update(names)
        else:
            for name in names:
                _direct_commands[name] = method.params


class TurtleCommandRequest(BaseModel):
    command: str
    language: Optional[str] = "en"


class TurtleCommandResponse(BaseModel):
    success: bool
    executable: Optional[str] = None
    method: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    error: Optional[str] = None
    breakdown: Optional[Dict[str, float]] = None
    executables: Optional[List[str]] = None
    is_compound: bool = False


class TurtleMethodInfo(BaseModel):
    name: str
    params: List[str]
    docstring: Optional[str]
    category: Optional[str] = None


class TurtleMethodsResponse(BaseModel):
    success: bool
    methods: List[TurtleMethodInfo]
    total: int
    categories: Optional[Dict[str, List[str]]] = None


def _get_turtle_pipeline() -> NLPPipeline:
    global _turtle_pipeline, _pipeline_initialized

    if _turtle_pipeline is None:
        print("[TurtleCommands] Initializing NLP pipeline...")
        _turtle_pipeline = NLPPipeline()

    if not _pipeline_initialized:
        methods = get_introspector().get_canonical_methods_only()
        _turtle_pipeline.initialize(methods)
        _pipeline_initialized = True
        print(f"[TurtleCommands] Pipeline ready with {len(methods)} methods")

    return _turtle_pipeline


def _try_direct_match(command: str) -> Optional[Dict]:
    _build_direct_command_maps()
    command = command.strip().lower()
    match = re.match(r'^(\w+)\s*(-?\d+(?:\.\d+)?)?$', command)
    if not match:
        return None

    method_name = match.group(1)
    number_str = match.group(2)

    if method_name in _direct_commands:
        params = _direct_commands[method_name]
        if number_str and params:
            param_name = params[0]
            value = float(number_str) if '.' in number_str else int(number_str)
            return {
                "success": True,
                "executable": f"{method_name}({param_name}={value})",
                "method": method_name,
                "parameters": {param_name: value},
                "confidence": 100.0,
            }

    if method_name in _no_arg_commands and not number_str:
        return {
            "success": True,
            "executable": f"{method_name}()",
            "method": method_name,
            "parameters": {},
            "confidence": 100.0,
        }

    return None


def _split_compound_command(command: str) -> List[str]:
    """Split compound commands like 'forward 50 and then left 90' into parts."""
    processed = command.lower().strip()

    split_patterns = [
        r'\s+and\s+then\s+',
        r'\s+after\s+that\s+',
        r'\s+then\s+',
        r'\s+and\s+',
        r'\s+next\s+',
        r',\s*then\s+',
        r',\s*and\s+',
        r',\s+',
    ]

    parts = [processed]
    for pattern in split_patterns:
        new_parts = []
        for part in parts:
            split_result = re.split(pattern, part, flags=re.IGNORECASE)
            new_parts.extend([p.strip() for p in split_result if p.strip()])
        parts = new_parts

    parts = [p for p in parts if len(p) > 2]
    return parts if parts else [command]


def _preprocess_turtle_command(command: str) -> str:
    """Normalize natural language to turtle-friendly format."""
    processed = command.lower()

    # Remove filler words
    filler_patterns = [
        r'\bthe\s+turtle\b', r'\bturtle\b', r'\bthe\s+pen\b',
        r'\bit\s+to\b', r'\bit\b', r'\bagain\b', r'["\']',
    ]
    for pattern in filler_patterns:
        processed = re.sub(pattern, '', processed, flags=re.IGNORECASE)

    processed = re.sub(r'[.,!?;:]+', ' ', processed)

    # Rewrite "move/go + direction" to "direction + number"
    processed = re.sub(
        r'\b(move|go)\s+(\d+)\s*(?:steps?\s*)?(forward|backward|back)\b',
        r'\3 \2', processed
    )
    processed = re.sub(
        r'\b(move|go)\s+(forward|backward|back)\s*(\d+)?\s*(?:steps?)?\b',
        r'\2 \3', processed
    )

    # Rewrite "turn + direction" to "direction + number"
    processed = re.sub(
        r'\b(turn)\s+(\d+)\s*(?:degrees?\s*)?(left|right)\b',
        r'\3 \2', processed
    )
    processed = re.sub(
        r'\b(turn)\s+(left|right)\s*(\d+)?\s*(?:degrees?)?\b',
        r'\2 \3', processed
    )

    return ' '.join(processed.split())


def _process_single_command(command: str, methods, pipeline) -> Dict:
    """Process a single turtle command through NLP pipeline."""
    processed_command = _preprocess_turtle_command(command)

    direct_result = _try_direct_match(processed_command)
    if direct_result:
        return direct_result

    results = pipeline.process_command(processed_command, methods, top_k=1)
    if not results:
        return {"success": False, "error": f"No matching command for: '{command}'"}

    action_verb, match_score = results[0]

    if match_score.total_score < 0.15:
        return {
            "success": False,
            "confidence": match_score.total_score * 100,
            "error": f"Low confidence match. Did you mean '{match_score.method_name}'?"
        }

    return {
        "success": True,
        "executable": match_score.get_method_call(),
        "method": match_score.method_name,
        "parameters": match_score.extracted_params,
        "confidence": match_score.total_score * 100,
        "breakdown": {
            "semantic_score": match_score.semantic_score * 100,
            "intent_score": match_score.intent_score * 100,
            "synonym_boost": match_score.synonym_boost * 100,
            "param_relevance": match_score.param_relevance * 100,
            "phrasal_verb_match": match_score.phrasal_verb_match * 100
        }
    }


def _process_command_sync(command: str, methods) -> Dict:
    """Process command synchronously (runs in thread pool)."""
    pipeline = _get_turtle_pipeline()
    command_parts = _split_compound_command(command)

    if len(command_parts) == 1:
        return _process_single_command(command_parts[0], methods, pipeline)

    executables = []
    errors = []
    total_confidence = 0.0

    for part in command_parts:
        result = _process_single_command(part, methods, pipeline)
        if result["success"]:
            executables.append(result["executable"])
            total_confidence += result["confidence"]
        else:
            errors.append(result.get("error", f"Failed: {part}"))

    if not executables:
        return {"success": False, "error": "; ".join(errors), "is_compound": True}

    return {
        "success": True,
        "executable": "; ".join(executables),
        "executables": executables,
        "confidence": total_confidence / len(executables) if executables else 0,
        "is_compound": True,
        "error": "; ".join(errors) if errors else None
    }


@router.post("/analyze_turtle_command", response_model=TurtleCommandResponse)
async def analyze_turtle_command(payload: TurtleCommandRequest):
    """Analyze natural language and return executable turtle code."""
    try:
        methods = get_introspector().get_canonical_methods_only()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor, _process_command_sync, payload.command, methods
        )
        return TurtleCommandResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/turtle_methods", response_model=TurtleMethodsResponse)
async def list_turtle_methods(canonical_only: bool = True):
    """List available turtle methods with parameters and descriptions."""
    try:
        introspector = get_introspector()
        methods = introspector.get_canonical_methods_only() if canonical_only else introspector.introspect()
        introspector.introspect()

        categorized_methods = {}
        for m in methods:
            detail = introspector.get_detailed_method(m.name)
            cat = detail.category if detail else introspector._get_method_category(m.name)
            if cat not in categorized_methods:
                categorized_methods[cat] = []
            categorized_methods[cat].append(m.name)

        return TurtleMethodsResponse(
            success=True,
            methods=[
                TurtleMethodInfo(
                    name=m.name, params=m.params, docstring=m.docstring,
                    category=introspector._get_method_category(m.name)
                )
                for m in methods
            ],
            total=len(methods),
            categories=categorized_methods
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/prewarm_turtle_pipeline")
async def prewarm_turtle_pipeline(background_tasks: BackgroundTasks):
    """Pre-warm the NLP pipeline for faster first request."""
    global _pipeline_initialized
    try:
        if _pipeline_initialized:
            return {"status": "already_initialized", "method_count": len(get_turtle_methods())}

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, _get_turtle_pipeline)
        return {"status": "initialized", "method_count": len(get_turtle_methods())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/refresh_turtle_methods")
async def refresh_methods():
    """Force refresh the turtle method list."""
    global _pipeline_initialized
    try:
        _pipeline_initialized = False
        loop = asyncio.get_event_loop()
        methods = await loop.run_in_executor(_executor, refresh_turtle_methods)
        await loop.run_in_executor(_executor, _get_turtle_pipeline)
        return {"status": "refreshed", "method_count": len(methods)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/turtle_cache")
async def clear_turtle_cache():
    """Clear the turtle docstring cache."""
    global _pipeline_initialized
    try:
        get_introspector().clear_cache()
        _pipeline_initialized = False
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
