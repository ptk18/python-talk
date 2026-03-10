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