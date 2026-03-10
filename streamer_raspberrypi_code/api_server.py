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
STREAM_TASKS = {}

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
    last_small_gray = None

    async with websockets.connect(ws_url, ssl=ssl_ctx) as ws:
        print("[STREAM] WebSocket connected")

        with mss.mss() as sct:
            while True:
                if turtle_process.poll() is not None:
                    print("[STREAM] Turtle process finished")
                    break

                img = np.array(sct.grab(region))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                small = cv2.resize(frame, (120, 120))
                gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)

                changed = False
                if last_small_gray is None:
                    changed = True
                else:
                    diff = cv2.absdiff(gray, last_small_gray)
                    changed = float(np.mean(diff)) > 2.0

                if changed:
                    _, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                    jpg_text = base64.b64encode(buf).decode("utf-8")
                    await ws.send(jpg_text)
                    print(f"[STREAM] Sent changed frame for CID={cid}")
                    last_small_gray = gray

                await asyncio.sleep(0.1)

        print("[STREAM] Streaming finished")

# -------------------- ROUTES --------------------

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/runturtle/{cid}")
async def run_turtle(cid: int, req: TurtleCodeRequest):
    raise HTTPException(
        status_code=410,
        detail="Deprecated. Use /start_turtle/{cid} and /turtle_command/{cid}"
    )

      
@app.post("/start_turtle/{cid}")
async def start_turtle(cid: int):
    if cid in TURTLE_PROCESSES:
        return {"status": "already_running", "conversation_id": cid}

    proc = subprocess.Popen(
        ["python3", "/home/pi/turtle_runtime.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
        text=True,
        bufsize=1
    )

    TURTLE_PROCESSES[cid] = proc
    TURTLE_STDIN[cid] = proc.stdin

    region = {
        "left": 0,
        "top": 50,
        "width": 800,
        "height": 800
    }

    ws_url = f"wss://161.246.5.67:5050/publish/{cid}"
    STREAM_TASKS[cid] = asyncio.create_task(
        stream_screen(region, proc, ws_url, cid)
    )

    return {
        "status": "started",
        "conversation_id": cid
    }


@app.post("/turtle_command/{cid}")
def turtle_command(cid: int, command: str):
    proc = TURTLE_PROCESSES.get(cid)
    if not proc:
        raise HTTPException(404, "Turtle not running")

    if proc.poll() is not None:
        TURTLE_PROCESSES.pop(cid, None)
        TURTLE_STDIN.pop(cid, None)
        STREAM_TASKS.pop(cid, None)
        raise HTTPException(500, "Turtle process already exited")

    try:
        print(f"[API] Sending command to CID={cid}: {command}", flush=True)
        proc.stdin.write(command + "\n")
        proc.stdin.flush()
    except Exception as e:
        raise HTTPException(500, f"Failed to send command: {e}")

    return {"status": "sent", "command": command}


@app.post("/kill/{cid}")
def kill_turtle(cid: int):
    proc = TURTLE_PROCESSES.get(cid)
    if not proc:
        raise HTTPException(404, "Turtle not running")

    try:
        if proc.stdin:
            proc.stdin.write("__EXIT__\n")
            proc.stdin.flush()
    except Exception:
        pass

    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        pass

    TURTLE_PROCESSES.pop(cid, None)
    TURTLE_STDIN.pop(cid, None)
    STREAM_TASKS.pop(cid, None)

    return {"status": "killed", "conversation_id": cid}