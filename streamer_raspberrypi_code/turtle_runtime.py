# code in pi5 : turtle_runtime.py
import sys
import turtle

screen = turtle.Screen()
screen.setup(width=800, height=800, startx=50, starty=50)
screen.screensize(700, 700)
screen.tracer(1, 20)

exec_globals = {
    "__name__": "__main__",
    "turtle": turtle,
    "screen": screen,
}

print("[RUNTIME] Ready", flush=True)

while True:
    try:
        raw = sys.stdin.readline()
        if raw == "":
            continue

        line = raw.strip()
        if not line:
            continue

        if line == "__EXIT__":
            print("[RUNTIME] Exiting", flush=True)
            break

        print(f"[RUNTIME] EXEC: {line}", flush=True)
        exec(line, exec_globals, exec_globals)
        screen.update()
        print("[RUNTIME] OK", flush=True)

    except Exception as e:
        print(f"[RUNTIME] ERROR: {e}", flush=True)