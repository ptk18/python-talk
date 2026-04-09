# app/routers/turtle/turtle_execute.py
# not used whole file
import os
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["Turtle Execute"])

STREAM_DEVICE_IP = "192.168.4.228"
STREAM_DEVICE_PORT = "8001"
STREAM_DEVICE_BASE_URL = "https://192.168.4.228:8001"
CODE_API_BASE = os.getenv("CODE_API_BASE", "http://localhost:8000/api")

BASE_EXEC_DIR = Path(__file__).resolve().parents[2] / "executions"
BASE_EXEC_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/run_turtle/{conversation_id}")
async def run_turtle(conversation_id: int):
    """
    Flow:
    1) Ask Pi to start/reuse turtle runtime
    2) Read full runner.py
    3) If Pi started a NEW runtime -> replay all executable lines
    4) If Pi reused existing runtime -> send only latest executable line
    """
    try:
        start_url = f"{STREAM_DEVICE_BASE_URL}/start_turtle/{conversation_id}"
        command_url = f"{STREAM_DEVICE_BASE_URL}/turtle_command/{conversation_id}"
        get_runner_url = f"{CODE_API_BASE}/get_runner_code"

        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            # 1) start or reuse runtime
            start_resp = await client.post(start_url)
            if start_resp.status_code != 200:
                raise HTTPException(
                    status_code=start_resp.status_code,
                    detail=f"Failed to start turtle session: {start_resp.text}",
                )

            start_data = start_resp.json()
            start_status = start_data.get("status")  # expected: "started" or "already_running"

            # 2) load runner.py
            runner_resp = await client.get(
                get_runner_url,
                params={"conversation_id": conversation_id},
            )
            if runner_resp.status_code != 200:
                raise HTTPException(
                    status_code=runner_resp.status_code,
                    detail=f"Failed to fetch runner code: {runner_resp.text}",
                )

            runner_data = runner_resp.json()
            runner_code = runner_data.get("code")
            if runner_code is None:
                raise HTTPException(
                    status_code=400,
                    detail="get_runner_code response missing 'code'",
                )

            # 3) decide mode
            if start_status == "started":
                commands = extract_all_executable_lines(runner_code)
                mode = "replay"
            else:
                latest = extract_latest_runner_line(runner_code)
                commands = [latest] if latest else []
                mode = "latest_line"

            if not commands:
                return {
                    "result": "No executable turtle commands found",
                    "conversation_id": conversation_id,
                    "mode": mode,
                    "commands_sent": 0,
                    "commands": [],
                    "start_status": start_status,
                }

            # 4) send to Pi
            sent = []
            for cmd in commands:
                send_resp = await client.post(
                    command_url,
                    params={"command": cmd},
                )
                if send_resp.status_code != 200:
                    raise HTTPException(
                        status_code=send_resp.status_code,
                        detail=f"Pi turtle command failed for '{cmd}': {send_resp.text}",
                    )
                sent.append(cmd)

            return {
                "result": "Turtle command flow complete",
                "conversation_id": conversation_id,
                "mode": mode,
                "commands_sent": len(sent),
                "commands": sent,
                "start_status": start_status,
                "latest_command": sent[-1] if sent else None,
            }

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to streaming device at {STREAM_DEVICE_IP}:{STREAM_DEVICE_PORT}. Error: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger turtle graphics: {str(e)}",
        )


def should_ignore_runner_line(line: str) -> bool:
    if not line:
        return True

    stripped = line.strip()
    if not stripped:
        return True

    if stripped.startswith("#"):
        return True

    if stripped.startswith("import ") or stripped.startswith("from "):
        return True

    ignored_contains = (
        "time.sleep(",
        "turtle.done(",
        "t.done(",
        "done(",
        "exitonclick(",
        "mainloop(",
    )
    if any(x in stripped for x in ignored_contains):
        return True

    return False


def extract_all_executable_lines(code: str) -> list[str]:
    if not code:
        return []

    commands = []
    for raw in code.splitlines():
        line = raw.strip()
        if should_ignore_runner_line(line):
            continue
        commands.append(line)

    return commands


def extract_latest_runner_line(code: str) -> str | None:
    commands = extract_all_executable_lines(code)
    if not commands:
        return None
    return commands[-1]


@router.get("/refresh_turtle/{conversation_id}")
async def refresh_turtle(conversation_id: int):
    try:
        start_url = f"{STREAM_DEVICE_BASE_URL}/start_turtle/{conversation_id}"

        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            start_resp = await client.post(start_url)

        if start_resp.status_code != 200:
            raise HTTPException(
                status_code=start_resp.status_code,
                detail=f"Failed to refresh turtle session: {start_resp.text}",
            )

        start_data = start_resp.json()

        return {
            "result": "refresh stream triggered",
            "conversation_id": conversation_id,
            "start_status": start_data.get("status"),
        }

    except httpx.RequestError as e:
        print("REFRESH_TURTLE RequestError:", repr(e), flush=True)
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to Pi: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh turtle: {str(e)}",
        )