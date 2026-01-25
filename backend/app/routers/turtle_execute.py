# app/routers/turtle_execute.py
import os
from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter(tags=["Turtle Execute"])

# Streaming device configuration (override via env to support remote devices)
STREAM_DEVICE_BASE_URL = os.getenv("STREAM_DEVICE_BASE_URL")
STREAM_DEVICE_IP = os.getenv("STREAM_DEVICE_IP", "161.246.5.67")
STREAM_DEVICE_PORT = os.getenv("STREAM_DEVICE_PORT", "8001")


def _get_stream_device_base_url() -> str:
    """Return the base URL used to reach the streaming device."""
    if STREAM_DEVICE_BASE_URL:
        return STREAM_DEVICE_BASE_URL.rstrip("/")
    return f"http://161.246.5.67:8001"

BASE_EXEC_DIR = os.path.join(os.path.dirname(__file__), "..", "executions")

@router.get("/run_turtle/{conversation_id}")
async def run_turtle(conversation_id: int):
    """
    Send the conversation's runner.py and all Python files from session directory to streaming device.
    The device at 161.246.5.67 will execute the code and stream via WebSocket.
    """
    try:
        # Get the session directory
        session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")
        runner_path = os.path.join(session_dir, "runner.py")

        if not os.path.exists(runner_path):
            raise HTTPException(
                status_code=404,
                detail=f"runner.py not found for conversation {conversation_id}. Run /execute_command first."
            )

        # Read all Python files from the session directory
        files = {}
        is_turtle_code = False

        for filename in os.listdir(session_dir):
            if filename.endswith('.py'):
                file_path = os.path.join(session_dir, filename)
                with open(file_path, 'r') as f:
                    content = f.read()

                    # Check if this is turtle code
                    if "turtle.Screen()" in content or "import turtle" in content:
                        is_turtle_code = True

                    # Override screen.setup() calls in any Python file to match streaming region
                    if is_turtle_code and filename != "runner.py":
                        # Replace any screen.setup() calls with our streaming-friendly settings
                        import re
                        # Match patterns like: screen.setup(...) or self.screen.setup(...)
                        content = re.sub(
                            r'(self\.screen|screen)\.setup\([^)]*\)',
                            r'\1.setup(800, 800, 50, 50)',
                            content
                        )
                        # Also ensure screensize is set after setup if not present
                        if 'screensize' not in content and 'self.screen.setup' in content:
                            content = re.sub(
                                r'(self\.screen\.setup\(800, 800, 50, 50\))',
                                r'\1\n        self.screen.screensize(700, 700)',
                                content
                            )

                    # If this is runner.py for turtle code, add keep-alive mechanism
                    if filename == "runner.py" and is_turtle_code:
                        # Check if it needs a keep-alive mechanism
                        if "exitonclick()" not in content and \
                           "done()" not in content and \
                           "mainloop()" not in content and \
                           "time.sleep" not in content:
                            # Add a delay to keep the window open for streaming
                            if "import time" not in content:
                                content = "import time\n" + content
                            content = content.rstrip() + "\ntime.sleep(120)  # Keep window open for streaming (2 minutes)\n"

                    files[filename] = content

        if not files:
            raise HTTPException(
                status_code=404,
                detail=f"No Python files found in session {conversation_id}"
            )

        # Send all files to streaming device
        stream_device_url = f"{_get_stream_device_base_url()}/runturtle/{conversation_id}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                stream_device_url,
                json={"files": files}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Stream device returned error: {response.text}"
                )

            result = response.json()
            return {
                "result": "Turtle execution triggered on streaming device",
                "conversation_id": conversation_id,
                "device_response": result,
                "ws_url": f"wss://161.246.5.67:5050/ws/subscribe/{conversation_id}"
            }

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to streaming device at {_get_stream_device_base_url()}. Error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger turtle graphics: {str(e)}"
        )
