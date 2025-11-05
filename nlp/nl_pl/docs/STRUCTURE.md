# NL_PL Module Structure

## Overview
Clean, modular architecture for parsing natural language to programming language constructs.

## 3-Part System

### 1. NL Text Parsing (parsers/)
Analyzes natural language text into semantic structures.

**Components:**
- `semantic_parser.py` - Extracts intent, action verbs, and parameters from NL text
- `surface_form_generator.py` - Generates human-readable phrases from method names
- `retrieval_index.py` - TF-IDF based matching between NL queries and methods

**Output Structure:**
```python
ParsedIntent(
    target_class="BankAccount",          # Target class
    action_verb="deposit",               # Extracted action
    intent_type="action",                # "action" or "query"
    slots={"amount": 200},              # Extracted parameters
    raw_text="deposit 200"              # Original text
)
```

**Semantic Parsing Format:** `obj.action(attributes)`
Example: `BankAccount.deposit(amount=200)`

### 2. AST Parsing (ast_analyzer/)
Analyzes Python source code to extract class structures.

**Components:**
- `catalog.py` - Data structures for storing class/method information
- `catalog_builder.py` - Parses Python files to extract:
  - Classes
  - Methods
  - Parameters with types
  - Required vs optional parameters
  - Docstrings
  - Query vs action methods

**Output Structure:**
```python
MethodInfo(
    name="deposit",
    class_name="BankAccount",
    params={"amount": Any},
    required_params=["amount"],
    docstring="Deposit money into the account",
    is_query=False,
    surface_forms={"deposit", "add money", "put money in", ...}
)
```

### 3. Result Processing (results/)
Resolves parsed intents to actual methods and exports analysis.

**Components:**
- `resolver.py` - Matches parsed intent to actual methods with confidence scoring
- `json_exporter.py` - Exports step-by-step analysis to JSON files

**Output Structure:**
```python
(
    method_name="deposit",
    params={"amount": 200},
    metadata={
        "confidence": 95.0,
        "matched_phrase": "deposit",
        "matched_method": "BankAccount.deposit"
    }
)
```

## JSON Output Files

### 1. AST Analysis (ast_analysis_*.json)
Complete analysis of source code structure.

```json
{
  "timestamp": "2025-10-07T18:50:31.173290",
  "class_name": "BankAccount",
  "methods": [
    {
      "name": "deposit",
      "parameters": {"amount": "Any"},
      "required_parameters": ["amount"],
      "docstring": "Deposit money into the account",
      "is_query": false,
      "surface_forms": ["deposit", "deposit money", ...]
    }
  ]
}
```

### 2. Full Analysis (full_analysis_*.json)
Step-by-step analysis of NL input processing.

```json
{
  "timestamp": "2025-10-07T18:50:31.174731",
  "input": {
    "raw_text": "deposit 200"
  },
  "step1_semantic_parsing": {
    "target_class": null,
    "action_verb": "deposit",
    "intent_type": "action",
    "extracted_slots": {"amount": 200}
  },
  "step2_method_resolution": {
    "matched_method": "BankAccount.deposit",
    "confidence": 95.0,
    "matched_phrase": "deposit",
    "alternatives": []
  },
  "step3_parameter_binding": {
    "parameters": {"amount": 200}
  }
}
```

## Usage Example

```python
from nl_pl.interface import NaturalLanguageInterface

interface = NaturalLanguageInterface(
    python_file="bankaccount.py",
    class_name="BankAccount",
    output_dir="nl_pl/output"
)

interface.export_ast_analysis()

method_name, params, result = interface.process("deposit 200", export_json=True)

print(f"Parsed Structure: {result['semantic_parsing']['parsed_structure']}")

instance = interface.get_class_instance("User", 1000)
method = getattr(instance, method_name)
execution_result = method(**params)
```

## Pipeline Flow

```
Input: "deposit 200"
    ↓
[1. Semantic Parser]
    ↓
ParsedIntent(action="deposit", slots={"amount": 200})
Formatted: BankAccount.deposit(amount=200)
    ↓
[2. AST Analyzer] + [Retrieval Index]
    ↓
Matched: BankAccount.deposit (confidence: 95.0)
    ↓
[3. Resolver]
    ↓
Output: method="deposit", params={"amount": 200}
    ↓
[4. JSON Exporter]
    ↓
Saved: full_analysis_20251007_185031.json
```

## Directory Layout

```
nl_pl/
├── __init__.py
├── interface.py                # Main interface
├── demo.py                     # Usage example
│
├── parsers/                    # Part 1: NL Parsing
│   ├── __init__.py
│   ├── semantic_parser.py      # NL → ParsedIntent
│   ├── surface_form_generator.py  # Method → Human phrases
│   └── retrieval_index.py      # Query → Method matching
│
├── ast_analyzer/               # Part 2: AST Analysis
│   ├── __init__.py
│   ├── catalog.py              # Data structures
│   └── catalog_builder.py      # Python file → DomainCatalog
│
├── results/                    # Part 3: Results
│   ├── __init__.py
│   ├── resolver.py             # Intent → Method + Params
│   └── json_exporter.py        # Analysis → JSON files
│
└── output/                     # Generated JSON files
    ├── ast_analysis_*.json
    └── full_analysis_*.json
```

## Key Features

1. **Clean Separation**: Each part (NL parsing, AST analysis, results) is independent
2. **No Prints/Emojis**: Clean output, analysis stored in JSON
3. **Structured Format**: All NL parsing shows `obj.action(attributes)` format
4. **Step-by-Step Analysis**: JSON files show complete processing pipeline
5. **Easy to Debug**: Each component can be tested independently
6. **Explainable**: Clear metadata showing confidence scores and alternatives
