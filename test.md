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