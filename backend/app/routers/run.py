from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import tempfile
import os
import sys
from typing import Dict, Any

router = APIRouter(prefix="/run", tags=["code_execution"])

class CodeExecutionRequest(BaseModel):
    code: str

class CodeExecutionResponse(BaseModel):
    output: str
    error: str = ""
    success: bool = True

@router.post("/", response_model=CodeExecutionResponse)
async def execute_python_code(request: CodeExecutionRequest):
    """Execute Python code and return the output"""
    
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    
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
                timeout=30,  # 30 second timeout
                cwd=tempfile.gettempdir()  # Run in temp directory for security
            )
            
            # Prepare response
            output = result.stdout if result.stdout else ""
            error = result.stderr if result.stderr else ""
            success = result.returncode == 0
            
            # If there's an error but no stderr, include returncode info
            if not success and not error:
                error = f"Process exited with code {result.returncode}"
            
            return CodeExecutionResponse(
                output=output,
                error=error,
                success=success
            )
            
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
                
    except subprocess.TimeoutExpired:
        return CodeExecutionResponse(
            output="",
            error="Code execution timed out (30 seconds limit)",
            success=False
        )
    except Exception as e:
        return CodeExecutionResponse(
            output="",
            error=f"Execution error: {str(e)}",
            success=False
        )
