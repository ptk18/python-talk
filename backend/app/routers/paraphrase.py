from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Tuple
import os
import json
import asyncio
from pydantic_ai import Agent
from dotenv import load_dotenv
import re
from difflib import SequenceMatcher

# Load environment variables
load_dotenv(dotenv_path="app/nlp_v2/.env")

router = APIRouter(prefix="/user_command_paraphrasing_suggestion", tags=["Paraphrase"])

PARAPHRASE_SYSTEM_PROMPT = """You generate paraphrases for user commands and sentences. Keep meaning identical.

Rules:
- Generate natural, voice-friendly variations
- Keep the same numbers and entities exactly as they appear
- Keep the same intent and meaning
- Use simple, clear language
- Vary grammatical structure (active/passive, word order, sentence patterns)
- Use synonyms where appropriate
- Include a mix of variations:
  * Very similar: only grammar/word order changes
  * Moderately similar: some synonym replacements
  * Less similar: different phrasing but same meaning
- Output ONLY valid JSON in this format: {"variants":["...", "..."]}
- NO markdown, NO code blocks, NO explanations

Examples:
Input: "turn on the light"
Output: {"variants":["switch on the light", "turn the light on", "switch the light on", "activate the light", "power on the light", "make the light turn on", "get the light on", "illuminate the room"]}

Input: "add 5 and 3"
Output: {"variants":["sum 5 and 3", "5 plus 3", "combine 5 and 3", "add 3 and 5", "what is 5 plus 3", "calculate 5 plus 3", "5 added to 3", "total of 5 and 3"]}
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
    """Generate paraphrases using Claude API"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

    # Use Claude Haiku for fast paraphrase generation
    agent = Agent("anthropic:claude-3-haiku-20240307", system_prompt=PARAPHRASE_SYSTEM_PROMPT)

    prompt = f"""Generate {max_variants} alternative phrasings for this sentence/command: "{text}"

Generate a diverse mix of variations:
- Some with only grammar/word order changes (very similar)
- Some with synonym replacements (moderately similar)
- Some with rephrasing (less similar but same meaning)

Keep numbers and key entities exactly as they appear.
Output ONLY valid JSON: {{"variants":["...", "..."]}}
"""

    try:
        result = await agent.run(prompt)
        response_text = str(result.data if hasattr(result, 'data') else result)

        print(f"Claude response (first 200 chars): {response_text[:200]}")

        json_str = extract_json_string(response_text)
        parsed = json.loads(json_str)

        variants = parsed.get('variants', [])

        # Validate variants (remove duplicates, check numbers)
        validated_variants = validate_paraphrases(text, variants)

        # Sort by similarity score (most similar first)
        sorted_variants = sort_paraphrases_by_similarity(text, validated_variants)

        # Ensure we don't exceed max_variants
        return sorted_variants[:max_variants]

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
