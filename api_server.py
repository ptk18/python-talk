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

async def stream_screen(region, process, ws_url):
    ssl_ctx = ssl._create_unverified_context()
    logging.info(f"Streaming to {ws_url}")

    async with websockets.connect(ws_url, ssl=ssl_ctx, max_size=None) as ws:
        with mss.mss() as sct:
            while process.poll() is None:
                img = np.array(sct.grab(region))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                ok, buf = cv2.imencode(
                    ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                )
                if not ok:
                    continue

                await ws.send(base64.b64encode(buf).decode())
                await asyncio.sleep(0.03)

    logging.info("Streaming finished")

# -------------------- ROUTES --------------------

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/runturtle/{cid}")
async def run_turtle(cid: int, req: TurtleCodeRequest):
    session_dir = os.path.join(BASE_SESSION_DIR, f"session_{cid}")

    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)

    os.makedirs(session_dir, exist_ok=True)

    if "runner.py" not in req.files:
        raise HTTPException(400, "runner.py missing")

    # Write files
    for name, content in req.files.items():
        with open(os.path.join(session_dir, name), "w") as f:
            f.write(content)

    logging.info(f"Starting turtle session {cid}")

    # Start turtle process
    proc = subprocess.Popen(
        ["python3", "runner.py"],
        cwd=session_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,  # allows killing child processes
    )

    region = {
        "left": 50,
        "top": 50,
        "width": 800,
        "height": 800,
    }

    ws_url = f"{WS_PUBLISH_BASE}/{cid}"

    # Run streaming in background
    asyncio.create_task(stream_screen(region, proc, ws_url))

    return {
        "status": "started",
        "conversation_id": cid,
        "ws_subscribe_url": f"wss://161.246.5.67:5050/ws/subscribe/{cid}",
    }
    
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
