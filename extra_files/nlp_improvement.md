# NLP Improvement Plan

## Overview
This document outlines the step-by-step plan to improve the NLP system's command recognition capabilities by implementing three key enhancements:
1. Lower LLM fallback threshold
2. LLM-generated synonyms integration
3. Paraphrase-based matching

---

## Current Problems

### Problem 1: LLM Fallback Too Late
**Location:** [main.py:162-207](backend/app/nlp_v2/main.py#L162-L207)

**Issue:** LLM fallback only triggers when `best_match.score < 100`, meaning it rarely activates. Even at 60-70% confidence, the NLP might be wrong.

**Impact:** Commands like "sum 5 and 3" may get low confidence scores but never reach the more capable LLM.

---

### Problem 2: Synonym Knowledge Isolated
**Location:** [auto_nl_interface_llm.py:253-303](backend/app/nlp_v2/auto_nl_interface_llm.py#L253-L303)

**Issue:** The LLM already generates excellent synonyms (`_build_synonym_map()`), but they're only used within the `NaturalLanguageInterface` class, not in the main NLP pipeline.

**Impact:** Semantic matcher doesn't know that "sum" = "add", "switch on" = "turn_on", etc.

---

### Problem 3: Single Command Attempt
**Issue:** System only tries to match the exact user input, doesn't explore variations.

**Impact:** If user says "sum 5 and 3" but the system expects "add", it fails even though we can generate "add 5 and 3" via paraphrasing.

---

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User Command: "sum 5 and 3"                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Load/Generate Synonyms (LLM - Cached)             │
│  ────────────────────────────────────────────────────       │
│  Output: {                                                  │
│    "add": ["sum", "plus", "combine", "total"],             │
│    "turn_light_on": ["switch on", "activate", "light on"]  │
│  }                                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Try Original Command Matching                     │
│  ────────────────────────────────────────                  │
│  - Intent parsing (verb/subject extraction)                │
│  - Parameter extraction (numbers, strings)                 │
│  - Semantic matching (HuggingFace) + Synonym boost         │
│  ────────────────────────────────────────                  │
│  Output: confidence = 45%  (not great!)                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Generate Paraphrases (if confidence < 80%)        │
│  ────────────────────────────────────────────────────       │
│  Input: "sum 5 and 3"                                      │
│  Output: [                                                 │
│    "add 5 and 3",                                          │
│    "5 plus 3",                                             │
│    "combine 5 and 3",                                      │
│    "total of 5 and 3"                                      │
│  ]                                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Try Matching Each Paraphrase                      │
│  ────────────────────────────────────────────────────       │
│  "add 5 and 3" → confidence = 95% ✓ (BEST!)               │
│  "5 plus 3" → confidence = 70%                             │
│  "combine 5 and 3" → confidence = 80%                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: Return Best Match OR LLM Fallback                 │
│  ────────────────────────────────────────────────────       │
│  IF best_confidence >= 60%:                                │
│    return best_result + metadata                           │
│  ELSE:                                                     │
│    trigger LLM fallback (Claude)                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Lower LLM Fallback Threshold (Quick Win)
**Time Estimate:** 15-30 minutes
**Difficulty:** Easy
**Impact:** High

#### Files to Modify:
1. `backend/app/routers/analyze_command.py`
2. `backend/app/nlp_v2/main.py`

#### Step-by-Step:

**1.1 Update analyze_command.py**
```python
# Line 46 - Change from:
confidence_threshold=30.0,

# To:
confidence_threshold=60.0,  # Lower threshold for earlier LLM intervention
```

**1.2 Update main.py - process_command()**
```python
# Line 162 - Change from:
if best_match.score < 100 and use_llm_fallback:

# To:
if best_match.score < confidence_threshold and use_llm_fallback:
```

**1.3 Update main.py - process_complex_command()**
```python
# Around line 301 - Ensure threshold is used consistently
# The complex command parser should also respect the confidence_threshold
```

#### Testing:
- Try command: "sum 5 and 3" (should trigger LLM fallback if semantic score < 60%)
- Try command: "switch on the light" (should trigger LLM fallback if semantic score < 60%)
- Verify LLM generates correct output

#### Expected Result:
✅ LLM fallback activates more frequently for ambiguous commands
✅ Better handling of synonym variations
✅ Fewer failed command recognitions

---

### Phase 2: Paraphrase-Based Matching
**Time Estimate:** 1-2 hours
**Difficulty:** Medium
**Impact:** Very High

#### Files to Create/Modify:
1. `backend/app/nlp_v2/paraphrase_matcher.py` (NEW)
2. `backend/app/nlp_v2/main.py` (MODIFY)
3. `backend/app/routers/analyze_command.py` (MODIFY)

#### Step-by-Step:

**2.1 Create paraphrase_matcher.py**

Create a new file that integrates paraphrasing into the matching pipeline:

```python
"""
Paraphrase-based command matching for improved recognition.
Generates variations of user commands and finds best match.
"""

from typing import Dict, Any, List, Optional
import asyncio
from app.routers.paraphrase import generate_paraphrases
from app.nlp_v2.main import process_command
from app.nlp_v2.extract_catalog_from_source_code.catalog import Catalog


async def process_command_with_paraphrases(
    text: str,
    catalog: Catalog,
    class_name: str,
    verbose: bool = False,
    use_semantic: bool = True,
    hf_token: Optional[str] = None,
    confidence_threshold: float = 60.0,
    use_llm_fallback: bool = True,
    source_file: Optional[str] = None,
    paraphrase_threshold: float = 80.0,  # Only use paraphrases if original < this
    max_paraphrases: int = 5
) -> Dict[str, Any]:
    """
    Try matching command with paraphrases if initial confidence is low.

    Process:
    1. Try original command first
    2. If confidence >= paraphrase_threshold, return immediately
    3. Otherwise, generate paraphrases and try each
    4. Return result with highest confidence

    Args:
        text: User's original command
        paraphrase_threshold: Only generate paraphrases if confidence below this
        max_paraphrases: Maximum number of paraphrases to try

    Returns:
        Best matching result with metadata about which variant matched
    """

    # Step 1: Try original command
    if verbose:
        print(f"\n[Paraphrase Matcher] Trying original: '{text}'")

    original_result = process_command(
        text=text,
        catalog=catalog,
        class_name=class_name,
        verbose=verbose,
        use_semantic=use_semantic,
        hf_token=hf_token,
        confidence_threshold=confidence_threshold,
        use_llm_fallback=use_llm_fallback,
        source_file=source_file
    )

    original_confidence = original_result.get('confidence', 0)

    if verbose:
        print(f"[Paraphrase Matcher] Original confidence: {original_confidence:.1f}%")

    # Step 2: If confidence is good enough, return immediately
    if original_confidence >= paraphrase_threshold:
        if verbose:
            print(f"[Paraphrase Matcher] Confidence sufficient, using original")
        original_result['matching_strategy'] = 'original_command'
        return original_result

    # Step 3: Generate paraphrases
    if verbose:
        print(f"[Paraphrase Matcher] Confidence < {paraphrase_threshold}%, generating paraphrases...")

    try:
        paraphrases = await generate_paraphrases(text, max_variants=max_paraphrases)

        if verbose:
            print(f"[Paraphrase Matcher] Generated {len(paraphrases)} paraphrases:")
            for i, p in enumerate(paraphrases, 1):
                print(f"  {i}. {p}")

    except Exception as e:
        if verbose:
            print(f"[Paraphrase Matcher] Failed to generate paraphrases: {e}")
        original_result['matching_strategy'] = 'original_command_only'
        return original_result

    # Step 4: Try each paraphrase
    best_result = original_result
    best_confidence = original_confidence
    best_variant = "original"

    for i, paraphrase in enumerate(paraphrases, 1):
        if verbose:
            print(f"\n[Paraphrase Matcher] Trying paraphrase {i}/{len(paraphrases)}: '{paraphrase}'")

        try:
            result = process_command(
                text=paraphrase,
                catalog=catalog,
                class_name=class_name,
                verbose=False,  # Don't spam logs for paraphrases
                use_semantic=use_semantic,
                hf_token=hf_token,
                confidence_threshold=confidence_threshold,
                use_llm_fallback=False,  # Don't trigger LLM for each paraphrase
                source_file=source_file
            )

            confidence = result.get('confidence', 0)

            if verbose:
                print(f"[Paraphrase Matcher]   Confidence: {confidence:.1f}%")

            if confidence > best_confidence:
                best_result = result
                best_confidence = confidence
                best_variant = paraphrase

                if verbose:
                    print(f"[Paraphrase Matcher]   ✓ New best match!")

                # If we found a very high confidence match, stop searching
                if confidence >= 90:
                    if verbose:
                        print(f"[Paraphrase Matcher]   Excellent match, stopping search")
                    break

        except Exception as e:
            if verbose:
                print(f"[Paraphrase Matcher]   Error: {e}")
            continue

    # Step 5: Add metadata and return
    if best_variant != "original":
        best_result['matched_via_paraphrase'] = best_variant
        best_result['original_command'] = text
        best_result['matching_strategy'] = 'paraphrase_matching'
        if verbose:
            print(f"\n[Paraphrase Matcher] Best match via paraphrase: '{best_variant}'")
            print(f"[Paraphrase Matcher] Final confidence: {best_confidence:.1f}%")
    else:
        best_result['matching_strategy'] = 'original_command'
        if verbose:
            print(f"\n[Paraphrase Matcher] Original command was best")

    # Step 6: LLM fallback if still low confidence
    if best_confidence < confidence_threshold and use_llm_fallback:
        if verbose:
            print(f"[Paraphrase Matcher] Confidence still < {confidence_threshold}%, triggering LLM fallback...")
        # Let the original process_command handle LLM fallback
        return process_command(
            text=text,
            catalog=catalog,
            class_name=class_name,
            verbose=verbose,
            use_semantic=use_semantic,
            hf_token=hf_token,
            confidence_threshold=confidence_threshold,
            use_llm_fallback=True,
            source_file=source_file
        )

    return best_result


def process_command_with_paraphrases_sync(
    text: str,
    catalog: Catalog,
    class_name: str,
    **kwargs
) -> Dict[str, Any]:
    """Synchronous wrapper for process_command_with_paraphrases"""
    return asyncio.run(process_command_with_paraphrases(
        text=text,
        catalog=catalog,
        class_name=class_name,
        **kwargs
    ))
```

**2.2 Update analyze_command.py**

```python
# Add import at top
from app.nlp_v2.paraphrase_matcher import process_command_with_paraphrases_sync

# Line 38-49 - Replace process_complex_command call with:
result = process_command_with_paraphrases_sync(
    text=command,
    catalog=catalog,
    class_name=class_name,
    verbose=False,
    use_semantic=True,
    hf_token=None,
    confidence_threshold=60.0,
    use_llm_fallback=True,
    source_file=temp_path,
    paraphrase_threshold=80.0,  # Only use paraphrases if original < 80%
    max_paraphrases=5
)
```

**2.3 Update main.py (Optional)**

Optionally expose the paraphrase matcher as part of the main module:

```python
# Add to imports
from app.nlp_v2.paraphrase_matcher import process_command_with_paraphrases_sync

# Optionally create alias
process_command_enhanced = process_command_with_paraphrases_sync
```

#### Testing:
```bash
# Test cases that should now work:
1. "sum 5 and 3" → should match via paraphrase "add 5 and 3"
2. "switch on the light" → should match via paraphrase "turn light on"
3. "5 plus 3" → should match via paraphrase "add 5 and 3"
4. "make it warmer" → should match via paraphrase "increase temperature"
5. "cool down" → should match via paraphrase "decrease temperature"
```

#### Expected Result:
✅ Commands with synonyms now match successfully
✅ Paraphrasing helps find the right method even with varied phrasing
✅ Metadata shows which paraphrase worked (for learning/debugging)

---

### Phase 3: LLM-Generated Synonyms Integration
**Time Estimate:** 1-2 hours
**Difficulty:** Medium
**Impact:** High

#### Files to Create/Modify:
1. `backend/app/nlp_v2/synonym_service.py` (NEW)
2. `backend/app/nlp_v2/semantic_matcher.py` (MODIFY)
3. `backend/app/nlp_v2/main.py` (MODIFY)

#### Step-by-Step:

**3.1 Create synonym_service.py**

Extract and enhance synonym generation from `auto_nl_interface_llm.py`:

```python
"""
Synonym generation service for method name variations.
Uses LLM to generate natural language synonyms for methods.
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()


SYNONYM_SYSTEM_PROMPT = """You generate natural language synonyms for Python method names.

Given a list of methods with their names and descriptions, provide common phrases and words that users might say to invoke each method.

Rules:
- Provide natural, conversational variations
- Include common synonyms for action verbs
- Include shortened forms (e.g., "temp" for "temperature", "ac" for "air conditioner")
- Use lowercase
- Provide 5-8 variations per method
- Output ONLY valid JSON: {"synonyms": {"method_name": ["synonym1", "synonym2", ...]}}
- NO markdown, NO code blocks, NO explanations

Examples:
Input methods:
- add: Add two numbers together
- turn_light_on: Turn the light on

Output:
{"synonyms": {
  "add": ["sum", "plus", "combine", "total", "add up", "calculate sum"],
  "turn_light_on": ["switch on light", "light on", "activate light", "power on light", "turn on the light", "enable light"]
}}
"""


def extract_json_string(response_text: str) -> str:
    """Extract the first JSON object from an LLM response."""
    cleaned = response_text.replace('```json', '').replace('```', '')
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1

    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in response: {response_text}")

    return cleaned[start:end]


class SynonymService:
    """Service for generating and caching method synonyms"""

    def __init__(self, model: str = "anthropic:claude-3-haiku-20240307"):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.agent = Agent(model, system_prompt=SYNONYM_SYSTEM_PROMPT)
        self._cache: Dict[str, Dict[str, List[str]]] = {}

    async def generate_synonyms_async(
        self,
        methods: List[Dict[str, str]],
        cache_key: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Generate synonyms for a list of methods.

        Args:
            methods: List of dicts with 'name' and 'description'
            cache_key: Optional key for caching (e.g., class_name)

        Returns:
            Dict mapping method_name -> list of synonyms
        """

        # Check cache
        if cache_key and cache_key in self._cache:
            return self._cache[cache_key]

        # Build prompt
        method_lines = []
        for method in methods:
            name = method.get('name', '')
            desc = method.get('description', '') or method.get('docstring', '') or ''
            method_lines.append(f"- {name}: {desc if desc else 'no description'}")

        prompt = (
            "Generate synonyms for these methods:\n"
            + "\n".join(method_lines)
            + "\n\nRemember: respond with JSON only."
        )

        try:
            result = await self.agent.run(prompt)
            response_text = str(result.data if hasattr(result, 'data') else result)

            json_str = extract_json_string(response_text)
            parsed = json.loads(json_str)
            synonym_map = parsed.get('synonyms', {})

            # Normalize synonyms to lowercase
            normalized = {}
            for method_name, synonyms in synonym_map.items():
                normalized[method_name] = [s.lower().strip() for s in synonyms if isinstance(s, str)]

            # Cache result
            if cache_key:
                self._cache[cache_key] = normalized

            return normalized

        except Exception as e:
            print(f"Failed to generate synonyms: {e}")
            # Return empty dict on failure
            return {}

    def generate_synonyms(
        self,
        methods: List[Dict[str, str]],
        cache_key: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Synchronous wrapper for generate_synonyms_async"""
        return asyncio.run(self.generate_synonyms_async(methods, cache_key))

    def clear_cache(self, cache_key: Optional[str] = None):
        """Clear synonym cache"""
        if cache_key:
            self._cache.pop(cache_key, None)
        else:
            self._cache.clear()


# Global singleton instance
_synonym_service: Optional[SynonymService] = None


def get_synonym_service() -> SynonymService:
    """Get global synonym service instance"""
    global _synonym_service
    if _synonym_service is None:
        _synonym_service = SynonymService()
    return _synonym_service
```

**3.2 Update semantic_matcher.py**

Add synonym boosting to the semantic matcher:

```python
# Add to imports at top
from typing import List, Dict, Tuple, Optional, Set

# Modify find_best_match method (around line 42)
def find_best_match(
    self,
    command: str,
    methods: List[Dict],
    top_k: int = 3,
    min_confidence: float = 0.3,
    synonyms: Optional[Dict[str, List[str]]] = None  # NEW parameter
) -> List[Tuple[Dict, float]]:
    """
    Find best matching methods with synonym support.

    Args:
        command: User's command text
        methods: List of method dictionaries
        top_k: Number of top matches to return
        min_confidence: Minimum confidence threshold
        synonyms: Optional dict of {method_name: [synonym1, synonym2, ...]}
    """
    if not methods:
        return []

    # Build method texts for embedding
    method_texts = []
    for method in methods:
        method_name = method.get('name', '').replace('_', ' ')
        description = method.get('description', '')
        text = f"{method_name}"
        if description:
            text += f" - {description}"
        method_texts.append(text)

    # Get semantic similarity scores
    try:
        scores = self.get_similarity_scores(command, method_texts)
    except Exception as e:
        return []

    command_lower = command.lower()
    command_words = set(command_lower.split())

    boosted_scores = []
    for i, method in enumerate(methods):
        score = scores[i]
        method_name = method.get('name', '').replace('_', ' ').lower()

        # Boost 1: Exact method name in command
        if method_name in command_lower:
            score = min(1.0, score + 0.15)

        # Boost 2: Synonym matching (NEW)
        if synonyms and method.get('name') in synonyms:
            method_synonyms = synonyms[method.get('name')]

            # Check if any synonym appears in command
            for syn in method_synonyms:
                syn_lower = syn.lower()
                syn_words = set(syn_lower.split())

                # Exact phrase match
                if syn_lower in command_lower:
                    score = min(1.0, score + 0.20)  # Strong boost
                    break

                # Word overlap match
                overlap = len(command_words & syn_words)
                if overlap > 0:
                    # Partial boost based on overlap
                    boost = min(0.15, overlap * 0.05)
                    score = min(1.0, score + boost)
                    break

        boosted_scores.append(score)

    # Filter and sort matches
    matches = []
    for i, method in enumerate(methods):
        if boosted_scores[i] >= min_confidence:
            matches.append((method, boosted_scores[i]))

    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:top_k]
```

**3.3 Update main.py**

Integrate synonym generation into the command processing pipeline:

```python
# Add imports
from app.nlp_v2.synonym_service import get_synonym_service

# Modify find_matching_methods_semantic (around line 28)
def find_matching_methods_semantic(
    text: str,
    catalog: Catalog,
    class_name: str,
    hf_token: Optional[str] = None,
    use_synonyms: bool = True  # NEW parameter
) -> list[MatchResult]:
    methods = catalog.get_methods(class_name)

    if not methods:
        return []

    method_dicts = [
        {
            "name": method.name,
            "description": method.docstring or method.name.replace('_', ' '),
            "parameters": method.parameters,
            "method_info": method
        }
        for method in methods
    ]

    # Generate synonyms if enabled
    synonyms = None
    if use_synonyms:
        try:
            synonym_service = get_synonym_service()
            synonym_input = [
                {
                    "name": m["name"],
                    "description": m["description"]
                }
                for m in method_dicts
            ]
            synonyms = synonym_service.generate_synonyms(
                synonym_input,
                cache_key=class_name  # Cache by class name
            )
        except Exception as e:
            print(f"Failed to generate synonyms, continuing without: {e}")
            synonyms = None

    # Use synonyms in semantic matching
    matcher = HFSemanticMatcher(hf_token=hf_token)
    semantic_matches = matcher.find_best_match(
        command=text,
        methods=method_dicts,
        top_k=5,
        min_confidence=0.2,
        synonyms=synonyms  # Pass synonyms
    )

    results = []
    for method_dict, confidence in semantic_matches:
        results.append(MatchResult(
            method_info=method_dict["method_info"],
            score=confidence * 100,
            matched_component="semantic_similarity"
        ))

    return results


# Update process_command to use synonyms (around line 68)
# Add use_synonyms parameter and pass to find_matching_methods_semantic
```

#### Testing:
```python
# Test synonym generation
from app.nlp_v2.synonym_service import get_synonym_service

service = get_synonym_service()
methods = [
    {"name": "add", "description": "Add two numbers together"},
    {"name": "turn_light_on", "description": "Turn the light on"}
]

synonyms = service.generate_synonyms(methods)
print(synonyms)
# Should output something like:
# {
#   "add": ["sum", "plus", "combine", "total", ...],
#   "turn_light_on": ["switch on light", "light on", ...]
# }

# Test commands that should now have higher confidence:
# "sum 5 and 3" → should boost "add" method score
# "switch on the light" → should boost "turn_light_on" method score
```

#### Expected Result:
✅ Synonyms automatically generated for all methods
✅ Semantic matching scores boosted when synonyms match
✅ Results cached per class for performance
✅ Better recognition of varied phrasings

---

### Phase 4: Command Caching (Optional Enhancement)
**Time Estimate:** 30-60 minutes
**Difficulty:** Easy
**Impact:** Medium (Performance)

#### Files to Create:
1. `backend/app/nlp_v2/command_cache.py` (NEW)

#### Step-by-Step:

**4.1 Create command_cache.py**

```python
"""
Simple in-memory cache for command pattern matching.
Stores successful command→method mappings for faster lookup.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class CommandPattern:
    """Represents a normalized command pattern"""

    def __init__(self, pattern: str, method: str, confidence: float, metadata: Dict[str, Any]):
        self.pattern = pattern
        self.method = method
        self.confidence = confidence
        self.metadata = metadata
        self.hit_count = 0
        self.last_used = datetime.now()

    def record_hit(self):
        """Record a cache hit"""
        self.hit_count += 1
        self.last_used = datetime.now()


class CommandCache:
    """Cache for command patterns"""

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        self._cache: Dict[str, CommandPattern] = {}
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)

    def normalize_command(self, command: str) -> str:
        """
        Normalize command to pattern by replacing numbers with placeholders.

        Example: "add 5 and 3" → "add {num} and {num}"
        """
        # Replace numbers with {num}
        normalized = re.sub(r'\d+(?:\.\d+)?', '{num}', command.lower())
        # Collapse whitespace
        normalized = ' '.join(normalized.split())
        return normalized

    def get(self, command: str) -> Optional[Dict[str, Any]]:
        """
        Try to get cached result for command.

        Returns:
            Cached result dict or None
        """
        pattern = self.normalize_command(command)

        if pattern in self._cache:
            cached = self._cache[pattern]

            # Check if expired
            if datetime.now() - cached.last_used > self.ttl:
                del self._cache[pattern]
                return None

            # Record hit and return
            cached.record_hit()
            return {
                'method': cached.method,
                'confidence': cached.confidence,
                'from_cache': True,
                **cached.metadata
            }

        return None

    def put(self, command: str, method: str, confidence: float, metadata: Dict[str, Any] = None):
        """
        Cache a successful command→method mapping.

        Args:
            command: Original command text
            method: Method name that matched
            confidence: Confidence score
            metadata: Additional metadata to cache
        """
        pattern = self.normalize_command(command)

        # Evict old entries if cache is full
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        self._cache[pattern] = CommandPattern(
            pattern=pattern,
            method=method,
            confidence=confidence,
            metadata=metadata or {}
        )

    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self._cache:
            return

        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_used)
        del self._cache[lru_key]

    def clear(self):
        """Clear entire cache"""
        self._cache.clear()

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self._cache:
            return {
                'size': 0,
                'total_hits': 0,
                'patterns': []
            }

        total_hits = sum(p.hit_count for p in self._cache.values())

        # Top patterns by hit count
        top_patterns = sorted(
            self._cache.values(),
            key=lambda p: p.hit_count,
            reverse=True
        )[:10]

        return {
            'size': len(self._cache),
            'total_hits': total_hits,
            'top_patterns': [
                {
                    'pattern': p.pattern,
                    'method': p.method,
                    'hits': p.hit_count
                }
                for p in top_patterns
            ]
        }


# Global cache instance
_command_cache: Optional[CommandCache] = None


def get_command_cache() -> CommandCache:
    """Get global command cache instance"""
    global _command_cache
    if _command_cache is None:
        _command_cache = CommandCache()
    return _command_cache
```

**4.2 Integrate cache into paraphrase_matcher.py**

```python
# Add import
from app.nlp_v2.command_cache import get_command_cache

# At start of process_command_with_paraphrases:
async def process_command_with_paraphrases(...):
    # Check cache first
    cache = get_command_cache()
    cached_result = cache.get(text)

    if cached_result and cached_result['confidence'] >= paraphrase_threshold:
        if verbose:
            print(f"[Cache] Hit! Using cached result for '{text}'")
        return cached_result

    # ... rest of existing code ...

    # Before returning best_result, cache it
    if best_confidence >= paraphrase_threshold:
        cache.put(
            command=text,
            method=best_result.get('method'),
            confidence=best_confidence,
            metadata=best_result
        )

    return best_result
```

#### Testing:
```python
# First request - should be slow (generates paraphrases)
result1 = process_command("sum 5 and 3")

# Second request with same pattern - should be fast (from cache)
result2 = process_command("sum 10 and 20")  # Same pattern: "sum {num} and {num}"

# Check cache stats
from app.nlp_v2.command_cache import get_command_cache
cache = get_command_cache()
print(cache.stats())
```

#### Expected Result:
✅ Faster response times for repeated command patterns
✅ Cache statistics for monitoring popular commands
✅ Automatic cache eviction for old/unused patterns

---

## Testing Strategy

### Unit Tests
Create `backend/tests/test_nlp_improvements.py`:

```python
import pytest
from app.nlp_v2.synonym_service import SynonymService
from app.nlp_v2.command_cache import CommandCache
from app.nlp_v2.paraphrase_matcher import process_command_with_paraphrases_sync
from app.nlp_v2.extract_catalog_from_source_code.ast_extractor import extract_from_file


class TestSynonymService:
    def test_synonym_generation(self):
        service = SynonymService()
        methods = [
            {"name": "add", "description": "Add two numbers"}
        ]
        synonyms = service.generate_synonyms(methods)

        assert "add" in synonyms
        assert len(synonyms["add"]) > 0
        assert "sum" in synonyms["add"] or "plus" in synonyms["add"]

    def test_synonym_caching(self):
        service = SynonymService()
        methods = [{"name": "test", "description": "Test method"}]

        result1 = service.generate_synonyms(methods, cache_key="test_class")
        result2 = service.generate_synonyms(methods, cache_key="test_class")

        # Should be same object (from cache)
        assert result1 is result2


class TestCommandCache:
    def test_pattern_normalization(self):
        cache = CommandCache()

        assert cache.normalize_command("add 5 and 3") == "add {num} and {num}"
        assert cache.normalize_command("add 10 and 20") == "add {num} and {num}"
        assert cache.normalize_command("set temp to 22") == "set temp to {num}"

    def test_cache_hit(self):
        cache = CommandCache()

        cache.put("add 5 and 3", "add", 95.0, {"test": True})
        result = cache.get("add 10 and 20")  # Different numbers, same pattern

        assert result is not None
        assert result['method'] == "add"
        assert result['from_cache'] is True


class TestParaphraseMatching:
    @pytest.fixture
    def calculator_catalog(self):
        return extract_from_file("backend/app/nlp_v2/source_kbs/calculator.py")

    def test_paraphrase_improves_matching(self, calculator_catalog):
        # Command that should fail without paraphrasing
        result = process_command_with_paraphrases_sync(
            text="sum 5 and 3",
            catalog=calculator_catalog,
            class_name="Calculator",
            use_semantic=True,
            confidence_threshold=60.0,
            paraphrase_threshold=80.0
        )

        assert result.get('method') == 'add'
        assert result.get('confidence', 0) >= 60.0
```

### Integration Tests

Test end-to-end with actual API:

```bash
# Test via curl
curl -X POST http://localhost:8000/api/analyze_command \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": 1,
    "command": "sum 5 and 3"
  }'

# Should return:
# {
#   "result": {
#     "method": "add",
#     "confidence": 95.0,
#     "matching_strategy": "paraphrase_matching",
#     "matched_via_paraphrase": "add 5 and 3"
#   }
# }
```

### Manual Test Cases

**Calculator Commands:**
- ✅ "sum 5 and 3" → `add(5, 3)`
- ✅ "5 plus 3" → `add(5, 3)`
- ✅ "subtract 2 from 5" → `subtract(5, 2)` (note order!)
- ✅ "5 minus 2" → `subtract(5, 2)`
- ✅ "multiply 4 and 7" → `multiply(4, 7)`
- ✅ "4 times 7" → `multiply(4, 7)`

**Smart Home Commands:**
- ✅ "switch on the light" → `turn_light_on()`
- ✅ "light on" → `turn_light_on()`
- ✅ "activate the light" → `turn_light_on()`
- ✅ "turn off the TV" → `turn_tv_off()`
- ✅ "TV off" → `turn_tv_off()`
- ✅ "make it warmer" → `increase_temperature()`
- ✅ "cool down" → `decrease_temperature()`
- ✅ "set temp to 22" → `set_temperature(22)`

---

## Rollback Plan

If issues occur, rollback in reverse order:

### Rollback Phase 4 (Cache):
- Remove cache imports from `paraphrase_matcher.py`
- Delete `command_cache.py`
- No breaking changes

### Rollback Phase 3 (Synonyms):
- Revert `semantic_matcher.py` to remove synonyms parameter
- Remove synonym_service imports from `main.py`
- Delete `synonym_service.py`

### Rollback Phase 2 (Paraphrases):
- Revert `analyze_command.py` to use `process_complex_command`
- Delete `paraphrase_matcher.py`

### Rollback Phase 1 (Threshold):
- Change `confidence_threshold` back to 30.0
- Change LLM fallback check back to `< 100`

---

## Performance Considerations

### Expected Performance Impact:

**Phase 1 (Threshold):**
- ⚠️ More LLM calls (slower but more accurate)
- Mitigation: Cache LLM results

**Phase 2 (Paraphrases):**
- ⚠️ ~1-2s added for paraphrase generation (only when confidence < 80%)
- ⚠️ 2-5 additional NLP passes per low-confidence command
- Mitigation:
  - Only generate paraphrases when needed
  - Limit to 5 paraphrases
  - Stop early if high confidence found

**Phase 3 (Synonyms):**
- ⚠️ Initial LLM call to generate synonyms (~1-2s, once per class)
- ✅ Cache results indefinitely
- ✅ Minimal overhead after initial generation

**Phase 4 (Cache):**
- ✅ Significant speedup for repeated patterns
- ✅ O(1) lookup time

### Optimization Ideas:

1. **Async Processing:** Run paraphrase generation in parallel
2. **Synonym Pre-generation:** Generate synonyms when code is uploaded, not on first command
3. **Smart Caching:** Cache paraphrases too, not just final results
4. **Batch Processing:** If multiple commands, process in parallel

---

## Monitoring & Metrics

### Add Logging:

```python
import logging

logger = logging.getLogger("nlp_improvements")

# In paraphrase matcher:
logger.info(f"Command: '{text}', Original confidence: {original_confidence}%")
logger.info(f"Best match: {best_variant}, Final confidence: {best_confidence}%")
logger.info(f"Strategy: {best_result['matching_strategy']}")

# Track metrics:
metrics = {
    "paraphrase_usage_rate": paraphrases_used / total_commands,
    "cache_hit_rate": cache_hits / total_commands,
    "avg_confidence_improvement": avg(final_conf - original_conf),
    "llm_fallback_rate": llm_calls / total_commands
}
```

### Dashboard Queries:

```sql
-- Most common command patterns
SELECT pattern, COUNT(*) as usage_count
FROM command_cache
GROUP BY pattern
ORDER BY usage_count DESC
LIMIT 20;

-- Average confidence by matching strategy
SELECT matching_strategy, AVG(confidence) as avg_confidence
FROM command_results
GROUP BY matching_strategy;

-- Paraphrase success rate
SELECT
  COUNT(CASE WHEN matched_via_paraphrase IS NOT NULL THEN 1 END) as paraphrase_success,
  COUNT(*) as total
FROM command_results;
```

---

## Success Criteria

### Phase 1 Success:
- ✅ LLM fallback triggers more frequently
- ✅ Commands with 30-60% confidence now get LLM assistance
- ✅ No regression in high-confidence commands

### Phase 2 Success:
- ✅ "sum 5 and 3" correctly matches `add()`
- ✅ "switch on light" correctly matches `turn_light_on()`
- ✅ At least 80% of synonym variations now work
- ✅ Response time < 3s for paraphrase-based matching

### Phase 3 Success:
- ✅ Synonyms generated automatically for all methods
- ✅ Semantic matching scores improve by 15-30% for synonym commands
- ✅ Synonym generation cached (only happens once)

### Phase 4 Success:
- ✅ Cache hit rate > 30% for repeated patterns
- ✅ Cached responses < 100ms
- ✅ Cache stats accessible for monitoring

---

## Future Enhancements

### Post-Implementation Ideas:

1. **User Feedback Loop:**
   - Show matched command to user for confirmation
   - Store confirmed mappings in database
   - Learn from user corrections

2. **Multi-Language Support:**
   - Extend paraphrasing to other languages
   - Use language detection before processing

3. **Context-Aware Matching:**
   - Remember previous commands in conversation
   - Use context to disambiguate ("turn it on" → what is "it"?)

4. **Parameter Intelligence:**
   - Better extraction for "subtract 2 from 5" → `{a: 5, b: 2}`
   - Handle units: "increase by 5 degrees" → `{amount: 5}`

5. **Voice-Optimized Paraphrasing:**
   - Generate paraphrases optimized for voice input
   - Handle homophones and common speech recognition errors

---

## Timeline

**Total Estimated Time:** 3-5 hours

- Phase 1: 30 minutes
- Phase 2: 1.5 hours
- Phase 3: 1.5 hours
- Phase 4: 1 hour
- Testing & Documentation: 30 minutes

**Recommended Schedule:**
- Day 1: Phase 1 + Testing
- Day 2: Phase 2 + Testing
- Day 3: Phase 3 + Testing
- Day 4: Phase 4 + Integration Testing + Documentation

---

## Questions & Decisions

### Open Questions:

1. **Paraphrase Threshold:** Should it be 80% or lower (60-70%)?
2. **Max Paraphrases:** 5 is reasonable, or should we try more (10)?
3. **Cache Size:** 1000 patterns enough, or should we increase?
4. **TTL:** 24 hours for cache expiry, or longer?
5. **Synonym Update:** Should synonyms be regenerated periodically?

### Decisions Made:

- ✅ Use Anthropic Claude Haiku for paraphrase/synonym generation (fast + cheap)
- ✅ Cache synonyms per class (not per session)
- ✅ Use in-memory cache (not Redis) for simplicity
- ✅ Keep paraphrase generation async to avoid blocking

---

## Appendix

### File Structure After Implementation:

```
backend/app/nlp_v2/
├── main.py (MODIFIED)
├── semantic_matcher.py (MODIFIED)
├── paraphrase_matcher.py (NEW)
├── synonym_service.py (NEW)
├── command_cache.py (NEW)
├── semantic_parsing/
│   ├── intent_parser.py
│   ├── parameter_extractor.py
│   └── ...
└── ...

backend/app/routers/
├── analyze_command.py (MODIFIED)
└── paraphrase.py (existing)

backend/tests/
└── test_nlp_improvements.py (NEW)
```

### Dependencies:

All dependencies already installed:
- ✅ pydantic-ai (for LLM agents)
- ✅ anthropic (Claude API)
- ✅ requests (HuggingFace API)
- ✅ spacy (NLP)

No new dependencies needed! 🎉

---
**Be careful with**
- keep the code simple and do not overkill
- do not inlcude emojis, special characters and unnecessary comments in the code 

**End of Implementation Plan**
