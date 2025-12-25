# Feeding Paraphrases into NLP Model

## Overview

This document explores integrating the "Other ways to say it" paraphrasing feature (used in the frontend Workspace) into the NLP v3 pipeline to improve command matching accuracy.

## Current Architecture

### Frontend Paraphrasing (`frontend/src/pages/Workspace.tsx`)
- **Location**: Lines 551-591, "Other ways to say it" button at line 772
- **How it works**:
  - User sends command → System interprets it
  - User clicks "Other ways to say it" → Calls `paraphraseAPI.getParaphrases()`
  - Claude Haiku generates grammatical variations (same words, different order)
  - Paraphrases displayed in UI
- **Current limitation**: Paraphrases are **stored only in frontend state**, not persisted or used for learning

### Backend Paraphrasing Service (`backend/app/routers/paraphrase.py`)
- **Standalone endpoint**: `/api/user_command_paraphrasing_suggestion`
- **LLM Model**: Claude 3 Haiku (fast, cheap)
- **Strategy**: Generates 3-6 grammatical variations by:
  - Rearranging word order ("turn on light" → "turn light on")
  - Adding/removing articles ("the", "a")
  - Keeping same numbers and entities
  - NO synonyms or creative rephrasing
- **Caching**: In-memory cache to avoid repeated API calls
- **Integration status**: **NOT connected to NLP pipeline**

### NLP v3 Pipeline (`backend/app/nlp_v3/`)

#### 1. Synonym Generation (`synonym_generator.py`)
- **Purpose**: Build synonym dictionary for better command matching
- **How it works**:
  ```python
  ClaudeSynonymGenerator.prewarm_cache(methods: List[MethodInfo])
  ```
  1. Extracts verbs, phrasal verbs, entities from method names
  2. Makes **ONE LLM call** to generate synonyms for all terms
  3. Stores in `self.cache` dictionary
  4. Only runs once per pipeline initialization

- **Example**:
  ```
  Methods: turn_on_light, turn_off_ac, set_temperature

  → Extracts:
    - verbs: ["turn", "set"]
    - phrasal_verbs: ["turn_on", "turn_off"]
    - entities: ["light", "ac", "temperature"]

  → LLM generates synonyms:
    - "turn": ["switch", "flip", "toggle"]
    - "turn_on": ["switch on", "activate", "power on"]
    - "light": ["lamp", "lights", "lighting"]

  → Stored in cache:
    cache["turn:"] = ["switch", "flip", "toggle"]
    cache["turn_on:"] = ["switch on", "activate", "power on"]
  ```

#### 2. Entity Normalization (`entity_normalizer.py`)
- **Purpose**: Map user terms to canonical method names
- **Depends on**: Synonym dictionary from `ClaudeSynonymGenerator`
- **Example**: "lamp" → "light", "aircon" → "ac"

#### 3. Main Pipeline (`main.py`)
- **Scoring system**: Matches commands to methods using:
  - Exact match (35%)
  - Synonym matching (22%)
  - Object/entity matching (18%)
  - Phrasal verb patterns (10%)
  - CodeBERT similarity (8%)
  - Semantic similarity (4%)
  - Parameter extraction (2%)
  - Fuzzy matching (1%)

## Can We Integrate Paraphrases to Teach the Model?

### ✅ What's Possible

#### 1. Use paraphrases as training data for synonym generation
- Feed paraphrases into `ClaudeSynonymGenerator.prewarm_cache()`
- Build richer synonym dictionaries from user patterns
- Improve verb/phrasal verb matching

#### 2. Enhance entity normalization
- Extract entity variations from paraphrases
- Build better `EntityNormalizer` mappings
- Example: User says "lamp" in paraphrases → learn "lamp" = "light"

#### 3. Augment the cache dynamically
- When user clicks "Other ways to say it", store successful patterns
- Update `ClaudeSynonymGenerator.cache` with user-validated variations
- Runtime learning from user behavior

### ⚠️ Limitations

#### 1. No persistent learning
- Current pipeline reinitializes on each session
- Paraphrases would need to be:
  - Stored in the database
  - Loaded during pipeline initialization
  - Persisted across conversations

#### 2. Paraphrases are grammatical, not semantic
- Current paraphrases (lines 40-44 in `paraphrase.py`) only rearrange words
- NLP model already handles:
  - Synonyms via LLM
  - Different word orders via dependency parsing
  - Entity normalization
- **Limited value** unless you expand paraphrasing to include semantic variations

#### 3. Pipeline is per-conversation isolated
- Each conversation has its own pipeline cache
- Paraphrases from one conversation won't help others
- Would need global pattern storage for cross-conversation learning

## How Would We Feed Paraphrases?

### Current Problem
`prewarm_cache()` only accepts `List[MethodInfo]` - it doesn't know about user commands or paraphrases.

```python
def prewarm_cache(self, methods: List[MethodInfo]):
    """Build synonym dictionary from methods using single LLM call"""
    if self.prewarmed or not self.available:
        return

    self.synonym_dict = self.build_method_synonym_dict(methods)
    self.prewarmed = True
```

### Solution A: Direct Cache Injection (Simpler)

Manually populate cache after paraphrases are generated:

```python
# After user generates paraphrases for "turn on the light"
paraphrases = ["turn the light on", "light on please", "switch on light"]

# Manually populate cache
for paraphrase in paraphrases:
    # Extract verb from paraphrase using dependency parser
    actions = pipeline.dependency_parser.extract_actions(paraphrase)

    for action_verb, objects, _, _ in actions:
        # Store as additional synonym
        cache_key = f"{action_verb}:"
        if cache_key not in pipeline.synonym_generator.cache:
            pipeline.synonym_generator.cache[cache_key] = []

        # Add the paraphrase pattern
        pipeline.synonym_generator.cache[cache_key].append(action_verb)
```

**What happens:**
- Cache now includes user-validated command patterns
- When processing future commands, pipeline has MORE patterns to match against
- Better matching for commands that match user's speech style

### Solution B: Extend `prewarm_cache()` (More Robust)

Modify the synonym generator to accept paraphrases:

```python
def build_method_synonym_dict(
    self,
    methods: List[MethodInfo],
    user_paraphrases: Dict[str, List[str]] = None  # NEW parameter
) -> Dict[str, List[str]]:
    """
    Build synonym dictionary from:
    1. Method names (structural patterns from code)
    2. User paraphrases (validated usage patterns from real users)
    """
    # Extract from methods (existing code)
    verbs = set()
    phrasal_verbs = set()
    entities = set()

    for method in methods:
        tokens = method.name.split('_')
        # ... existing extraction logic ...

    # NEW: Extract additional patterns from user paraphrases
    if user_paraphrases:
        for original_command, variants in user_paraphrases.items():
            for variant in variants:
                # Parse variant to extract verbs and entities
                doc = nlp(variant)  # Using spaCy

                # Extract verbs
                for token in doc:
                    if token.pos_ == "VERB":
                        verbs.add(token.lemma_)

                # Extract entities/nouns
                for chunk in doc.noun_chunks:
                    entities.add(chunk.text.lower())

    # Generate synonyms via LLM (existing code)
    # ...
```

## Implementation Roadmap

### Phase 1: Database Storage

Create a new table to persist paraphrases:

```python
# In backend/app/models/models.py

class CommandParaphrase(Base):
    __tablename__ = "command_paraphrases"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    original_command = Column(String, nullable=False)
    paraphrase_variants = Column(JSON, nullable=False)  # Store as JSON array
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="paraphrases")
```

### Phase 2: Save Paraphrases Endpoint

Add endpoint to save paraphrases when user generates them:

```python
# In backend/app/routers/paraphrase.py

@router.post("/save_paraphrases")
async def save_paraphrases(
    conversation_id: int,
    original: str,
    variants: List[str],
    db: Session = Depends(get_db)
):
    """
    Save user-generated paraphrases to database for future learning
    """
    paraphrase = CommandParaphrase(
        conversation_id=conversation_id,
        original_command=original,
        paraphrase_variants=variants
    )
    db.add(paraphrase)
    db.commit()

    # Optionally: Update pipeline cache in real-time
    cache_key = f"conv_{conversation_id}"
    if cache_key in _pipeline_cache:
        pipeline = _pipeline_cache[cache_key]
        # Inject paraphrases into cache
        enhance_pipeline_with_paraphrases(pipeline, original, variants)

    return {"status": "saved", "message": "Paraphrases stored successfully"}
```

### Phase 3: Load Paraphrases During Pipeline Initialization

Modify pipeline initialization to load historical paraphrases:

```python
# In backend/app/routers/analyze_command.py

@router.post("/prewarm_pipeline")
def prewarm_pipeline(payload: AnalyzeCommandRequest, db: Session = Depends(get_db)):
    conversation_id = payload.conversation_id

    # ... existing code to extract methods ...

    # NEW: Load user paraphrases from database
    paraphrases = db.query(CommandParaphrase)\
        .filter(CommandParaphrase.conversation_id == conversation_id)\
        .all()

    user_patterns = {
        p.original_command: p.paraphrase_variants
        for p in paraphrases
    }

    # Initialize pipeline with both methods and user patterns
    pipeline = NLPPipeline()
    pipeline.initialize(methods, user_paraphrases=user_patterns)
    _pipeline_cache[cache_key] = pipeline

    return {"status": "initialized", "patterns_loaded": len(user_patterns)}
```

### Phase 4: Update Frontend to Save Paraphrases

Modify Workspace.tsx to persist paraphrases:

```typescript
// In frontend/src/pages/Workspace.tsx

const handleToggleParaphrases = async (msg: Message) => {
    // ... existing code to fetch paraphrases ...

    if (msg.paraphrases && msg.paraphrases.length > 0) {
        // NEW: Save paraphrases to database
        try {
            await paraphraseAPI.saveParaphrases(
                parseInt(conversationId!),
                msg.content,
                msg.paraphrases
            );
            console.log("Paraphrases saved for future learning");
        } catch (error) {
            console.error("Failed to save paraphrases:", error);
        }
    }

    // ... rest of existing code ...
};
```

### Phase 5: Enhance Paraphrase Generation (Optional but Recommended)

Current paraphrases are too limited (word reordering only). Enhance to include:

```python
# In backend/app/routers/paraphrase.py

ENHANCED_PARAPHRASE_SYSTEM_PROMPT = """You generate paraphrases for user commands. Keep meaning identical.

Rules:
- Generate 3 types of variations:
  1. GRAMMATICAL: Rearrange word order (e.g., "turn on light" → "turn light on")
  2. SYNONYMS: Replace with common synonyms (e.g., "turn on" → "switch on", "activate")
  3. CASUAL: Natural speech patterns (e.g., "please turn on the light" → "light on")

- Keep the same numbers and entities exactly
- Keep the same intent and meaning
- Generate 5-8 variations total
- All variations MUST be grammatically correct
- Output ONLY valid JSON: {"variants":["...", "..."]}

Examples:
Input: "turn on the light"
Output: {"variants":[
    "turn the light on",           # grammatical
    "switch on the light",         # synonym
    "activate the light",          # synonym
    "light on please",             # casual
    "switch the light on"          # synonym + grammatical
]}
"""
```

## Recommended Strategy

### Start Small: Option 1 - Light Integration

Use paraphrases to augment synonym cache during runtime (no database changes):

**Pros:**
- Quick to implement
- No schema changes
- Immediate feedback loop

**Cons:**
- Learning not persisted
- Only helps current session

**Implementation:**
```python
# Add helper function in analyze_command.py

def enhance_pipeline_with_paraphrases(
    pipeline: NLPPipeline,
    original_command: str,
    paraphrases: List[str]
):
    """Add paraphrases to synonym cache for better matching"""
    for paraphrase in paraphrases:
        # Extract action verbs from paraphrase
        actions = pipeline.dependency_parser.extract_actions(paraphrase)

        for action_verb, _, _, _ in actions:
            # Store as synonym for original command's verb
            original_actions = pipeline.dependency_parser.extract_actions(original_command)

            if original_actions:
                original_verb = original_actions[0][0]
                cache_key = f"{original_verb}:"

                if cache_key in pipeline.synonym_generator.cache:
                    if action_verb not in pipeline.synonym_generator.cache[cache_key]:
                        pipeline.synonym_generator.cache[cache_key].append(action_verb)
```

### Scale Up: Option 2 - Full Integration

Database-backed learning system (follow Phase 1-5 above):

**Pros:**
- Persistent learning
- Cross-session improvements
- Analytics on user patterns

**Cons:**
- Requires database migration
- More complex implementation
- Need to handle cache invalidation

## Key Insight: Is It Worth It?

**Current paraphrasing limitations:**
- Only generates word reorderings ("turn on light" → "turn light on")
- NLP pipeline **already handles** these variations via:
  - Dependency parsing (extracts action regardless of word order)
  - Synonym generation via LLM
  - Entity normalization

**Recommendation:**
1. **First**, enhance paraphrasing to include semantic variations (synonyms, casual speech)
2. **Then**, integrate those richer paraphrases into the pipeline
3. **Focus on**: Learning user-specific vocabulary and speech patterns

**Better use case:**
Use paraphrases to collect **user feedback** on which commands were successful, then learn from those patterns over time.

## Future Enhancements

### 1. User-Specific Learning
- Track which paraphrases user actually uses
- Build personalized synonym dictionaries per user
- Adapt to individual speech patterns

### 2. Global Pattern Library
- Aggregate paraphrases across all users
- Identify common variations
- Improve base model for everyone

### 3. Multi-Language Support
- Generate paraphrases in user's native language
- Build cross-language synonym mappings
- Support code-switching (Thai + English)

### 4. Active Learning Loop
```
User says command
→ System interprets
→ User confirms/corrects
→ System generates paraphrases
→ User selects preferred variation
→ System learns from selection
→ Improves future matching
```

## References

- Frontend paraphrasing: `frontend/src/pages/Workspace.tsx` lines 551-591, 772
- Backend paraphrasing API: `backend/app/routers/paraphrase.py`
- Synonym generation: `backend/app/nlp_v3/synonym_generator.py`
- Entity normalization: `backend/app/nlp_v3/entity_normalizer.py`
- Main NLP pipeline: `backend/app/nlp_v3/main.py`
- Command analysis: `backend/app/routers/analyze_command.py`
