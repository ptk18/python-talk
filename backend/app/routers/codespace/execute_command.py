import os
import shutil
import subprocess
import sys
import tempfile
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Conversation
from app.models.schemas import ExecuteCommandRequest, SimpleCodeRequest
from app.nlp_v3.catalog import extract_from_file
from app.security import validate_code

router = APIRouter(tags=["Execute Command"])

BASE_EXEC_DIR = os.path.join(os.path.dirname(__file__), "..", "executions")
os.makedirs(BASE_EXEC_DIR, exist_ok=True)


def safe_filename(name: str) -> str:
    """Return a filesystem-safe filename component."""
    return "".join(c for c in name if c.isalnum() or c in ("_", "-")).rstrip()


@router.post("/execute_command")
def execute_command(request: ExecuteCommandRequest, db: Session = Depends(get_db)):
    convo = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if not convo.code or not convo.code.strip():
        raise HTTPException(status_code=400, detail="This conversation has no code uploaded. Please upload a Python file first.")

    is_safe, violations = validate_code(convo.code, strict_mode=False)
    if not is_safe:
        raise HTTPException(
            status_code=400,
            detail="Security validation failed:\n" + "\n".join(f"- {v}" for v in violations)
        )

    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{request.conversation_id}")

    # For first-time initialization, clear existing session directory to ensure clean state
    # This prevents old files from a deleted/reused conversation ID from persisting
    if request.executable == "first_time_created" and os.path.exists(session_dir):
        shutil.rmtree(session_dir)
    os.makedirs(session_dir, exist_ok=True)

    orig_fname = getattr(convo, "file_name", None) or "module.py"
    safe_module_fname = safe_filename(orig_fname)
    if not safe_module_fname.lower().endswith(".py"):
        safe_module_fname = safe_module_fname + ".py"

    module_path = os.path.join(session_dir, safe_module_fname)
    runner_path = os.path.join(session_dir, "runner.py")

    with open(module_path, "w", encoding="utf-8") as f:
        f.write(convo.code)

    try:
        catalog = extract_from_file(module_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse module to detect class: {e}")

    if not catalog.classes:
        raise HTTPException(
            status_code=400,
            detail=f"No class found in uploaded Python file '{orig_fname}'. Please ensure your file contains at least one class definition."
        )

    class_name = list(catalog.classes.keys())[0]

    if not os.path.exists(runner_path):
        module_name = os.path.splitext(safe_module_fname)[0]
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(f"from {module_name} import {class_name}\n")
            f.write("import sys\n")
            f.write("\n")
            f.write(f"obj = {class_name}()\n")

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
            raise HTTPException(status_code=500, detail="Execution timed out")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

    if request.executable != "first_time_created":
        executable = request.executable.strip()
        if "\n" in executable or ";" in executable:
            raise HTTPException(status_code=400, detail="Executable must be a single simple method call like 'pause()'")

        with open(runner_path, "a", encoding="utf-8") as f:
            f.write(f"print(obj.{executable})\n")

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

    executable = request.executable.strip()

    try:
        with open(runner_path, "a", encoding="utf-8") as f:
            for line in executable.splitlines():
                line = line.strip()
                if not line:
                    continue
                f.write(f"print(obj.{line})\n")

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

@router.get("/get_session_files")
def get_session_files(conversation_id: int = Query(..., description="Conversation ID to get all session files")):
    """
    Fetch all Python files from the session directory for a given conversation_id.
    Returns a dict mapping filename to file content.
    """
    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")

    if not os.path.exists(session_dir):
        raise HTTPException(
            status_code=404,
            detail=f"Session directory not found for conversation {conversation_id}."
        )

    try:
        files = {}
        for filename in os.listdir(session_dir):
            if filename.endswith('.py'):
                file_path = os.path.join(session_dir, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    files[filename] = f.read()

        if not files:
            raise HTTPException(
                status_code=404,
                detail=f"No Python files found in session {conversation_id}."
            )

        return {"conversation_id": conversation_id, "files": files}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read session files: {str(e)}")

@router.post("/save_runner_code")
def save_runner_code(request: dict):
    """
    Save edited runner.py code for a given conversation_id.
    """
    conversation_id = request.get("conversation_id")
    code = request.get("code")

    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required")

    if code is None:
        raise HTTPException(status_code=400, detail="code is required")

    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")
    runner_path = os.path.join(session_dir, "runner.py")

    if not os.path.exists(session_dir):
        os.makedirs(session_dir, exist_ok=True)

    try:
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(code)
        return {"message": "Code saved successfully", "conversation_id": conversation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save runner.py: {str(e)}")

@router.post("/save_file")
def save_file(request: dict, db: Session = Depends(get_db)):
    """
    Save any file in the conversation session directory.
    Also updates the database if this is the uploaded module file.
    """
    conversation_id = request.get("conversation_id")
    filename = request.get("filename")
    code = request.get("code")

    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required")

    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")

    if code is None:
        raise HTTPException(status_code=400, detail="code is required")

    # Validate filename for security
    if not filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Only Python files (.py) are supported")

    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Security validation - check code for dangerous patterns (use strict=False for user uploads)
    is_safe, violations = validate_code(code, strict_mode=False)
    if not is_safe:
        raise HTTPException(
            status_code=400,
            detail="Security validation failed:\n" + "\n".join(f"- {v}" for v in violations)
        )

    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")
    file_path = os.path.join(session_dir, filename)

    if not os.path.exists(session_dir):
        os.makedirs(session_dir, exist_ok=True)

    try:
        # Save file to session directory
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Check if this is the uploaded module file (not runner.py)
        # If so, update the database Conversation.code field
        if filename != "runner.py":
            convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if convo and convo.file_name == filename:
                convo.code = code
                db.commit()
                return {
                    "message": f"File {filename} saved successfully",
                    "conversation_id": conversation_id,
                    "updated_database": True
                }

        return {"message": f"File {filename} saved successfully", "conversation_id": conversation_id, "updated_database": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save {filename}: {str(e)}")

@router.get("/get_file")
def get_file(conversation_id: int = Query(..., description="Conversation ID"), 
             filename: str = Query(..., description="Filename to get")):
    """
    Get content of a specific file from the session directory.
    """
    # Validate filename for security
    if not filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Only Python files (.py) are supported")
    
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")
    file_path = os.path.join(session_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File {filename} not found for conversation {conversation_id}."
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        return {"conversation_id": conversation_id, "filename": filename, "code": code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read {filename}: {str(e)}")

@router.get("/list_files")
def list_files(conversation_id: int = Query(..., description="Conversation ID")):
    """
    List all Python files in the conversation session directory.
    Returns files with uploaded files first, then runner.py
    """
    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")

    if not os.path.exists(session_dir):
        return {"conversation_id": conversation_id, "files": []}

    try:
        files = []
        for filename in os.listdir(session_dir):
            if filename.endswith('.py'):
                files.append(filename)

        # Sort files: uploaded files first (not runner.py), then runner.py
        uploaded_files = sorted([f for f in files if f != 'runner.py'])
        runner_files = [f for f in files if f == 'runner.py']

        return {"conversation_id": conversation_id, "files": uploaded_files + runner_files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.delete("/delete_file")
def delete_file(request: dict):
    """
    Delete a file from the conversation session directory.
    """
    conversation_id = request.get("conversation_id")
    filename = request.get("filename")

    if not conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required")
    
    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")

    # Prevent deletion of runner.py
    if filename == "runner.py":
        raise HTTPException(status_code=400, detail="Cannot delete runner.py")

    # Validate filename for security
    if not filename.endswith('.py'):
        raise HTTPException(status_code=400, detail="Only Python files (.py) are supported")
    
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")
    file_path = os.path.join(session_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File {filename} not found for conversation {conversation_id}."
        )

    try:
        os.remove(file_path)
        return {"message": f"File {filename} deleted successfully", "conversation_id": conversation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete {filename}: {str(e)}")


@router.post("/execute_simple")
def execute_simple(request: SimpleCodeRequest):
    """
    Execute simple Python code without a conversation/session.
    Uses strict_mode=True for security (only whitelisted modules allowed).
    Useful for quick code snippets and testing.
    """
    if not request.code or not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    # Security validation with strict mode (whitelist only)
    is_safe, violations = validate_code(request.code, strict_mode=True)
    if not is_safe:
        raise HTTPException(
            status_code=400,
            detail="Security validation failed:\n" + "\n".join(f"- {v}" for v in violations)
        )

    # Validate timeout (max 60 seconds for simple execution)
    timeout = min(request.timeout or 30, 60)

    try:
        # Create a temporary file to store the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(request.code)
            temp_file_path = temp_file.name

        try:
            # Execute the Python code in a subprocess
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tempfile.gettempdir()  # Run in temp directory for security
            )

            # Prepare response
            output = result.stdout if result.stdout else ""
            error = result.stderr if result.stderr else ""
            success = result.returncode == 0

            # If there's an error but no stderr, include returncode info
            if not success and not error:
                error = f"Process exited with code {result.returncode}"

            return {
                "output": output,
                "error": error,
                "success": success
            }

        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    except subprocess.TimeoutExpired:
        return {
            "output": "",
            "error": f"Code execution timed out ({timeout} seconds limit)",
            "success": False
        }
    except Exception as e:
        return {
            "output": "",
            "error": f"Execution error: {str(e)}",
            "success": False
        }