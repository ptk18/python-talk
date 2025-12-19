"""
NLP v3 - Honest Pipeline with Transparent Scoring
Based on nlp_poc_honest.py with modular architecture
"""

from .main import HonestNLPPipeline, process_command
from .models import MethodInfo, MatchScore
from .catalog import extract_from_file, FileCatalog, ClassCatalog, MethodCatalog

__all__ = [
    'HonestNLPPipeline',
    'process_command',
    'MethodInfo',
    'MatchScore',
    'extract_from_file',
    'FileCatalog',
    'ClassCatalog',
    'MethodCatalog',
]
