from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import os
import asyncio
import ssl
import websockets
import cv2
import mss
import numpy as np
import base64
import shutil
import signal
import logging

TURTLE_PROCESSES = {}
TURTLE_STDIN = {}

# -------------------- APP SETUP --------------------

app = FastAPI(title="Pi Turtle Streaming Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

BASE_SESSION_DIR = "/home/pi/turtle_sessions"
os.makedirs(BASE_SESSION_DIR, exist_ok=True)

WS_PUBLISH_BASE = "wss://161.246.5.67:5050/publish"

# -------------------- MODELS --------------------

class TurtleCodeRequest(BaseModel):
    files: dict[str, str]

# -------------------- STREAMING --------------------

async def stream_screen(region, turtle_process, ws_url, cid: int):
    print(f"[STREAM] CID={cid}")
    print(f"[STREAM] Connecting to {ws_url}")

    ssl_ctx = ssl._create_unverified_context()
    last_frame = None
    frame_count = 0

    async with websockets.connect(ws_url, ssl=ssl_ctx) as ws:
        print("[STREAM] WebSocket connected")

        with mss.mss() as sct:
            while True:
                if turtle_process.poll() is not None:
                    print("[STREAM] Turtle process finished")
                    break

                img = np.array(sct.grab(region))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                _, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])

                jpg_text = base64.b64encode(buf).decode("utf-8")
                last_frame = jpg_text
                frame_count += 1

                if frame_count % 30 == 0:
                    print(f"[STREAM] Sent frame {frame_count}, size={len(jpg_text)}")

                await ws.send(jpg_text)
                await asyncio.sleep(0.03)

            # FREEZE LAST FRAME
            if last_frame:
                print("[STREAM] Freezing last frame (3 seconds)")
                for _ in range(90):  # ~3 seconds @30fps
                    await ws.send(last_frame)
                    await asyncio.sleep(0.03)

        print("[STREAM] Streaming finished")

# -------------------- ROUTES --------------------

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/runturtle/{cid}")
async def run_turtle(cid: int, req: TurtleCodeRequest):
    print(f"[RUNTURTLE] CID={cid}")
    print(f"[RUNTURTLE] Files received: {list(req.files.keys())}")

    temp_dir = f"session_{cid}"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        for name, content in req.files.items():
            path = os.path.join(temp_dir, name)
            
            if name == "runner.py":
                # --- FIXED INDENTATION HERE ---
                setup_code = """import turtle
try:
    # width, height, startx, starty
    turtle.setup(width=600, height=450, startx=0, starty=0)
except:
    pass
"""
                # Combine: Setup + User Code + Sleep
                content = setup_code + "\n" + content + "\n\nimport time\ntime.sleep(10)" 
                # ------------------------------
                
            with open(path, "w") as f:
                f.write(content)

            if name == "runner.py":
                print("[RUNTURTLE] runner.py preview:")
                print("--------------------------------")
                print("\n".join(content.splitlines()[:20]))
                print("--------------------------------")

        if "runner.py" not in req.files:
            raise HTTPException(400, "runner.py missing")

        print("[RUNTURTLE] Starting turtle process")
        proc = subprocess.Popen(["python3", "runner.py"], cwd=temp_dir)

        # Region to capture (Matches the setup(600, 450) + some border room)
        region = {
            "left": 0,    # Capture from left edge
            "top": 50,     # Capture from top edge
            "width": 600, # Slightly wider than 600 to see borders
            "height": 450 # Slightly taller than 450 to see borders
        }

        ws_url = f"wss://161.246.5.67:5050/publish/{cid}"
        print(f"[RUNTURTLE] Streaming to {ws_url}")

        await stream_screen(region, proc, ws_url, cid)

        proc.wait()
        print("[RUNTURTLE] Turtle process exited cleanly")

        return {"status": "done", "cid": cid}

    finally:
        print("[RUNTURTLE] Cleaning up")
        shutil.rmtree(temp_dir, ignore_errors=True)

      
@app.post("/start_turtle/{cid}")
def start_turtle(cid: int):
    if cid in TURTLE_PROCESSES:
        return {"status": "already_running"}

    proc = subprocess.Popen(
        ["python3", "turtle_runtime.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
        text=True,
        bufsize=1
    )

    TURTLE_PROCESSES[cid] = proc

    return {
        "status": "started",
        "conversation_id": cid
    }
    
@app.post("/turtle_command/{cid}")
def turtle_command(cid: int, command: str):
    proc = TURTLE_PROCESSES.get(cid)
    if not proc:
        raise HTTPException(404, "Turtle not running")

    try:
        proc.stdin.write(command + "\n")
        proc.stdin.flush()
    except Exception:
        raise HTTPException(500, "Failed to send command")

    return {"status": "sent", "command": command}


@app.post("/kill/{cid}")
def kill_turtle(cid: int):
    session_dir = os.path.join(BASE_SESSION_DIR, f"session_{cid}")

    if not os.path.exists(session_dir):
        raise HTTPException(404, "Session not found")

    try:
        for p in os.popen("ps -eo pid,cmd").read().splitlines():
            if f"session_{cid}" in p:
                pid = int(p.strip().split()[0])
                os.killpg(os.getpgid(pid), signal.SIGTERM)
    except Exception:
        pass

    shutil.rmtree(session_dir, ignore_errors=True)
    return {"status": "killed"}