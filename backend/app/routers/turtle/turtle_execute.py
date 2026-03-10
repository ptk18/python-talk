# app/routers/turtle_execute.py
import os
import re
from fastapi import APIRouter, HTTPException
import httpx

from pathlib import Path

router = APIRouter(tags=["Turtle Execute"])

# Streaming device configuration
STREAM_DEVICE_IP = "192.168.4.228"
STREAM_DEVICE_PORT = "8001"

# API base URL for internal calls
CODE_API_BASE = os.getenv("CODE_API_BASE", "http://localhost:8000/api")


BASE_EXEC_DIR = Path(__file__).resolve().parents[2] / "executions"
BASE_EXEC_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/run_turtle/{conversation_id}")
async def run_turtle(conversation_id: int):
    try:
        start_url = f"http://{STREAM_DEVICE_IP}:{STREAM_DEVICE_PORT}/start_turtle/{conversation_id}"
        command_url = f"http://{STREAM_DEVICE_IP}:{STREAM_DEVICE_PORT}/turtle_command/{conversation_id}"
        get_runner_url = f"{CODE_API_BASE}/get_runner_code"

        async with httpx.AsyncClient(timeout=30.0) as client:
            start_resp = await client.post(start_url)
            if start_resp.status_code != 200:
                raise HTTPException(
                    status_code=start_resp.status_code,
                    detail=f"Failed to start turtle session: {start_resp.text}",
                )

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
            if not runner_code:
                raise HTTPException(
                    status_code=400,
                    detail="get_runner_code response missing 'code'",
                )

            command = extract_latest_runner_line(runner_code)
            if not command:
                raise HTTPException(
                    status_code=400,
                    detail="Could not extract latest executable runner line",
                )

            print(f"[BACKEND] latest command for cid={conversation_id}: {command}", flush=True)

            send_resp = await client.post(
                command_url,
                params={"command": command},
            )
            if send_resp.status_code != 200:
                raise HTTPException(
                    status_code=send_resp.status_code,
                    detail=f"Pi turtle command failed: {send_resp.text}",
                )

            return {
                "result": "Incremental turtle command sent",
                "conversation_id": conversation_id,
                "command": command,
                "device_response": send_resp.json(),
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
            detail=f"Failed to trigger turtle graphics incrementally: {str(e)}",
        )


def extract_latest_runner_line(code: str) -> str | None:
    """
    Return the last meaningful executable line from runner.py.

    Rules:
    - ignore empty lines
    - ignore comments
    - ignore import lines
    - ignore common keep-alive lines like time.sleep(...)
    - ignore turtle.mainloop()/done()/exitonclick()
    """
    if not code:
        return None

    lines = code.splitlines()

    ignored_prefixes = (
        "import ",
        "from ",
        "#",
    )

    ignored_exact_contains = (
        "time.sleep(",
        "turtle.done(",
        "t.done(",
        "done(",
        "exitonclick(",
        "mainloop(",
    )

    candidates: list[str] = []

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith(ignored_prefixes):
            continue
        if any(x in line for x in ignored_exact_contains):
            continue
        candidates.append(line)

    if not candidates:
        return None

    return candidates[-1]


@router.get("/get_latest_runner_line")
async def get_latest_runner_line(conversation_id: int):
    """
    Fetch full runner.py using existing get_runner_code endpoint,
    then return only the latest executable line for incremental turtle execution.
    """
    try:
        get_runner_url = f"{CODE_API_BASE}/get_runner_code"

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                get_runner_url,
                params={"conversation_id": conversation_id},
            )

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

        latest_line = extract_latest_runner_line(runner_code)
        if not latest_line:
            raise HTTPException(
                status_code=400,
                detail="Could not extract a latest executable runner line",
            )

        return {
            "conversation_id": conversation_id,
            "command": latest_line,
        }

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not fetch runner code: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract latest runner line: {str(e)}",
        )