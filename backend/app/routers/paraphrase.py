from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Tuple
import os
import json
import asyncio
from anthropic import AsyncAnthropic
from dotenv import load_dotenv
import re
from difflib import SequenceMatcher
from functools import lru_cache
import hashlib

# Load environment variables
load_dotenv(dotenv_path="app/nlp_v3/.env")

# Initialize Anthropic client once
_anthropic_client = None

def get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        _anthropic_client = AsyncAnthropic(api_key=api_key)
    return _anthropic_client

# Simple in-memory cache for paraphrases
_paraphrase_cache = {}

router = APIRouter(prefix="/user_command_paraphrasing_suggestion", tags=["Paraphrase"])

PARAPHRASE_SYSTEM_PROMPT = """You generate paraphrases for user commands and sentences. Keep meaning identical.

Rules:
- Generate natural, voice-friendly variations
- Keep the same numbers and entities exactly as they appear
- Keep the same intent and meaning
- Use simple, clear language
- ONLY change word order OR replace with simple, common synonyms
- Do NOT creatively rephrase or use complex alternatives
- Include two types of variations:
  * Word order changes only (same words, different arrangement)
  * Simple synonym replacements (common, everyday alternatives)
- Output ONLY valid JSON in this format: {"variants":["...", "..."]}
- NO markdown, NO code blocks, NO explanations

Examples:
Input: "turn on the light"
Output: {"variants":["turn the light on", "switch on the light", "switch the light on", "power on the light", "turn on the lamp", "switch on the lamp"]}

Input: "add 5 and 3"
Output: {"variants":["5 plus 3", "add 3 and 5", "3 plus 5", "sum 5 and 3", "sum 3 and 5"]}
"""

class ParaphraseRequest(BaseModel):
    text: str = Field(..., description="The user's original command text")
    max_variants: int = Field(default=10, ge=1, le=10, description="Maximum number of paraphrases to generate")

class ParaphraseResponse(BaseModel):
    variants: List[str] = Field(..., description="List of paraphrased versions of the command")

def extract_json_string(response_text: str) -> str:
    """Extract the first JSON object from an LLM response."""
    cleaned = response_text.replace('```json', '').replace('```', '')
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1

    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in response: {response_text}")

    return cleaned[start:end]

def calculate_similarity_score(original: str, variant: str) -> float:
    """
    Calculate similarity score between original and variant.
    Higher score = more similar (grammar changes only)
    Lower score = less similar (more synonym/structural changes)

    Combines multiple metrics:
    - Word overlap ratio (same words, different order)
    - Character-level similarity
    - Length similarity
    """
    original_lower = original.lower()
    variant_lower = variant.lower()

    # 1. Word-level similarity (60% weight)
    original_words = set(original_lower.split())
    variant_words = set(variant_lower.split())

    if not original_words or not variant_words:
        word_similarity = 0.0
    else:
        intersection = original_words.intersection(variant_words)
        union = original_words.union(variant_words)
        word_similarity = len(intersection) / len(union) if union else 0.0

    # 2. Character-level similarity using SequenceMatcher (30% weight)
    char_similarity = SequenceMatcher(None, original_lower, variant_lower).ratio()

    # 3. Length similarity (10% weight) - penalize very different lengths
    len_ratio = min(len(original), len(variant)) / max(len(original), len(variant)) if max(len(original), len(variant)) > 0 else 0.0

    # Weighted combination
    total_score = (word_similarity * 0.6) + (char_similarity * 0.3) + (len_ratio * 0.1)

    return total_score

def validate_paraphrases(original_text: str, variants: List[str]) -> List[str]:
    """Basic validation to ensure paraphrases maintain numbers from original"""
    original_numbers = set(re.findall(r'\d+', original_text))

    validated = []
    for variant in variants:
        # Skip if identical to original
        if variant.lower().strip() == original_text.lower().strip():
            continue

        variant_numbers = set(re.findall(r'\d+', variant))
        # Keep variant if it has the same numbers or if original had no numbers
        if not original_numbers or variant_numbers == original_numbers:
            validated.append(variant)

    return validated

def sort_paraphrases_by_similarity(original_text: str, variants: List[str]) -> List[str]:
    """
    Sort paraphrases by similarity score.
    Most similar (grammar changes) come first, least similar (more changes) come last.
    """
    # Calculate similarity score for each variant
    scored_variants: List[Tuple[str, float]] = []
    for variant in variants:
        score = calculate_similarity_score(original_text, variant)
        scored_variants.append((variant, score))

    # Sort by score descending (highest similarity first)
    scored_variants.sort(key=lambda x: x[1], reverse=True)

    # Return just the variant strings
    return [variant for variant, score in scored_variants]

async def generate_paraphrases(text: str, max_variants: int) -> List[str]:
    """Generate paraphrases using Claude API with caching"""
    # Check cache first
    cache_key = f"{text.lower().strip()}:{max_variants}"
    if cache_key in _paraphrase_cache:
        return _paraphrase_cache[cache_key]

    client = get_anthropic_client()

    # Simplified, shorter prompt for faster response
    prompt = f'Generate {max_variants} variations for: "{text}"\nOutput JSON: {{"variants":["...", "..."]}}'

    try:
        # Direct API call with minimal tokens for speed
        message = await client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,  # Reduced from default, enough for paraphrases
            temperature=0.7,  # Some creativity but consistent
            system=PARAPHRASE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        json_str = extract_json_string(response_text)
        parsed = json.loads(json_str)

        variants = parsed.get('variants', [])

        # Validate variants (remove duplicates, check numbers)
        validated_variants = validate_paraphrases(text, variants)

        # Sort by similarity score (most similar first)
        sorted_variants = sort_paraphrases_by_similarity(text, validated_variants)

        # Ensure we don't exceed max_variants
        result = sorted_variants[:max_variants]

        # Cache the result
        _paraphrase_cache[cache_key] = result

        return result

    except Exception as e:
        print(f"Error generating paraphrases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate paraphrases: {str(e)}")

@router.post("", response_model=ParaphraseResponse)
async def paraphrase_command(request: ParaphraseRequest):
    """
    Generate paraphrased versions of a user command while maintaining the same meaning and numbers.

    This endpoint uses Claude AI to generate natural language variations of the input command
    that keep the same intent, operation, and numerical values.
    """
    try:
        variants = await generate_paraphrases(request.text, request.max_variants)

        return ParaphraseResponse(variants=variants)

    except ValueError as ve:
        raise HTTPException(status_code=500, detail=str(ve))
    except Exception as e:
        print(f"Unexpected error in paraphrase endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during paraphrasing")
