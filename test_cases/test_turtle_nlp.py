from pathlib import Path
import json

from app.parser_engine.api import compile_single

MODULE_PATH = "backend/app/domains/turtle_app.py"  
# change this path to your real turtle_app.py path

tests = [
    ("write hello as text", "write(text='hello')"),
    ("write hi top as text", "write(text='hi top')"),
    ("set background color to salmon", "bgcolor(color_name='salmon')"),
    ("set pen color to red", "pencolor(color_name='red')"),
    ("set fill color to blue", "fillcolor(color_name='blue')"),
    ("draw circle 50", "circle(radius=50)"),
]

passed = 0
failed = 0

for sentence, expected in tests:
    result = compile_single(sentence, MODULE_PATH)
    actual = result.get("executable")

    ok = actual == expected
    print("=" * 60)
    print("INPUT   :", sentence)
    print("EXPECTED:", expected)
    print("ACTUAL  :", actual)
    print("STATUS  :", "PASS" if ok else "FAIL")
    print("FULL    :", json.dumps(result, indent=2, ensure_ascii=False))

    if ok:
        passed += 1
    else:
        failed += 1

print("\nSUMMARY")
print("PASS:", passed)
print("FAIL:", failed)