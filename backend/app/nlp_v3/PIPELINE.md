# NLP v3 Pipeline

## Processing Flow

```
Command: "move forward 50 steps"
         │
         ▼
┌─────────────────────────────────────────────┐
│ 1. PREPROCESSING (optional)                 │
│    TurtlePreprocessor: removes filler words │
│    → "forward 50"                           │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 2. DEPENDENCY PARSING                       │
│    spaCy extracts: verb, objects, params    │
│    → verb="forward", objects=[], params=[50]│
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 3. SCORING (for each method)                │
│    Direct match   50%  │ verb == method     │
│    Synonym match  25%  │ synonyms overlap   │
│    Entity match   15%  │ objects in method  │
│    Semantic       10%  │ embedding fallback │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 4. OUTPUT                                   │
│    method="forward", params={distance: 50}  │
│    confidence=0.95                          │
└─────────────────────────────────────────────┘
```

---

## Dynamic Synonym Generation

On conversation load, synonyms are dynamically generated for unknown verbs:

```
Load conversation with user code
         │
         ▼
┌─────────────────────────────────────────────┐
│ 1. Extract methods from Python file         │
│    → ["calculate_tax", "send_email", ...]   │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 2. Find unknown verbs (not in JSON)         │
│    → ["calculate", "send"]                  │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 3. ONE batch LLM call (Haiku ~$0.001)       │
│    → {"calculate": ["compute", "eval"...],  │
│        "send": ["transmit", "dispatch"...]} │
└─────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ 4. Persist to synonyms_base.json            │
│    → Next time: instant, no LLM call        │
└─────────────────────────────────────────────┘
```

**Cost**: ~$0.001 once per unique method set, then free forever.

**Model**: Uses `claude-3-haiku-20240307` for synonym generation.

---

## Components

| File | Purpose |
|------|---------|
| `service.py` | `NLPService` - main facade combining extractor + pipeline |
| `main.py` | `NLPPipeline` - orchestrates parsing and scoring |
| `dependency_parser.py` | Extracts verbs/objects using spaCy (EN) or pythainlp (TH) |
| `semantic_matcher.py` | Embedding similarity using sentence-transformers |
| `synonym_generator.py` | Static base + dynamic LLM synonym generation |
| `synonyms_base.json` | Cached synonyms (grows dynamically) |
| `entity_normalizer.py` | Maps entity variations to canonical names (requires LLM) |

### Extractors (`extractors/`)

| Extractor | Use Case |
|-----------|----------|
| `ASTExtractor` | User-uploaded Python code (Codespace) |
| `TurtleExtractor` | Python turtle module methods |
| `ModuleExtractor` | Any Python module |

### Preprocessors (`preprocessors/`)

| Preprocessor | Use Case |
|--------------|----------|
| `DefaultPreprocessor` | No-op (Codespace) |
| `TurtlePreprocessor` | Removes filler words for turtle commands |

---

## Scoring Formula

```python
total = (
    direct_match * 0.50 +    # verb matches method name
    synonym_match * 0.25 +   # synonym tokens overlap
    entity_match * 0.15 +    # objects in method name
    semantic * 0.10          # embedding similarity
)
if params_extracted:
    total += 0.05            # bonus for parameter extraction
```

**Note**: Numeric parameters are extracted using the `word2number` library (e.g., "fifty" → 50).

---

## Usage

### Codespace (user code)
```python
from app.nlp_v3 import NLPService, ASTExtractor

service = NLPService(extractor=ASTExtractor())
service.initialize(user_code_string)
results = service.process("add 2 and 3")
```

### Turtle
```python
from app.nlp_v3 import NLPService, TurtleExtractor, TurtlePreprocessor

service = NLPService(
    extractor=TurtleExtractor(),
    preprocessor=TurtlePreprocessor()
)
service.initialize(None)
results = service.process("move forward 50 steps")
```

