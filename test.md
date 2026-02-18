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
