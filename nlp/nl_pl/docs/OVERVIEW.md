# NL_PL System Overview

## Summary
Fully dynamic natural language to Python code system using semantic parsing, AST analysis, and Pydantic models. Zero hardcoded patterns - all linguistic knowledge discovered from source code.

## System Architecture

```
User Input → Syntactic Parse → Semantic Analysis → Method Resolution → Code Execution
              (spaCy)           (Dynamic Config)     (AST-based)        (Pydantic)
```

## Core Components

### 1. Syntactic Parsing (`parsers/syntactic_parser.py`)
- spaCy-based dependency parsing
- Extracts tokens, POS tags, dependencies
- Handles compound sentences with conjunctions

### 2. Semantic Analysis (`parsers/semantic_analyzer.py`)
- Builds parse trees from syntactic tokens
- Extracts semantic frames (AGENT, PATIENT, etc.)
- Resolves circular references in dependency trees
- Pydantic models: `SyntacticParse`, `ParseNode`, `SemanticFrame`

### 3. Dynamic Configuration (`dynamic_config.py`)
- AST-based discovery of action/query indicators
- Extracts noise words from context
- Zero hardcoded linguistic patterns
- Learns from method names and docstrings

### 4. Method Resolution (`results_binding/resolver.py`)
- TF-IDF-based method matching via `RetrievalIndex`
- Confidence scoring for ambiguity resolution
- Dynamic parameter binding
- Uses config-provided indicators only

### 5. Interface (`interface.py`)
- Orchestrates all components
- Exports structured JSON analysis
- Validates with Pydantic schemas

## Example Flow

```
Input: "turn on the lights and turn off the tv"

1. Syntactic Parse (spaCy)
   → Tokens: [turn, on, the, lights, and, turn, off, the, tv]
   → Dependencies: ROOT→conj→obj, etc.

2. Semantic Analysis
   → Parse tree built with cycle detection
   → Frames: [ACTION(turn on, lights), ACTION(turn off, tv)]

3. Dynamic Config
   → Discovers: action_indicators=['turn', 'set', 'switch', ...]
   → From AST: SmartHome methods analyzed

4. Method Resolution
   → Matches: SmartHome.turn_on_light(), SmartHome.turn_off_tv()
   → TF-IDF scoring with confidence thresholds

5. Execution
   → Calls resolved methods with bound parameters
```

## Key Features

### Fully Dynamic
- No hardcoded word lists
- All patterns extracted from AST
- Works with any Python class
- Adapts to new domains automatically

### Robust Parsing
- Handles compound sentences
- Cycle detection prevents recursion errors
- Semantic frame extraction
- Dependency tree analysis

### Confidence-Based Resolution
- TF-IDF scoring for method matching
- Ambiguity resolution with intent analysis
- Fallback strategies for low-confidence matches

## File Structure

```
nlp/nl_pl/
├── interface.py                    # Main orchestrator
├── dynamic_config.py               # AST-based config discovery
├── parsers/
│   ├── syntactic_parser.py         # spaCy wrapper
│   ├── semantic_analyzer.py        # Parse tree + frames
│   ├── semantic_parser.py          # High-level NL parsing
│   └── retrieval_index.py          # TF-IDF matching
├── results_binding/
│   └── resolver.py                 # Method resolution
└── output/                         # JSON exports
```

## Usage

```python
from nlp.nl_pl.interface import NaturalLanguageInterface

interface = NaturalLanguageInterface(
    python_file="source_kbs/smarthome.py",
    class_name="SmartHome"
)

result = interface.process("turn on the lights")
# Returns method + params + confidence
```
