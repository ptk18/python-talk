from typing import List, Dict, Tuple, Optional
import json
import os


class HFSemanticMatcher:
    def __init__(self, hf_token: Optional[str] = None):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        if hf_token is None:
            hf_token = os.environ.get('HUGGINGFACE_TOKEN') or os.environ.get('HF_TOKEN')

        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("requests library required")

        self.api_url = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"
        self.hf_token = hf_token

    def get_similarity_scores(self, query: str, candidates: List[str]) -> List[float]:
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {"inputs": {"source_sentence": query, "sentences": candidates}}
        response = self.requests.post(self.api_url, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            error_msg = response.text
            try:
                error_msg = response.json().get('error', response.text)
            except:
                pass
            raise Exception(f"HuggingFace API error {response.status_code}: {error_msg}")

        return response.json()


    def find_best_match(self, command: str, methods: List[Dict], top_k: int = 3, min_confidence: float = 0.3) -> List[Tuple[Dict, float]]:
        if not methods:
            return []

        method_texts = []
        for method in methods:
            method_name = method.get('name', '').replace('_', ' ')
            description = method.get('description', '')
            text = f"{method_name}"
            if description:
                text += f" - {description}"
            method_texts.append(text)

        try:
            scores = self.get_similarity_scores(command, method_texts)
        except Exception as e:
            return []

        command_lower = command.lower()
        boosted_scores = []
        for i, method in enumerate(methods):
            score = scores[i]
            method_name = method.get('name', '').replace('_', ' ').lower()

            if method_name in command_lower:
                score = min(1.0, score + 0.15)  

            boosted_scores.append(score)

        matches = []
        for i, method in enumerate(methods):
            if boosted_scores[i] >= min_confidence:
                matches.append((method, boosted_scores[i]))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]

    def match_with_fallback(self, command: str, methods: List[Dict], confidence_threshold: float = 0.5) -> Optional[Tuple[Dict, float]]:
        matches = self.find_best_match(command, methods, top_k=1, min_confidence=0.0)

        if not matches:
            return None

        method, confidence = matches[0]
        return (method, confidence)
