import re
from typing import List, Dict, Any, Optional
from .models import MethodInfo, MatchResult
from .stage_1_tokenize import analyze_sentence
from .stage_2_grammar import extract_grammar
from .stage_3_match import find_best_match
from .turtle_methods import get_turtle_methods

LOG_PREFIX = "[NLP]"


class DictionaryNLPService:

    def __init__(self):
        self._methods: List[MethodInfo] = []
        self._initialized = False

    def initialize_turtle(self) -> List[MethodInfo]:
        print(f"{LOG_PREFIX} Initializing turtle methods via introspection...")
        self._methods = get_turtle_methods()
        self._initialized = True
        print(f"{LOG_PREFIX} Loaded {len(self._methods)} methods from turtle.Turtle")
        return self._methods

    def preprocess(self, command: str) -> str:
        cmd = command.lower()
        cmd = re.sub(r"\bthe\s+turtle\b", "turtle", cmd)
        cmd = re.sub(r"\bthe\s+pen\b", "pen", cmd)
        cmd = re.sub(r"\bplease\b", "", cmd)
        cmd = re.sub(r"\bcan\s+you\b", "", cmd)
        cmd = re.sub(r"\bsteps?\b", "", cmd)
        cmd = re.sub(r"\bdegrees?\b", "", cmd)
        cmd = re.sub(r"\bunits?\b", "", cmd)
        cmd = re.sub(r"\bpixels?\b", "", cmd)
        # Remove filler/connector words that don't affect command semantics
        cmd = re.sub(r"\bagain\b", "", cmd)
        cmd = re.sub(r"\bthen\b", "", cmd)
        cmd = re.sub(r"\bnow\b", "", cmd)
        cmd = re.sub(r"\bjust\b", "", cmd)
        cmd = re.sub(r"[.,!?;:]+", " ", cmd)
        cmd = " ".join(cmd.split())
        return cmd

    def process(self, command: str, top_k: int = 1) -> List[Dict[str, Any]]:
        if not self._initialized:
            return [{"success": False, "error": "Service not initialized"}]

        preprocessed = self.preprocess(command)
        print(f"{LOG_PREFIX} Preprocessed: '{preprocessed}'")

        words = analyze_sentence(preprocessed)
        print(f"{LOG_PREFIX} POS tags: {[(w.original, w.pos) for w in words]}")

        grammar = extract_grammar(words)
        print(f"{LOG_PREFIX} Grammar: verb='{grammar.verb}' obj='{grammar.object}' particle='{grammar.particle}' nums={grammar.numbers}")

        result = find_best_match(grammar, self._methods)

        return [{
            "success": result.success,
            "method": result.method,
            "confidence": result.confidence,
            "parameters": result.params,
            "executable": result.executable,
            "error": result.error
        }]
