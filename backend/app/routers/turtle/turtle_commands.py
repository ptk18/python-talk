from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import asyncio
import re
import threading
from concurrent.futures import ThreadPoolExecutor

from app.nlp_main_process import DictionaryNLPService

router = APIRouter(tags=["Turtle Commands"])

_executor = ThreadPoolExecutor(max_workers=2)
_turtle_service: Optional[DictionaryNLPService] = None
_turtle_lock = threading.Lock()


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
    executables: Optional[List[str]] = None
    is_compound: bool = False


class TurtleMethodInfo(BaseModel):
    name: str
    params: List[str]


class TurtleMethodsResponse(BaseModel):
    success: bool
    methods: List[TurtleMethodInfo]
    total: int


def _get_turtle_service() -> DictionaryNLPService:
    global _turtle_service
    with _turtle_lock:
        if _turtle_service is None:
            print("[TurtleCommands] Initializing Dictionary NLP service...")
            _turtle_service = DictionaryNLPService()
            methods = _turtle_service.initialize_turtle()
            print(f"[TurtleCommands] Service ready with {len(methods)} methods")
        return _turtle_service


def _try_direct_match(command: str) -> Optional[Dict]:
    command = command.strip().lower()
    match = re.match(r'^(forward|fd|backward|back|bk|left|lt|right|rt|circle|dot|pensize|speed|setheading|seth)\s+(-?\d+(?:\.\d+)?)$', command)
    if match:
        method_map = {"fd": "forward", "bk": "backward", "back": "backward", "lt": "left", "rt": "right", "seth": "setheading"}
        method_name = match.group(1)
        method_name = method_map.get(method_name, method_name)
        value = float(match.group(2)) if '.' in match.group(2) else int(match.group(2))
        return {
            "success": True,
            "executable": f"{method_name}({value})",
            "method": method_name,
            "parameters": {"value": value},
            "confidence": 1.0,
        }

    no_arg_match = re.match(r'^(penup|pu|pendown|pd|home|clear|reset|hideturtle|ht|showturtle|st|begin_fill|end_fill|stamp)$', command)
    if no_arg_match:
        method_map = {"pu": "penup", "pd": "pendown", "ht": "hideturtle", "st": "showturtle"}
        method_name = no_arg_match.group(1)
        method_name = method_map.get(method_name, method_name)
        return {
            "success": True,
            "executable": f"{method_name}()",
            "method": method_name,
            "parameters": {},
            "confidence": 1.0,
        }

    return None


def _split_compound_command(command: str) -> List[str]:
    processed = command.lower().strip()
    split_patterns = [
        r'\s+and\s+then\s+',
        r'\s+then\s+',
        r'\s+and\s+',
        r',\s*',
    ]
    parts = [processed]
    for pattern in split_patterns:
        new_parts = []
        for part in parts:
            split_result = re.split(pattern, part, flags=re.IGNORECASE)
            new_parts.extend([p.strip() for p in split_result if p.strip()])
        parts = new_parts
    return [p for p in parts if len(p) > 2] or [command]


def _process_single_command(command: str, service: DictionaryNLPService) -> Dict:
    preprocessed = service.preprocess(command)
    direct_result = _try_direct_match(preprocessed)
    if direct_result:
        return direct_result

    results = service.process(command)
    if not results or not results[0].get("success"):
        return {"success": False, "error": f"No matching command for: '{command}'"}

    r = results[0]
    return {
        "success": True,
        "executable": r.get("executable", ""),
        "method": r.get("method", ""),
        "parameters": r.get("parameters", {}),
        "confidence": r.get("confidence", 0.0),
    }


def _process_command_sync(command: str) -> Dict:
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
    try:
        print(f"\n{'='*60}")
        print(f"[NLP] Input: '{payload.command}'")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(_executor, _process_command_sync, payload.command)
        print(f"[NLP] Result: {result.get('executable')} (confidence={result.get('confidence', 0):.2f})")
        print(f"{'='*60}\n")
        return TurtleCommandResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/turtle_methods", response_model=TurtleMethodsResponse)
async def list_turtle_methods():
    try:
        service = _get_turtle_service()
        methods = service._methods
        return TurtleMethodsResponse(
            success=True,
            methods=[
                TurtleMethodInfo(name=m.name, params=[p["name"] for p in m.params])
                for m in methods
            ],
            total=len(methods)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/prewarm_turtle_pipeline")
async def prewarm_turtle_pipeline(background_tasks: BackgroundTasks):
    global _turtle_service
    try:
        if _turtle_service is not None:
            return {"status": "already_initialized", "method_count": len(_turtle_service._methods)}
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(_executor, _get_turtle_service)
        return {"status": "initialized", "method_count": len(_turtle_service._methods)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/turtle_cache")
async def clear_turtle_cache():
    global _turtle_service
    try:
        with _turtle_lock:
            _turtle_service = None
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
