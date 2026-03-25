## Test 1 - Direct Match

```
curl -s -X POST "http://127.0.0.1:8000/api/analyze_command" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": 1, "command": "turn on tv"}' | python3 -m json.tool
```

## Test 2 - Follow-up

```
curl -s -X POST "http://127.0.0.1:8000/api/analyze_command" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": 1, "command": "turn on"}' | python3 -m json.tool

curl -s -X POST "http://127.0.0.1:8000/api/analyze_command" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": 1, "command": "light"}' | python3 -m json.tool

```

## Test 3 - Multiple

```
curl -s -X POST "http://127.0.0.1:8000/api/analyze_command" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": 1, "command": "turn on tv then turn on light"}' | python3 -m json.tool
```

## Test 4 - Noise

```
curl -s -X POST "http://127.0.0.1:8000/api/analyze_command" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": 1, "command": "asdfghj"}' | python3 -m json.tool
```



Docstring → Phrase Match → Action → Arg Bind → Executable → Runner → State.

The domain file acts as a semantic contract

Methods declare their natural-language interface inside docstrings

The system builds a phrase index

Longest phrase wins (deterministic)

Arguments are bound by rule-based heuristics

Object state is managed explicitly (no auto-instantiation)




## Test

create turtle call t1
draw circle
50


create accountant for Suriya call it acc1
spend 1200 rent
add note lunch with friend
set monthly limit rent 10000

set budget 3000
food

create robot named Atlas call it r1
say hello
walk 10
turn left
jump 5
charge 20
battery status
rename to Neo
shutdown

try this:-
"draw circle radius 9+2"


create turtle call t1
draw circle 50
turn left 90


create a bank account named acc1
top
1000







## How turtle Works

How your 6 steps map to this design
Step 1

When app starts:

backend calls /start_turtle/{cid}

Pi starts runtime

Pi sends startup stream burst for 3 seconds

then stops sending

frontend keeps last frame

Step 2

When new generated code appears:

backend extracts only:

not comment

only last executable line

sends it to /turtle_command/{cid}

Step 3

When executable line is sent:

same turtle process runs it

same screen, same location

Pi starts 3-second burst stream again

Step 4

After burst ends:

frontend keeps last frame

runtime stays alive

wait for next command

Step 5

On refresh:

frontend reconnects websocket

backend calls /start_turtle/{cid}

Pi sees same cid already running

does not restart turtle

just sends 3-second burst again

Step 6

On new app / open another app:

Pi checks CURRENT_CID

if another app is running, kill it first

then start new one

if existing app needs full replay, backend must rebuild the runner and replay all lines into the new runtime












## How files in PI5 works -

running: stream_server.py
running: api_server.py
auto-spawned by API: turtle_runtime.py
not used: turtle_run.py

stream_server.py runs the WSS relay server on port 5050.
frontend connects to stream_server.py at /subscribe/{cid} to receive frames.
api_server.py runs the Pi HTTP API on port 8001.
backend calls api_server.py at /start_turtle/{cid}.
api_server.py starts turtle_runtime.py if that cid is not already running.
turtle_runtime.py opens the turtle window and keeps one persistent Python process alive.
api_server.py stores that runtime process in memory by cid.
backend reads runner.py from your backend session storage.
backend decides whether to send only latest line or replay all lines.
backend calls api_server.py at /turtle_command/{cid} with one command at a time.
api_server.py writes that command into turtle_runtime.py stdin.
turtle_runtime.py executes the line in the same existing turtle state.
after start or command, api_server.py starts a 3-second screen-capture burst.
during burst, api_server.py captures the Pi screen and publishes frames to stream_server.py at /publish/{cid}.
stream_server.py forwards those frames to all frontend subscribers for that same cid.
frontend shows the latest received frame and keeps it after burst ends.
if same cid starts again, api_server.py reuses existing turtle_runtime.py.
if a different cid starts, api_server.py kills the old runtime first, then starts a new one.




## How everything run for turlte

TurtlePlayground.vue gets the speech result text.
handleMicClick() puts transcript into commandText.
handleRunCommand() starts processing that text.
processCommand(...) turns speech text into executable turtle code.
appendToCodeEditor(...) adds that code into runner.py content in frontend.
saveAppData(...) sends updated runner code to backend /api/save_runner_code.
startRemoteTurtleSession(appId) calls backend /api/run_turtle/{cid}.
backend turtle_execute.py handles /api/run_turtle/{cid}.
turtle_execute.py calls Pi api_server.py at /start_turtle/{cid}.
turtle_execute.py gets full runner code from backend /api/get_runner_code.
turtle_execute.py extracts latest line or all lines.
turtle_execute.py calls Pi api_server.py at /turtle_command/{cid}.
Pi api_server.py sends that line into turtle_runtime.py.
turtle_runtime.py executes the turtle command.
Pi api_server.py starts screen burst capture.
Pi api_server.py publishes frames to stream_server.py.
frontend websocket subscriber receives frames from stream_server.py.
streamFrame updates and the image shows on screen.