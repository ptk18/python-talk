# NLP v3 - Natural Language Processing Pipeline

## What It Does
Converts natural language commands like "draw a circle" into Python method calls.

## Models Used
- **spaCy** (`en_core_web_trf`) - Parses sentences to find actions and objects
- **Sentence Transformers** (`all-MiniLM-L6-v2`, `microsoft/codebert-base`) - Understands meaning similarity
- **Claude AI** - Generates synonyms for better matching

## How It Works
1. Parse command: "draw a blue square" → action="draw", objects=["square"]
2. Find similar methods using semantic matching and synonyms
3. Return best match with transparent scoring

## Key Features
- **Smart Matching**: Finds methods even with different words
- **Transparent Scoring**: Shows exactly why each method was chosen
- **Fast & Cached**: Pre-builds synonyms, remembers previous matches
