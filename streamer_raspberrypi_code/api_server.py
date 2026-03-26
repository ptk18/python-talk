# code in pi5 : api_server.py
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
import signal
import logging
import threading

TURTLE_PROCESSES = {}
TURTLE_STDIN = {}
STREAM_TASKS = {}
CURRENT_CID = None

app = FastAPI(title="Pi Turtle Streaming Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

BASE_SESSION_DIR = "/home/pi/turtle_sessions"
os.makedirs(BASE_SESSION_DIR, exist_ok=True)

WS_PUBLISH_BASE = "wss://161.246.5.67:5050/publish"
RUNTIME_PATH = "/home/pi/turtle_runtime.py"


class TurtleCodeRequest(BaseModel):
    files: dict[str, str]


def _pipe_reader(prefix: str, pipe):
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            print(f"{prefix} {line.rstrip()}", flush=True)
    except Exception as e:
        print(f"{prefix} reader error: {e}", flush=True)


async def stream_screen_burst(region, turtle_process, ws_url, cid: int, duration: float = 10.0):
    print(f"[STREAM] BURST CID={cid}", flush=True)
    print(f"[STREAM] Connecting to {ws_url}", flush=True)

    ssl_ctx = ssl._create_unverified_context()
    last_small_gray = None
    loop = asyncio.get_running_loop()
    end_time = loop.time() + duration

    try:
        async with websockets.connect(ws_url, ssl=ssl_ctx) as ws:
            print("[STREAM] WebSocket connected", flush=True)

            with mss.mss() as sct:
                while loop.time() < end_time:
                    if turtle_process.poll() is not None:
                        print("[STREAM] Turtle process finished", flush=True)
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
                        _, buf = cv2.imencode(
                            ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50]
                        )
                        jpg_text = base64.b64encode(buf).decode("utf-8")
                        await ws.send(jpg_text)
                        last_small_gray = gray
                        print(f"[STREAM] Sent changed frame for CID={cid}", flush=True)

                    await asyncio.sleep(0.05)

        print(f"[STREAM] Burst finished for CID={cid}", flush=True)

    except asyncio.CancelledError:
        print(f"[STREAM] Burst cancelled for CID={cid}", flush=True)
        raise
    except Exception as e:
        print(f"[STREAM] ERROR for CID={cid}: {e}", flush=True)


def start_stream_burst(cid: int, proc):
    region = {
        "left": 0,
        "top": 0,
        "width": 1000,
        "height": 1000,
    }

    ws_url = f"{WS_PUBLISH_BASE}/{cid}"

    old_task = STREAM_TASKS.get(cid)
    if old_task and not old_task.done():
        old_task.cancel()

    STREAM_TASKS[cid] = asyncio.create_task(
        stream_screen_burst(region, proc, ws_url, cid, duration=10.0)
    )


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/runturtle/{cid}")
async def run_turtle_deprecated(cid: int, req: TurtleCodeRequest):
    raise HTTPException(
        status_code=410,
        detail="Deprecated. Use /start_turtle/{cid} and /turtle_command/{cid}",
    )


@app.post("/start_turtle/{cid}")
async def start_turtle(cid: int):
    global CURRENT_CID

    # kill previous app if opening another one
    if CURRENT_CID is not None and CURRENT_CID != cid:
        old_proc = TURTLE_PROCESSES.get(CURRENT_CID)
        if old_proc:
            try:
                if old_proc.stdin:
                    old_proc.stdin.write("__EXIT__\n")
                    old_proc.stdin.flush()
            except Exception:
                pass

            try:
                os.killpg(os.getpgid(old_proc.pid), signal.SIGTERM)
            except Exception:
                pass

        TURTLE_PROCESSES.pop(CURRENT_CID, None)
        TURTLE_STDIN.pop(CURRENT_CID, None)

        old_task = STREAM_TASKS.pop(CURRENT_CID, None)
        if old_task and not old_task.done():
            old_task.cancel()

    # same app already running -> do not reset turtle, just burst stream again
    if cid in TURTLE_PROCESSES:
        proc = TURTLE_PROCESSES[cid]
        if proc.poll() is None:
            CURRENT_CID = cid
            start_stream_burst(cid, proc)
            return {
                "status": "already_running",
                "conversation_id": cid,
                "fresh_runtime": False,
            }
        TURTLE_PROCESSES.pop(cid, None)
        TURTLE_STDIN.pop(cid, None)
        old_task = STREAM_TASKS.pop(cid, None)
        if old_task and not old_task.done():
            old_task.cancel()

    env = os.environ.copy()
    env["DISPLAY"] = env.get("DISPLAY", ":0")

    proc = subprocess.Popen(
        ["python3", RUNTIME_PATH],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
        text=True,
        bufsize=1,
        env=env,
    )

    TURTLE_PROCESSES[cid] = proc
    TURTLE_STDIN[cid] = proc.stdin
    CURRENT_CID = cid

    threading.Thread(
        target=_pipe_reader,
        args=(f"[RUNTIME STDOUT cid={cid}]", proc.stdout),
        daemon=True,
    ).start()

    threading.Thread(
        target=_pipe_reader,
        args=(f"[RUNTIME STDERR cid={cid}]", proc.stderr),
        daemon=True,
    ).start()

    await asyncio.sleep(1.0)

    if proc.poll() is not None:
        raise HTTPException(
            status_code=500,
            detail=f"turtle_runtime.py exited immediately with code {proc.returncode}",
        )

    start_stream_burst(cid, proc)

    return {
        "status": "started",
        "conversation_id": cid,
        "fresh_runtime": True,
    }


@app.post("/turtle_command/{cid}")
async def turtle_command(cid: int, command: str, replay: bool = False):
    proc = TURTLE_PROCESSES.get(cid)
    if not proc:
        raise HTTPException(404, "Turtle not running")

    if proc.poll() is not None:
        TURTLE_PROCESSES.pop(cid, None)
        TURTLE_STDIN.pop(cid, None)
        old_task = STREAM_TASKS.pop(cid, None)
        if old_task and not old_task.done():
            old_task.cancel()
        raise HTTPException(500, "Turtle process already exited")

    clean_line = command.strip()
    if not clean_line or clean_line.startswith("#"):
        return {"status": "ignored", "reason": "comment_or_empty"}

    try:
        print(f"[API] Sending command to CID={cid}: {clean_line} replay={replay}", flush=True)
        proc.stdin.write(clean_line + "\n")
        proc.stdin.flush()

        # only restart burst for normal single commands
        # replay mode sends many lines, so don't keep cancelling burst every line
        if not replay:
            start_stream_burst(cid, proc)

    except Exception as e:
        raise HTTPException(500, f"Failed to send command: {e}")

    return {
        "status": "sent",
        "command": clean_line,
        "replay": replay,
    }

@app.post("/kill/{cid}")
def kill_turtle(cid: int):
    global CURRENT_CID

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

    task = STREAM_TASKS.pop(cid, None)
    if task and not task.done():
        task.cancel()

    if CURRENT_CID == cid:
        CURRENT_CID = None

    return {"status": "killed", "conversation_id": cid}