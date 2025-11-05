# app/routes/execute_command.py
import os
import subprocess
import sys
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Conversation
from app.models.schemas import ExecuteCommandRequest
# import your extractor to detect class name
from app.nlp_v2.extract_catalog_from_source_code.ast_extractor import extract_from_file
from fastapi import Query

router = APIRouter(tags=["Execute Command"])

BASE_EXEC_DIR = os.path.join(os.path.dirname(__file__), "..", "executions")
os.makedirs(BASE_EXEC_DIR, exist_ok=True)


def safe_filename(name: str) -> str:
    """Return a filesystem-safe filename component."""
    return "".join(c for c in name if c.isalnum() or c in ("_", "-")).rstrip()


@router.post("/execute_command")
def execute_command(request: ExecuteCommandRequest, db: Session = Depends(get_db)):
    # fetch conversation and code
    convo = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not convo.code:
        raise HTTPException(status_code=400, detail="This conversation has no code")

    # prepare session directory: app/executions/session_<id>/
    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{request.conversation_id}")
    os.makedirs(session_dir, exist_ok=True)

    # use the original file_name if present (otherwise default to module.py)
    orig_fname = getattr(convo, "file_name", None) or "module.py"
    safe_module_fname = safe_filename(orig_fname)
    if not safe_module_fname.lower().endswith(".py"):
        safe_module_fname = safe_module_fname + ".py"

    module_path = os.path.join(session_dir, safe_module_fname)
    runner_path = os.path.join(session_dir, "runner.py")

    # 1) Ensure module file is written (only write if not exists or overwrite if you prefer)
    if not os.path.exists(module_path):
        # write the module source to file
        with open(module_path, "w", encoding="utf-8") as f:
            f.write(convo.code)

    # 2) Detect class name using extract_from_file (works off a file path)
    try:
        catalog = extract_from_file(module_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse module to detect class: {e}")

    if not catalog.classes:
        raise HTTPException(status_code=400, detail="No class found in uploaded module")

    # pick the first class by name
    class_name = list(catalog.classes.keys())[0]

    # 3) Initialize runner.py if not exists
    if not os.path.exists(runner_path):
        # runner imports the user's module and creates a persistent instance
        module_name = os.path.splitext(safe_module_fname)[0]
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(f"from {module_name} import {class_name}\n")
            f.write("import sys\n")
            f.write("\n")
            f.write(f"obj = {class_name}()\n")
            f.write("# session runner - commands will be appended below\n")

    # 4) Append execution command line
    # request.executable is expected like "pause()" or "play()" - we will call obj.pause() -> print(obj.pause())
    # Sanitize a little: strip surrounding whitespace
    executable = request.executable.strip()
    # basic safety: do not allow multi-line statements
    if "\n" in executable or ";" in executable:
        raise HTTPException(status_code=400, detail="Executable must be a single simple method call like 'pause()'")

    with open(runner_path, "a", encoding="utf-8") as f:
        # append a print wrapper so we get the return value or printed output aggregated in stdout
        f.write(f"print(obj.{executable})\n")

    # 5) Execute runner.py with working dir = session_dir so the module import resolves
    try:
        # run the runner; cwd ensures `from module import Class` will find the module file in same dir
        result = subprocess.run(
            [sys.executable, "runner.py"],
            capture_output=True,
            text=True,
            cwd=session_dir,
            timeout=10
        )
        # prefer stdout; if empty, return stderr
        output = result.stdout.strip() or result.stderr.strip()
        return {"output": output or "No output"}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Execution timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

@router.post("/rerun_command")
def rerun_command(conversation_id: int = Query(..., description="ID of the conversation to rerun")):
    """
    Re-run the previously prepared runner.py for a given conversation_id.
    This assumes /execute_command has already created session_<id>/runner.py.
    """
    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")
    runner_path = os.path.join(session_dir, "runner.py")

    if not os.path.exists(runner_path):
        raise HTTPException(status_code=404, detail="runner.py not found for this conversation. Run /execute_command first.")

    try:
        result = subprocess.run(
            [sys.executable, "runner.py"],
            capture_output=True,
            text=True,
            cwd=session_dir,
            timeout=10
        )
        output = result.stdout.strip() or result.stderr.strip()
        return {"output": output or "No output"}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Re-run timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-run error: {str(e)}")
    
    
@router.post("/append_command")
def append_command(request: ExecuteCommandRequest):
    """
    Append a new command (like play(), pause()) to an existing runner.py
    without executing it.
    """
    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{request.conversation_id}")
    runner_path = os.path.join(session_dir, "runner.py")

    if not os.path.exists(runner_path):
        raise HTTPException(
            status_code=404,
            detail="runner.py not found for this conversation. Run /execute_command first."
        )

    # Sanitize input
    executable = request.executable.strip()
    if "\n" in executable or ";" in executable:
        raise HTTPException(
            status_code=400,
            detail="Executable must be a single-line method call like 'pause()'"
        )

    try:
        with open(runner_path, "a", encoding="utf-8") as f:
            f.write(f"print(obj.{executable})\n")

        return {"message": f"Appended command '{executable}' successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to append command: {str(e)}")

@router.get("/get_runner_code")
def get_runner_code(conversation_id: int = Query(..., description="Conversation ID to get runner.py code")):
    """
    Fetch the full content of runner.py for a given conversation_id.
    """
    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")
    runner_path = os.path.join(session_dir, "runner.py")

    if not os.path.exists(runner_path):
        raise HTTPException(
            status_code=404,
            detail=f"runner.py not found for conversation {conversation_id}. Run /execute_command first."
        )

    try:
        with open(runner_path, "r", encoding="utf-8") as f:
            code = f.read()
        return {"conversation_id": conversation_id, "code": code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read runner.py: {str(e)}")
