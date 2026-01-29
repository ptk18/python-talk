#!/usr/bin/env python3
"""
NLP v4 Test Script

Tests semantic matching with all-mpnet-base-v2 against real source_kbs classes.
Run from backend directory:
    python -m app.nlp_v4.test_v4
"""

import sys
import os

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.nlp_v4.service import NLPService
from app.nlp_v4.extractors import ASTExtractor


# ---------------------------------------------------------------------------
# Test data: (class_file, test_commands_with_expected_method)
# ---------------------------------------------------------------------------

SOURCE_KBS = os.path.join(os.path.dirname(__file__), "..", "..", "..", "source_kbs")

TEST_CASES = {
    "Calculator": {
        "file": os.path.join(SOURCE_KBS, "calculator.py"),
        "commands": [
            ("add 5 and 3", "add"),
            ("subtract 10 from 20", "subtract"),
            ("multiply 4 by 6", "multiply"),
            ("divide 10 by 2", "divide"),
            # Variations
            ("what is the sum of 2 and 3", "add"),
            ("take away 5 from 8", "subtract"),
            ("what is 5 times 3", "multiply"),
            ("split 20 into 4", "divide"),
            # Harder
            ("plus 7 and 2", "add"),
            ("minus 10 and 3", "subtract"),
        ],
    },
    "SmartHome": {
        "file": os.path.join(SOURCE_KBS, "smarthome.py"),
        "commands": [
            ("turn on the light", "turn_light_on"),
            ("turn off the light", "turn_light_off"),
            ("turn on the TV", "turn_tv_on"),
            ("turn off the TV", "turn_tv_off"),
            ("turn on the air conditioner", "turn_ac_on"),
            ("turn off the AC", "turn_ac_off"),
            ("increase the temperature by 5", "increase_temperature"),
            ("decrease the temperature", "decrease_temperature"),
            # Variations
            ("switch on the light", "turn_light_on"),
            ("shut off the television", "turn_tv_off"),
            ("make it warmer", "increase_temperature"),
            ("make it cooler", "decrease_temperature"),
            ("enable the AC", "turn_ac_on"),
        ],
    },
    "BankAccount": {
        "file": os.path.join(SOURCE_KBS, "bankaccount.py"),
        "commands": [
            ("deposit 500", "deposit"),
            ("withdraw 200", "withdraw"),
            ("check my balance", "get_balance"),
            ("who owns this account", "get_owner"),
            ("do I have enough money for 1000", "has_sufficient_funds"),
            ("is my balance low", "is_low_balance"),
            # Variations
            ("put money in", "deposit"),
            ("take out 50", "withdraw"),
            ("how much money do I have", "get_balance"),
            ("show account information", "get_account_info"),
            ("am I overdrawn", "is_overdrawn"),
        ],
    },
}


def run_test(class_name: str, test_data: dict) -> dict:
    """Run tests for a single class. Returns accuracy stats."""
    print(f"\n{'='*70}")
    print(f"  {class_name}")
    print(f"{'='*70}")

    # Read source file
    with open(test_data["file"], "r") as f:
        source_code = f.read()

    # Initialize service
    service = NLPService(extractor=ASTExtractor())
    methods = service.initialize(source_code)

    print(f"\nExtracted {len(methods)} methods:")
    for m in methods:
        print(f"  - {m.name}({', '.join(m.params)})")

    print(f"\n{'-'*70}")
    print(f"  Commands:")
    print(f"{'-'*70}")

    correct = 0
    total = len(test_data["commands"])

    for command, expected in test_data["commands"]:
        results = service.process(command, top_k=5)

        if results:
            top = results[0]
            match = top.method_name == expected
            if match:
                correct += 1
            symbol = "O" if match else "X"

            print(f"\n  {symbol} \"{command}\"")
            print(f"    Expected: {expected}")
            print(f"    Got:      {top.method_name} ({top.confidence:.1f}%)")

            # Show top 3
            for r in results[:3]:
                bar = "#" * int(r.confidence / 5)
                print(f"      {r.confidence:5.1f}% {bar} {r.method_name}")

            if top.parameters:
                print(f"    Params: {top.parameters}")
        else:
            print(f"\n  X \"{command}\"")
            print(f"    Expected: {expected}")
            print(f"    Got: NO MATCH")

    accuracy = correct / total * 100
    print(f"\n  Accuracy: {correct}/{total} ({accuracy:.0f}%)")

    return {"correct": correct, "total": total, "accuracy": accuracy}


def main():
    print("=" * 70)
    print("  NLP v4 - Semantic-First Pipeline Test")
    print("  Model: all-mpnet-base-v2 (no training)")
    print("=" * 70)

    all_correct = 0
    all_total = 0

    for class_name, test_data in TEST_CASES.items():
        stats = run_test(class_name, test_data)
        all_correct += stats["correct"]
        all_total += stats["total"]

    overall = all_correct / all_total * 100
    print(f"\n{'='*70}")
    print(f"  OVERALL: {all_correct}/{all_total} ({overall:.0f}%)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
