# app/routers/turtle_execute.py
import os
from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter(tags=["Turtle Execute"])

# Streaming device configuration
STREAM_DEVICE_IP = "192.168.4.228"
STREAM_DEVICE_PORT = "8001"

BASE_EXEC_DIR = os.path.join(os.path.dirname(__file__), "..", "executions")

@router.get("/run_turtle/{conversation_id}")
async def run_turtle(conversation_id: int):
    """
    Collect Python files for this conversation (if any) + fetch runner.py via get_runner_code,
    then send them as { "files": { filename: content } } to the streaming device.
    """
    try:
        files: dict[str, str] = {}
        is_turtle_code = False

        # 1️⃣ Optional: collect any extra .py files from session directory
        session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")
        if os.path.isdir(session_dir):
            for filename in os.listdir(session_dir):
                if filename.endswith(".py"):
                    file_path = os.path.join(session_dir, filename)
                    with open(file_path, "r") as f:
                        content = f.read()

                    # detect turtle usage
                    if "turtle.Screen()" in content or "import turtle" in content:
                        is_turtle_code = True

                    # normalize screen.setup for streaming (non-runner files)
                    if is_turtle_code and filename != "runner.py":
                        content = re.sub(
                            r"(self\.screen|screen)\.setup\([^)]*\)",
                            r"\1.setup(800, 800, 50, 50)",
                            content,
                        )
                        if "screensize" not in content and "self.screen.setup" in content:
                            content = re.sub(
                                r"(self\.screen\.setup\(800, 800, 50, 50\))",
                                r"\1\n        self.screen.screensize(700, 700)",
                                content,
                            )

                    files[filename] = content

        # 2️⃣ Always fetch runner.py from get_runner_code
        get_runner_url = f"{CODE_API_BASE}/get_runner_code"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(get_runner_url, params={"conversation_id": conversation_id})

        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Failed to fetch runner code: {resp.text}",
            )

        data = resp.json()
        runner_code = data.get("code")
        if not runner_code:
            raise HTTPException(
                status_code=400,
                detail="get_runner_code response missing 'code'",
            )

        # mark that we have turtle code
        if "turtle" in runner_code:
            is_turtle_code = True

        # 2.1️⃣ Optionally ensure keep-alive for turtle window
        if is_turtle_code:
            if (
                "exitonclick()" not in runner_code
                and "done()" not in runner_code
                and "mainloop()" not in runner_code
                and "time.sleep" not in runner_code
            ):
                if "import time" not in runner_code:
                    runner_code = "import time\n" + runner_code
                runner_code = runner_code.rstrip() + "\n" \
                    "time.sleep(120)  # Keep window open for streaming (2 minutes)\n"

        # put into files dict as runner.py (this is what streaming server expects)
        files["runner.py"] = runner_code

        # 3️⃣ Validate
        if "runner.py" not in files:
            raise HTTPException(
                status_code=400,
                detail="runner.py not prepared for streaming device",
            )

        # 4️⃣ Send to streaming device
        stream_device_url = f"http://{STREAM_DEVICE_IP}:{STREAM_DEVICE_PORT}/run_turtle/{conversation_id}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            print(">>> Calling stream device:", stream_device_url, flush=True)
            response = await client.post(
                stream_device_url,
                json={"files": files},  # ✅ matches TurtleCodeRequest on streaming server
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Stream device returned error: {response.text}",
            )

        result = response.json()
        return {
            "result": "Turtle execution triggered on streaming device",
            "conversation_id": conversation_id,
            "device_response": result,
        }

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to streaming device at {STREAM_DEVICE_IP}:{STREAM_DEVICE_PORT}. Error: {str(e)}",
        )
    except HTTPException:
        # passthrough explicit HTTPExceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger turtle graphics: {str(e)}",
        )
