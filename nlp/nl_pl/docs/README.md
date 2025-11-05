# NL-PL: Natural Language to Programming Language Interface

Clean, modular architecture for semantic parsing and method resolution.

## Directory Structure

```
nl-pl/
├── parsers/                    # NL text parsing (semantic parsing)
│   ├── semantic_parser.py      # Parses NL into intent structure
│   ├── surface_form_generator.py  # Generates method surface forms
│   └── retrieval_index.py      # TF-IDF based method matching
│
├── ast_analyzer/               # AST parsing for source code
│   ├── catalog.py              # Domain catalog data structures
│   └── catalog_builder.py      # Extracts classes/methods/params from Python files
│
├── results/                    # Result processing
│   ├── resolver.py             # Resolves intent to method + params
│   └── json_exporter.py        # Exports analysis to structured JSON
│
├── output/                     # JSON output files
│
├── interface.py                # Main interface
└── demo.py                     # Example usage

```

## Pipeline

1. **NL Parsing** (parsers/)
   - Input: Natural language text
   - Output: ParsedIntent with structure `obj.action(attributes)`
   - Components: semantic_parser, surface_form_generator, retrieval_index

2. **AST Analysis** (ast_analyzer/)
   - Input: Python source file
   - Output: DomainCatalog with classes, methods, parameters, types
   - Components: catalog, catalog_builder

3. **Resolution** (results/)
   - Input: ParsedIntent + DomainCatalog
   - Output: Matched method + validated parameters + metadata
   - Components: resolver, json_exporter

## Usage

```python
from nl_pl.interface import NaturalLanguageInterface

interface = NaturalLanguageInterface(
    python_file="bankaccount.py",
    class_name="BankAccount",
    output_dir="nl-pl/output"
)

interface.export_ast_analysis()

method_name, params, result = interface.process("deposit 200", export_json=True)

instance = interface.get_class_instance("User", 1000)
method = getattr(instance, method_name)
execution_result = method(**params)
```

## Output Structure

### Semantic Parsing Output
```json
{
  "parsed_structure": "BankAccount.deposit(amount=200)",
  "target_class": "BankAccount",
  "action_verb": "deposit",
  "intent_type": "action",
  "extracted_slots": {"amount": 200}
}
```

### AST Analysis Output
```json
{
  "class_name": "BankAccount",
  "methods": [
    {
      "name": "deposit",
      "parameters": {"amount": "float"},
      "required_parameters": ["amount"],
      "docstring": "Deposit money into account",
      "is_query": false,
      "surface_forms": ["deposit", "add money", "put money", ...]
    }
  ]
}
```

### Resolution Output
```json
{
  "matched_method": "BankAccount.deposit",
  "parameters": {"amount": 200},
  "metadata": {
    "confidence": 95.0,
    "matched_phrase": "deposit",
    "alternatives": []
  }
}
```
