# test_runner.py
# ============================================================
# Test runner so you don't have to edit main_process.py
#
# Usage:
#   python test_runner.py parser/code/robot.py
#   python test_runner.py parser/code/smarthome.py
#   python test_runner.py parser/code/bank_account.py
# ============================================================

import sys
import json
from pathlib import Path

from lex_alz import setup_nltk
from main_process import run


# Map file name -> sentences to test
TESTS = {
    # "robot.py": [
    #     "Move 3 steps slowly",
    #     "Take 3 steps slowly",
    #     "walk 3 steps",
    #     "say hello",
    #     "say bingo",
    #     "quickly walk 2 steps",
    #     "walk 4 steps in the kitchen",
    # ],
    # "smarthome.py": [
    #     "turn on the light",
    #     "switch off the tv",
    #     "power on television",
    #     "increase temperature by 2",
    #     "make it warmer by 3 degrees",
    #     "decrease temperature 1",
    # ],
    "bank_account.py": [
        "deposit 500",
        "add money 200",
        "withdraw 50",
        "send 100 to bob",
        "transfer 300 to alice",
        "get balance",
        "show transactions limit 3",
    ],
}


def main():
    setup_nltk()

    py_file = "parser/code/bank_account.py"
    fname = "bank_account.py"

    if fname not in TESTS:
        print(f"No tests registered for {fname}. Add it to TESTS in test_runner.py")
        sys.exit(1)

    for s in TESTS[fname]:
        print(json.dumps(run(s, py_file), indent=2))
        print("-" * 60)


if __name__ == "__main__":
    main()
