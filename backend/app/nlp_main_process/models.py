from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class MatchType(Enum):
    EXACT = "exact"
    SYNONYM = "synonym"
    INFLECTION = "inflection"
    NONE = "none"


@dataclass
class WordInfo:
    original: str
    lemma: str
    pos: str
    synonyms: List[str] = field(default_factory=list)
    inflections: List[str] = field(default_factory=list)


@dataclass
class GrammarExtraction:
    verb: Optional[str] = None
    verb_synonyms: List[str] = field(default_factory=list)
    object: Optional[str] = None
    object_synonyms: List[str] = field(default_factory=list)
    particle: Optional[str] = None
    numbers: List[str] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)


@dataclass
class MethodInfo:
    name: str
    verb: str
    verb_synonyms: List[str] = field(default_factory=list)
    verb_forms: List[str] = field(default_factory=list)
    object: Optional[str] = None
    object_synonyms: List[str] = field(default_factory=list)
    object_forms: List[str] = field(default_factory=list)
    particle: Optional[str] = None
    params: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MatchResult:
    success: bool
    method: str = ""
    confidence: float = 0.0
    verb_match: MatchType = MatchType.NONE
    object_match: MatchType = MatchType.NONE
    particle_match: bool = False
    params: Dict[str, Any] = field(default_factory=dict)
    executable: str = ""
    error: Optional[str] = None
