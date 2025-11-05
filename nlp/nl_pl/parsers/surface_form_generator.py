import re
from typing import Set
from ..dynamic_config import DynamicConfig


class SurfaceFormGenerator:
    @staticmethod
    def generate_forms(method_info, config: DynamicConfig = None) -> Set[str]:
        forms = set()
        forms.update(SurfaceFormGenerator._from_method_name(method_info.name))

        if method_info.docstring:
            forms.update(SurfaceFormGenerator._from_docstring(method_info.docstring))

        if method_info.is_query:
            forms.update(SurfaceFormGenerator._add_query_variants(method_info.name, forms, config))

        expanded_forms = set()
        for form in forms:
            expanded_forms.update(SurfaceFormGenerator._generate_variants(form))
        forms.update(expanded_forms)

        return forms

    @staticmethod
    def _from_method_name(method_name: str) -> Set[str]:
        forms = set()
        tokens = method_name.split('_')
        readable = ' '.join(tokens)
        forms.add(readable)

        for i in range(1, len(tokens) + 1):
            for j in range(len(tokens) - i + 1):
                phrase = ' '.join(tokens[j:j+i])
                if len(phrase) > 2:
                    forms.add(phrase)

        return forms

    @staticmethod
    def _add_query_variants(method_name: str, existing_forms: Set[str], config: DynamicConfig = None) -> Set[str]:
        variants = set()
        
        if config:
            query_verbs = config.get_query_verbs()
            query_prefixes = config.get_query_method_prefixes()
        else:
            query_verbs = ['check', 'show', 'display', 'view', 'see', 'find', 'lookup']
            query_prefixes = ('get_', 'is_', 'has_', 'are_', 'count_', 'list_', 'show_')
        
        method_lower = method_name.lower()

        for prefix in query_prefixes:
            if method_lower.startswith(prefix):
                subject = method_name[len(prefix):]
                subject_readable = subject.replace('_', ' ')
                for verb in query_verbs:
                    variants.add(f"{verb} {subject_readable}")
                break

        return variants

    @staticmethod
    def _from_docstring(docstring: str) -> Set[str]:
        forms = set()
        sentences = re.split(r'[.!?]', docstring.lower())

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                for prefix in ['this method', 'this function', 'will', 'can', 'should']:
                    sentence = sentence.replace(prefix, '').strip()
                if len(sentence.split()) <= 6:
                    forms.add(sentence)

            question_patterns = [
                r'(what (?:is|are) (?:the |my )?[\w\s]+)',
                r'(how (?:much|many) [\w\s]+)',
                r'(check [\w\s]+)',
                r'(get [\w\s]+)',
                r'(show [\w\s]+)',
            ]

            for pattern in question_patterns:
                matches = re.findall(pattern, sentence)
                for match in matches:
                    if len(match.split()) <= 6:
                        forms.add(match.strip())

        return forms

    @staticmethod
    def _generate_variants(phrase: str) -> Set[str]:
        variants = {phrase}
        transformations = [
            (r'(\w+)ing\b', r'\1'),
            (r'\b(\w{3,})s\b', r'\1'),
            (r'(\w+)ed\b', r'\1'),
            (r'\b(turn|raise|lower|check|show|get)\b', r'\1ing'),
            (r'\b(turn|raise|lower|check|show)\b', r'\1ed'),
        ]

        for pattern, replacement in transformations:
            variant = re.sub(pattern, replacement, phrase)
            if variant != phrase:
                variants.add(variant)

        return variants
