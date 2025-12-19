import os
import json
import asyncio
from typing import Dict, List, Optional
from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()


SYNONYM_SYSTEM_PROMPT = """You generate natural language synonyms and antonyms for Python method names.

Given a list of methods with their names and descriptions, provide:
1. Common PHRASAL expressions and words that users might say to invoke each method (synonyms)
2. Phrasal expressions and words that mean the opposite action (antonyms)

CRITICAL RULES FOR PHRASAL EXPRESSIONS:
- ALWAYS keep multi-word phrases together as single strings (e.g., "turn on", NOT "turn" and "on" separately)
- Prioritize complete phrasal verbs like "turn on", "switch off", "power up"
- Include both formal and casual variations
- Preserve natural language structure

Action-specific patterns:
- For "turn_on" methods: include "turn on", "switch on", "power on", "activate", "enable", "start", "open"
- For "turn_off" methods: include "turn off", "switch off", "power off", "deactivate", "disable", "stop", "close"
- For "increase" methods: include "turn up", "raise", "increase", "boost", "higher", "more"
- For "decrease" methods: include "turn down", "lower", "decrease", "reduce", "less"
- For "mute" methods: include "mute", "silence", "quiet", "turn off sound"
- For "unmute" methods: include "unmute", "unsilence", "turn on sound", "sound on"

Object variations:
- Include both full and shortened forms (e.g., "air conditioner" and "ac", "television" and "tv")
- Include "the" article variations ("turn on the ac", "turn on ac")

Antonym rules:
- For ON/OPEN actions, antonyms should be: "turn off", "switch off", "close", "stop", "disable", "deactivate", "power off", "shut down"
- For OFF/CLOSE actions, antonyms should be: "turn on", "switch on", "open", "start", "enable", "activate", "power on"
- For INCREASE actions, antonyms should be: "turn down", "lower", "decrease", "reduce", "less"
- For DECREASE actions, antonyms should be: "turn up", "raise", "increase", "boost", "more"

Provide 6-8 PHRASAL synonyms and 4-6 PHRASAL antonyms per method.
Output ONLY valid JSON: {"synonyms": {"method_name": ["phrase1", "phrase2", ...]}, "antonyms": {"method_name": ["phrase1", "phrase2", ...]}}
NO markdown, NO code blocks, NO explanations.

Examples:
Input methods:
- add: Add two numbers together
- turn_ac_on: Turn the air conditioner on
- turn_ac_off: Turn the air conditioner off

Output:
{"synonyms": {
  "add": ["sum", "plus", "combine", "total", "add up", "calculate sum", "add together", "sum up"],
  "turn_ac_on": ["turn on ac", "switch on ac", "ac on", "activate ac", "power on ac", "enable ac", "start ac", "open ac", "turn on the air conditioner", "activate the air conditioner", "power on the ac", "switch on the air conditioner"],
  "turn_ac_off": ["turn off ac", "switch off ac", "ac off", "deactivate ac", "power off ac", "disable ac", "stop ac", "close ac", "turn off the air conditioner", "deactivate the air conditioner", "power off the ac", "shut down the ac"]
},
"antonyms": {
  "add": ["subtract", "remove", "minus", "take away", "deduct"],
  "turn_ac_on": ["turn off", "switch off", "close", "stop", "disable", "deactivate", "power off", "shut down"],
  "turn_ac_off": ["turn on", "switch on", "open", "start", "enable", "activate", "power on", "start up"]
}}
"""


def extract_json_string(response_text: str) -> str:
    # Remove code block markers
    cleaned = response_text.replace('```json', '').replace('```', '')
    
    # Find JSON boundaries
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1

    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in response: {response_text}")

    json_str = cleaned[start:end].strip()
    
    return json_str


class SynonymService:

    def __init__(self, model: str = "anthropic:claude-3-haiku-20240307"):
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.agent = Agent(model, system_prompt=SYNONYM_SYSTEM_PROMPT)
        self._cache: Dict[str, Dict[str, List[str]]] = {}
        self._generating: Dict[str, bool] = {}  # Track ongoing generations

    async def generate_synonyms_async(
        self,
        methods: List[Dict[str, str]],
        cache_key: Optional[str] = None,
        timeout: int = 10
    ) -> Dict[str, Dict[str, List[str]]]:

        if cache_key and cache_key in self._cache:
            return self._cache[cache_key]
            
        # Prevent duplicate generation for same cache_key
        if cache_key and cache_key in self._generating:
            # Wait for ongoing generation (simple polling)
            for _ in range(timeout):
                await asyncio.sleep(0.5)
                if cache_key in self._cache:
                    return self._cache[cache_key]
            # Timeout waiting, continue with new generation
            
        if cache_key:
            self._generating[cache_key] = True

        method_lines = []
        for method in methods:
            name = method.get('name', '')
            desc = method.get('description', '') or method.get('docstring', '') or ''
            method_lines.append(f"- {name}: {desc if desc else 'no description'}")

        prompt = (
            "Generate synonyms and antonyms for these methods:\n"
            + "\n".join(method_lines)
            + "\n\nRemember: respond with JSON only including both synonyms and antonyms."
        )

        try:
            result = await self.agent.run(prompt)
            
            # Extract the actual response content from AgentRunResult
            if hasattr(result, 'data'):
                response_text = str(result.data)
            else:
                response_text = str(result)
            
            # If response is wrapped in AgentRunResult(...), extract the content
            if response_text.startswith('AgentRunResult(output='):
                start = response_text.find("'") + 1
                end = response_text.rfind("'")
                response_text = response_text[start:end]
            
            json_str = extract_json_string(response_text)
            
            # Unescape newlines and other escape sequences
            json_str = json_str.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
            
            parsed = json.loads(json_str)
            synonym_map = parsed.get('synonyms', {})
            antonym_map = parsed.get('antonyms', {})

            normalized = {
                'synonyms': {},
                'antonyms': {}
            }

            for method_name, synonyms in synonym_map.items():
                normalized['synonyms'][method_name] = [s.lower().strip() for s in synonyms if isinstance(s, str)]

            for method_name, antonyms in antonym_map.items():
                normalized['antonyms'][method_name] = [a.lower().strip() for a in antonyms if isinstance(a, str)]

            if cache_key:
                self._cache[cache_key] = normalized
                self._generating.pop(cache_key, None)  # Mark as complete

            return normalized

        except Exception as e:
            print(f"Failed to generate synonyms: {e}")
            if cache_key:
                self._generating.pop(cache_key, None)  # Mark as complete even on error
            return {'synonyms': {}, 'antonyms': {}}

    def generate_synonyms(
        self,
        methods: List[Dict[str, str]],
        cache_key: Optional[str] = None
    ) -> Dict[str, Dict[str, List[str]]]:
        return asyncio.run(self.generate_synonyms_async(methods, cache_key))

    def clear_cache(self, cache_key: Optional[str] = None):
        if cache_key:
            self._cache.pop(cache_key, None)
        else:
            self._cache.clear()


_synonym_service: Optional[SynonymService] = None


def get_synonym_service() -> SynonymService:
    global _synonym_service
    if _synonym_service is None:
        _synonym_service = SynonymService()
    return _synonym_service
