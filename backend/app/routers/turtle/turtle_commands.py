from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import asyncio
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from app.nlp_v4 import NLPService, TurtleExtractor, TurtlePreprocessor
from app.nlp_v4.turtle_introspector import (
    get_turtle_methods,
    get_introspector,
    refresh_turtle_methods,
    get_excluded_turtle_methods,
    get_exclusion_stats
)

router = APIRouter(tags=["Turtle Commands"])

# Configuration
CONFIDENCE_THRESHOLD = 0.15  # 15% minimum confidence

_executor = ThreadPoolExecutor(max_workers=2)
_turtle_service: Optional[NLPService] = None
_direct_commands: Optional[Dict[str, List[str]]] = None
_no_arg_commands: Optional[set] = None
_turtle_lock = threading.Lock()


def _build_direct_command_maps():
    """Build command maps from introspector (called once, cached, thread-safe)."""
    global _direct_commands, _no_arg_commands
    with _turtle_lock:
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


def _get_turtle_service() -> NLPService:
    """Get or initialize turtle NLP service (thread-safe)."""
    global _turtle_service

    with _turtle_lock:
        if _turtle_service is None:
            print("[TurtleCommands] Initializing NLP service...")

            # Create service with TurtleExtractor and TurtlePreprocessor
            _turtle_service = NLPService(
                extractor=TurtleExtractor(canonical_only=True),
                preprocessor=TurtlePreprocessor(),
                confidence_threshold=CONFIDENCE_THRESHOLD
            )

            # Initialize (source is ignored for TurtleExtractor)
            methods = _turtle_service.initialize(None)
            print(f"[TurtleCommands] Service ready with {len(methods)} methods")

        return _turtle_service


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


def _process_single_command(command: str, service: NLPService) -> Dict:
    """Process a single turtle command through NLP service."""
    # Preprocess command for direct match using the service's preprocessor
    preprocessed = service.preprocessor.preprocess(command)

    # Try direct match first (for simple commands like "forward 50")
    direct_result = _try_direct_match(preprocessed)
    if direct_result:
        return direct_result

    # Process through NLP service (preprocessor will be applied again, but that's fine)
    results = service.process(command, top_k=1)

    if not results:
        return {"success": False, "error": f"No matching command for: '{command}'"}

    # Get top result (already filtered by confidence threshold in service)
    r = results[0]

    return {
        "success": True,
        "executable": r.executable,
        "method": r.method_name,
        "parameters": r.parameters,
        "confidence": r.confidence,
        "breakdown": r.breakdown
    }


def _process_command_sync(command: str) -> Dict:
    """Process command synchronously (runs in thread pool)."""
    service = _get_turtle_service()
    command_parts = _split_compound_command(command)

    if len(command_parts) == 1:
        return _process_single_command(command_parts[0], service)

    executables = []
    errors = []
    total_confidence = 0.0

    for part in command_parts:
        result = _process_single_command(part, service)
        if result["success"]:
            executables.append(result["executable"])
            total_confidence += result.get("confidence", 0)
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
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            _executor, _process_command_sync, payload.command
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
    """Pre-warm the NLP service for faster first request."""
    global _turtle_service
    try:
        if _turtle_service is not None and _turtle_service.initialized:
            return {"status": "already_initialized", "method_count": len(_turtle_service.methods)}

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, _get_turtle_service)
        return {"status": "initialized", "method_count": len(get_turtle_methods())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/refresh_turtle_methods")
async def refresh_methods():
    """Force refresh the turtle method list."""
    global _turtle_service
    try:
        # Reset service to force reinitialization
        with _turtle_lock:
            _turtle_service = None

        loop = asyncio.get_event_loop()
        methods = await loop.run_in_executor(_executor, refresh_turtle_methods)
        await loop.run_in_executor(_executor, _get_turtle_service)
        return {"status": "refreshed", "method_count": len(methods)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/turtle_cache")
async def clear_turtle_cache():
    """Clear the turtle service and introspector cache."""
    global _turtle_service
    try:
        with _turtle_lock:
            _turtle_service = None
        get_introspector().clear_cache()
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/turtle_excluded")
async def get_excluded_methods():
    """
    Get all excluded turtle methods with their exclusion reasons.

    Returns a detailed breakdown of why each method was excluded from NLP processing.
    Useful for debugging and understanding the filtering logic.
    """
    try:
        excluded = get_excluded_turtle_methods()
        stats = get_exclusion_stats()
        return {
            "success": True,
            "excluded_methods": excluded,
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
