# code in pi5 : api_server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
DONE_EVENTS = {}

app = FastAPI(title="Pi Turtle Streaming Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)

BASE_SESSION_DIR = "/home/pi/Desktop/GUI_Stream/turtle_sessions"
os.makedirs(BASE_SESSION_DIR, exist_ok=True)

WS_PUBLISH_BASE = "wss://161.246.5.67:443/publish"
RUNTIME_PATH = "/home/pi//Desktop/GUI_Stream/turtle_runtime.py"


def _pipe_reader(prefix: str, pipe, cid: int):
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break

            line = line.rstrip()
            print(f"{prefix} {line}", flush=True)

            if line == "[RUNTIME] OK":
                evt = DONE_EVENTS.get(cid)
                if evt:
                    evt.set()

    except Exception as e:
        print(f"{prefix} reader error: {e}", flush=True)

async def stream_screen_loop(region, turtle_process, ws_url, cid: int):
    print(f"[STREAM] LOOP START CID={cid}", flush=True)
    print(f"[STREAM] Connecting to {ws_url}", flush=True)

    ssl_ctx = ssl._create_unverified_context()

    try:
        async with websockets.connect(
            ws_url,
            ssl=ssl_ctx,
            ping_interval=20,
            ping_timeout=20,
            max_size=None,
        ) as ws:
            print(f"[STREAM] WebSocket connected for CID={cid}", flush=True)

            with mss.mss() as sct:
                while True:
                    if turtle_process.poll() is not None:
                        print(f"[STREAM] Turtle process finished for CID={cid}", flush=True)
                        break

                    img = np.array(sct.grab(region))
                    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                    _, buf = cv2.imencode(
                        ".jpg",
                        frame,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 65],
                    )
                    jpg_text = base64.b64encode(buf).decode("utf-8")
                    await ws.send(jpg_text)

                    await asyncio.sleep(0.05)   # around 20 FPS

    except asyncio.CancelledError:
        print(f"[STREAM] LOOP CANCELLED CID={cid}", flush=True)
        raise
    except Exception as e:
        print(f"[STREAM] LOOP ERROR CID={cid}: {e}", flush=True)
    finally:
        print(f"[STREAM] LOOP END CID={cid}", flush=True)


def start_stream_loop(cid: int, proc):
    region = {
        "left": 0,
        "top": 0,
        "width": 1000,
        "height": 1000,
    }

    old_task = STREAM_TASKS.get(cid)
    if old_task and not old_task.done():
        return

    ws_url = f"{WS_PUBLISH_BASE}/{cid}"
    STREAM_TASKS[cid] = asyncio.create_task(
        stream_screen_loop(region, proc, ws_url, cid)
    )


async def stop_stream_loop(cid: int):
    task = STREAM_TASKS.pop(cid, None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def stop_turtle_session(cid: int):
    global CURRENT_CID

    proc = TURTLE_PROCESSES.get(cid)

    if proc:
        try:
            if proc.stdin:
                proc.stdin.write("__EXIT__\n")
                proc.stdin.flush()
        except Exception:
            pass

        await asyncio.sleep(0.2)

        try:
            if proc.poll() is None:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            pass

    TURTLE_PROCESSES.pop(cid, None)
    TURTLE_STDIN.pop(cid, None)
    DONE_EVENTS.pop(cid, None)

    await stop_stream_loop(cid)

    if CURRENT_CID == cid:
        CURRENT_CID = None


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/start_turtle/{cid}")
async def start_turtle(cid: int):
    global CURRENT_CID

    if CURRENT_CID is not None and CURRENT_CID != cid:
        await stop_turtle_session(CURRENT_CID)

    if cid in TURTLE_PROCESSES:
        proc = TURTLE_PROCESSES[cid]
        if proc.poll() is None:
            CURRENT_CID = cid
            start_stream_loop(cid, proc)
            return {
                "status": "already_running",
                "conversation_id": cid,
                "fresh_runtime": False,
            }
        else:
            await stop_turtle_session(cid)

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
    DONE_EVENTS[cid] = threading.Event()
    CURRENT_CID = cid

    threading.Thread(
        target=_pipe_reader,
        args=(f"[RUNTIME STDOUT cid={cid}]", proc.stdout, cid),
        daemon=True,
    ).start()

    threading.Thread(
        target=_pipe_reader,
        args=(f"[RUNTIME STDERR cid={cid}]", proc.stderr, cid),
        daemon=True,
    ).start()

    await asyncio.sleep(1.0)

    if proc.poll() is not None:
        await stop_turtle_session(cid)
        raise HTTPException(
            status_code=500,
            detail=f"turtle_runtime.py exited immediately with code {proc.returncode}",
        )

    start_stream_loop(cid, proc)

    return {
        "status": "started",
        "conversation_id": cid,
        "fresh_runtime": True,
    }


@app.post("/turtle_command/{cid}")
async def turtle_command(cid: int, command: str):
    proc = TURTLE_PROCESSES.get(cid)
    if not proc:
        raise HTTPException(404, "Turtle not running")

    if proc.poll() is not None:
        await stop_turtle_session(cid)
        raise HTTPException(500, "Turtle process already exited")

    clean_line = command.strip()
    if not clean_line or clean_line.startswith("#"):
        return {"status": "ignored", "reason": "comment_or_empty"}

    try:
        evt = DONE_EVENTS.setdefault(cid, threading.Event())
        evt.clear()

        print(f"[API] Sending command to CID={cid}: {clean_line}", flush=True)
        proc.stdin.write(clean_line + "\n")
        proc.stdin.flush()

        done = await asyncio.to_thread(evt.wait, 15.0)
        if not done:
            raise HTTPException(504, f"Turtle command timed out: {clean_line}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to send command: {e}")

    return {"status": "sent", "command": clean_line}


@app.post("/kill/{cid}")
async def kill_turtle(cid: int):
    proc = TURTLE_PROCESSES.get(cid)
    if not proc:
        raise HTTPException(404, "Turtle not running")

    await stop_turtle_session(cid)
    return {"status": "killed", "conversation_id": cid}