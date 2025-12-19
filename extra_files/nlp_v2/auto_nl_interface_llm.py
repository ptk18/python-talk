import json
import asyncio
import inspect
import importlib.util
import os
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()

SYNONYM_SYSTEM_PROMPT = """You are a helper that suggests natural language synonyms for callable method names.\n\nReturn ONLY valid JSON with this shape: {\"synonyms\": {\"method_name\": [\"synonym\", ...]}}.\n\nGuidelines:\n- Provide banking-related terms and short phrases that a user might say.\n- Use lowercase, no quotation marks except the JSON quotes.\n- Include at least the original method name if nothing else fits.\n- Prefer up to 6 concise items per method.\n- Do not add prose, explanations, or markdown fences.\n"""


def extract_json_string(response_text: str) -> str:
    """Extract the first JSON object from an LLM response."""
    cleaned = response_text.replace('```json', '').replace('```', '')
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1

    if start == -1 or end == 0:
        raise ValueError(f"No JSON found in response: {response_text}")

    return cleaned[start:end]


class FunctionInfo(BaseModel):
    name: str
    params: Dict[str, str] 
    description: str
    required_params: List[str]

def load_python_file(file_path: str):
    spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def extract_function_info(func) -> FunctionInfo:
    sig = inspect.signature(func)
    
    params = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue
        
        if param.annotation != inspect.Parameter.empty:
            param_type = param.annotation.__name__
        else:
            param_type = "any"
        
        params[param_name] = param_type
        
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    doc = inspect.getdoc(func)
    if doc:
        description = doc.split('\n')[0]  
    else:
        description = f"Execute {func.__name__}"
    
    return FunctionInfo(
        name=func.__name__,
        params=params,
        description=description,
        required_params=required
    )

def analyze_python_file(file_path: str) -> Dict[str, List[FunctionInfo]]:
    module = load_python_file(file_path)
    
    result = {}
    
    for class_name, class_obj in inspect.getmembers(module, inspect.isclass):
        if class_obj.__module__ == "dynamic_module":
            methods = []
            
            for method_name, method in inspect.getmembers(class_obj, inspect.isfunction):
                if not method_name.startswith('_'):
                    func_info = extract_function_info(method)
                    methods.append(func_info)
            
            result[class_name] = methods
    
    return result

def build_system_prompt(schemas: Dict[str, List[FunctionInfo]], class_name: str) -> str:
    
    methods = schemas.get(class_name, [])
    
    method_descriptions = []
    for method in methods:
        param_info = []
        for param, ptype in method.params.items():
            required = " (required)" if param in method.required_params else " (optional)"
            param_info.append(f"{param}: {ptype}{required}")
        
        param_str = ", ".join(param_info) if param_info else "no parameters"
        method_descriptions.append(f"- {method.name}({param_str}) - {method.description}")
    
    methods_text = "\n".join(method_descriptions)
    
    prompt = f"""You are a command generator for the {class_name} class.

Available methods:
{methods_text}

Your task: Convert natural language requests into JSON commands ONLY if they are relevant to the available methods.

CRITICAL VALIDATION RULES:
1. ONLY process commands that can be accomplished using the available methods above
2. If a command is NOT related to the available methods, output an error JSON instead
3. Do NOT try to force unrelated commands into available methods

CRITICAL: You must output ONLY raw JSON with no markdown, no code blocks, no explanations.

For VALID commands, output format:
{{"commands": [{{"name": "method_name", "params": {{"param": value}}}}], "description": "What these commands do"}}

For INVALID commands, output format:
{{"error": "Command not related to available methods", "suggestion": "Try commands related to: [list key method names]"}}

Rules:
1. Use exact method names from the list above
2. Include only required parameters (you can infer sensible defaults)
3. Output MUST be valid JSON with double quotes
4. NO markdown code blocks (no ```json)
5. NO explanatory text before or after JSON
6. For sequences like "draw a square", break it into multiple commands
7. When "and" is used in arithmetic (e.g., "add X and Y"), treat it as a SINGLE command with two parameters, NOT two separate commands

Examples:
Input: "move forward 100"
Output: {{"commands": [{{"name": "forward", "params": {{"distance": 100}}}}], "description": "Move forward 100 units"}}

Input: "turn left"
Output: {{"commands": [{{"name": "left", "params": {{"angle": 90}}}}], "description": "Turn left 90 degrees"}}

Input: "add 2 and 3"
Output: {{"commands": [{{"name": "add", "params": {{"a": 2, "b": 3}}}}], "description": "Add 2 and 3"}}

Input: "multiply 5 and 7"
Output: {{"commands": [{{"name": "multiply", "params": {{"a": 5, "b": 7}}}}], "description": "Multiply 5 and 7"}}

Input: "turn on the air conditioner"
Output: {{"error": "Command not related to available methods", "suggestion": "Try commands related to: forward, backward, left, right, circle, color, goto"}}

Input: "draw a red square"
Output: {{"commands": [{{"name": "color", "params": {{"color_name": "red"}}}}, {{"name": "forward", "params": {{"distance": 100}}}}, {{"name": "right", "params": {{"angle": 90}}}}, {{"name": "forward", "params": {{"distance": 100}}}}, {{"name": "right", "params": {{"angle": 90}}}}, {{"name": "forward", "params": {{"distance": 100}}}}, {{"name": "right", "params": {{"angle": 90}}}}, {{"name": "forward", "params": {{"distance": 100}}}}], "description": "Draw a red square"}}
"""
    
    return prompt

class Command(BaseModel):
    name: str
    params: Dict[str, Any] = Field(default_factory=dict)

class CommandSequence(BaseModel):
    commands: List[Command]
    description: str

async def convert_text_to_commands_async(agent: Agent, text: str) -> CommandSequence:
    """Convert natural language to commands using AI"""
    result = await agent.run(text)
    response_text = str(result.data if hasattr(result, 'data') else result)
    
    print(f"Raw LLM response: {response_text[:200]}...")
    json_str = extract_json_string(response_text)
    
    print(f"Extracted JSON: {json_str}")
    
    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        print(f"Problematic JSON: {json_str}")
        raise

    if 'error' in parsed:
        print(f"\n{parsed['error']}")
        if 'suggestion' in parsed:
            print(f"{parsed['suggestion']}")
        return CommandSequence(
            commands=[],
            description=f"Invalid command: {text}"
        )

    commands = [Command(**cmd) for cmd in parsed.get('commands', [])]

    return CommandSequence(
        commands=commands,
        description=parsed.get('description', text)
    )

def convert_text_to_commands(agent: Agent, text: str) -> CommandSequence:
    try:
        return asyncio.run(convert_text_to_commands_async(agent, text))
    except Exception as e:
        print(f"Error converting text: {e}")
        return CommandSequence(commands=[], description=f"Error: {e}")

class NaturalLanguageInterface:

    def __init__(self, python_file: str, class_name: str, model: str = "anthropic:claude-3-haiku-20240307"):
        self.python_file = python_file
        self.class_name = class_name

        print(f" Analyzing {python_file}...")
        self.schemas = analyze_python_file(python_file)

        if class_name not in self.schemas:
            raise ValueError(f"Class '{class_name}' not found in {python_file}")

        print(f" Building AI prompt for {class_name}...")
        system_prompt = build_system_prompt(self.schemas, class_name)

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables. Please add it to your .env file.")

        self.agent = Agent(model, system_prompt=system_prompt)

        self._synonym_map = self._build_synonym_map(model)
        self._method_keyword_data = self._prepare_method_keywords()

        print(f"Interface ready! Found {len(self.schemas[class_name])} methods\n")

    def _is_command_valid(self, text: str) -> bool:
        text_lower = text.lower()
        command_tokens = set(self._tokenize_text(text_lower))
        normalized_text = text_lower.replace('_', ' ')

        method_tokens = self._method_keyword_data['tokens']
        token_overlap = command_tokens.intersection(method_tokens)

        phrase_matches = {
            phrase for phrase in self._method_keyword_data['phrases']
            if phrase in normalized_text
        }

        print(f"Debug: Command words: {command_tokens}")
        print(f"Debug: Method tokens: {sorted(method_tokens)}")
        print(f"Debug: Token overlap: {token_overlap}")
        print(f"Debug: Phrase matches: {phrase_matches}")

        return bool(token_overlap or phrase_matches)

    def _build_synonym_map(self, model: str) -> Dict[str, List[str]]:
        methods = self.schemas.get(self.class_name, [])
        if not methods:
            return {}

        synonym_agent = Agent(model, system_prompt=SYNONYM_SYSTEM_PROMPT)
        method_lines = []
        for method in methods:
            description = method.description or ""
            method_lines.append(
                f"- {method.name}: {description if description else 'no description provided'}"
            )

        prompt = (
            "Provide synonyms and common user phrasings for these methods in a retail bank account context.\n"
            + "\n".join(method_lines)
            + "\n\nRemember: respond with JSON only."
        )

        try:
            result = asyncio.run(synonym_agent.run(prompt))
            response_text = str(result.data if hasattr(result, 'data') else result)
            json_str = extract_json_string(response_text)
            parsed = json.loads(json_str)
            synonym_data = parsed.get('synonyms', {})
        except Exception as exc:
            print(f"Synonym expansion unavailable ({exc}). Falling back to literal matching.")
            return {}

        normalized: Dict[str, List[str]] = {}
        for method in methods:
            key = method.name.lower()
            candidates = []
            for lookup in {method.name, key, method.name.replace('_', ' ')}:
                maybe = synonym_data.get(lookup)
                if maybe:
                    candidates.extend(maybe)
            cleaned = []
            for synonym in candidates:
                if not isinstance(synonym, str):
                    continue
                synonym_text = synonym.strip().lower()
                if not synonym_text:
                    continue
                cleaned.append(synonym_text)
            if not cleaned:
                cleaned.append(key.replace('_', ' '))
            normalized[key] = sorted(set(cleaned))

        print(f"Synonym hints loaded: {normalized}")
        return normalized

    def _prepare_method_keywords(self) -> Dict[str, set]:
        tokens = set()
        phrases = set()

        for method in self.schemas.get(self.class_name, []):
            name_phrase = method.name.lower().replace('_', ' ')
            tokens.update(self._tokenize_text(name_phrase))
            if ' ' in name_phrase:
                phrases.add(name_phrase)

            if method.description:
                tokens.update(self._tokenize_text(method.description))

            if method.params:
                tokens.update(self._tokenize_text(' '.join(method.params.keys())))

            synonyms = self._synonym_map.get(method.name.lower(), [])
            for synonym in synonyms:
                synonym_phrase = synonym.replace('_', ' ')
                tokens.update(self._tokenize_text(synonym_phrase))
                if ' ' in synonym_phrase:
                    phrases.add(synonym_phrase)

        return {'tokens': tokens, 'phrases': phrases}

    @staticmethod
    def _tokenize_text(text: str) -> List[str]:
        return [token for token in re.split(r"[^a-z0-9']+", text.lower()) if token]

    def process(self, text: str) -> CommandSequence:
        if not self._is_command_valid(text):
            print(f"\nInvalid command: '{text}'")
            print(f"This command is not related to available {self.class_name} methods.")
            print("\nAvailable methods:")
            for method in self.schemas[self.class_name]:
                print(f"  • {method.name} - {method.description}")

            return CommandSequence(
                commands=[],
                description=f"Invalid command: '{text}' is not related to {self.class_name} methods"
            )

        return convert_text_to_commands(self.agent, text)
    
    def show_available_methods(self):
        print(f"\nAvailable methods in {self.class_name}:")
        for method in self.schemas[self.class_name]:
            params = ', '.join(f"{p}:{t}" for p, t in method.params.items())
            print(f"  • {method.name}({params})")
            print(f"    {method.description}")


if __name__ == "__main__":
    interface = NaturalLanguageInterface(
        python_file="./source_kbs/calculator.py",
        class_name="Calculator",
    )
    
    interface.show_available_methods()
    
    # test_cases = [
    #     "move forward 100 pixels",
    #     "turn left 90 degrees",
    #     "draw a red square with side length 50",
    #     "go to position 100, 100 then draw a circle",
    # ]
    # test_cases = [
    #     "Draw a red circle with radius ten",
    #     "Move forward one hundred steps and turn ninety degrees to the left",
    #     "Turn on the air conditioner and turn off the TV"
    # ]
    # test_cases = [
    #     "turn on the air conditioner",
    #     "set the temperature to 22 degrees",
    #     "turn off the TV",
    #     "open bank account with $5000",
    # ]
    test_cases = [
            "add 2 and 3",
            "add 2 and 3 then multiply with 5",
            "multiply 4 and 7",
            "subtract 2 from 5 then add 3 and 4"
    ]

    print("\nTesting Natural Language Commands")
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n[Test {i}] Input: '{text}'")
        
        commands = interface.process(text)
        
        print(f"Description: {commands.description}")
        print("Commands:")
        for j, cmd in enumerate(commands.commands, 1):
            params_str = ', '.join(f"{k}={v}" for k, v in cmd.params.items())
            print(f"  {j}. {cmd.name}({params_str})")
        
        import time
        time.sleep(1)
