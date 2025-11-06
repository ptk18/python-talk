from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import requests
from requests.auth import HTTPBasicAuth
import subprocess
import json
import os
from pprint import pprint
from tempfile import NamedTemporaryFile
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/basic_client", response_class=HTMLResponse)
async def basic_client():
    with open("basic_client.html", "r") as f:
        html_content = f.read()
    return html_content
   

@app.get("/")
def read_root():
    return {"Hello": "World"}
    
import asyncio
import websockets
import cv2
import mss
import numpy as np
import base64

async def stream_screen(region, turtle_process, server_url):
    async with websockets.connect(server_url) as websocket:
        with mss.mss() as sct:
            while True:
                # Check if the Turtle subprocess is still running
                if turtle_process.poll() is not None:  # If not None, it's finished
                    print("Turtle graphics has finished.")
                    break  # Exit the streaming loop
                
                screenshot = np.array(sct.grab(region))
                frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
                _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
                jpg_as_text = base64.b64encode(buffer).decode('utf-8')
                
                await websocket.send(jpg_as_text)
                await asyncio.sleep(0.03)  # ~30 fps

from pydantic import BaseModel

class TurtleCodeRequest(BaseModel):
    files: dict[str, str]  # filename -> file content

@app.post("/run_turtle/{question_id}")
async def run_turtle(question_id: int, request: TurtleCodeRequest):
    # Get stream server URL from environment or use default
    STREAM_HOST = os.getenv('STREAM_HOST', 'localhost')
    STREAM_PORT = os.getenv('STREAM_PORT', '5050')
    SERVER_URL = f"ws://{STREAM_HOST}:{STREAM_PORT}/publish/{question_id}"

    # Streaming capture region - positioned to capture turtle window
    x1 = 50
    y1 = 50
    width = 800
    height = 800
    region = (x1, y1, width, height)

    # Create a temporary directory for this session
    temp_dir = f"turtle_session_{question_id}"
    os.makedirs(temp_dir, exist_ok=True)

    # Write all received files to the temporary directory
    temp_files = []
    for filename, content in request.files.items():
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        temp_files.append(file_path)

    try:
        # Start the Turtle graphics with runner.py from the temp directory
        runner_path = os.path.join(temp_dir, "runner.py")
        if not os.path.exists(runner_path):
            raise HTTPException(status_code=400, detail="runner.py not found in files")

        turtle_process = subprocess.Popen(['python3', 'runner.py'], cwd=temp_dir)

        # Start streaming
        await stream_screen(region, turtle_process, SERVER_URL)

        # Wait for the process to finish
        turtle_process.wait()

        return {"result": "Done", "question_id": question_id}
    finally:
        # Clean up temp files and directory
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
