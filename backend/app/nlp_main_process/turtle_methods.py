import nltk
from typing import List, Optional
from .models import MethodInfo
from .dictionary_lookup import get_synonyms, get_inflections
from ..nlp_v4.turtle_introspector import get_introspector

LOG_PREFIX = "[NLP]"

DECOMPOSITION_PATTERNS = {
    "penup": ("pen", None, "up"),
    "pendown": ("pen", None, "down"),
    "goto": ("go", None, "to"),
    "setpos": ("set", "position", None),
    "setposition": ("set", "position", None),
    "setx": ("set", "x", None),
    "sety": ("set", "y", None),
    "hideturtle": ("hide", "turtle", None),
    "showturtle": ("show", "turtle", None),
    "pencolor": ("pen", "color", None),
    "pensize": ("pen", "size", None),
    "fillcolor": ("fill", "color", None),
    "bgcolor": ("background", "color", None),
    "setheading": ("set", "heading", None),
    "begin_fill": ("begin", "fill", None),
    "end_fill": ("end", "fill", None),
    "clearstamp": ("clear", "stamp", None),
    "clearstamps": ("clear", "stamps", None),
}

PARTICLES = {"up", "down", "on", "off", "to"}
KNOWN_OBJECTS = {"turtle", "color", "size", "fill", "heading", "position", "stamp"}


def decompose_method_name(name: str) -> tuple:
    if name in DECOMPOSITION_PATTERNS:
        return DECOMPOSITION_PATTERNS[name]

    if "_" in name:
        parts = name.split("_", 1)
        return (parts[0], parts[1], None)

    for particle in PARTICLES:
        if name.endswith(particle) and len(name) > len(particle):
            return (name[:-len(particle)], None, particle)

    for obj in KNOWN_OBJECTS:
        if name.endswith(obj) and len(name) > len(obj):
            return (name[:-len(obj)], obj, None)

    return (name, None, None)


def extract_docstring_verb(docstring: str) -> Optional[str]:
    if not docstring:
        return None

    first_line = docstring.split('\n')[0].strip()
    if not first_line:
        return None

    try:
        tokens = nltk.word_tokenize(first_line)
        tagged = nltk.pos_tag(tokens)
        for word, tag in tagged:
            if tag.startswith('VB'):
                return word.lower()
    except Exception:
        pass

    return None


def infer_param_type(param_name: str, docstring: str) -> str:
    param_lower = param_name.lower()
    doc_lower = docstring.lower() if docstring else ""

    if f"{param_lower} --" in doc_lower or f"{param_lower}:" in doc_lower:
        if "string" in doc_lower or "str" in doc_lower:
            return "str"

    if param_lower in ("distance", "angle", "radius", "x", "y", "width", "size", "speed", "extent", "steps", "n"):
        return "int"
    if param_lower in ("color", "text", "arg", "s", "name"):
        return "str"

    return "int"


def get_turtle_methods() -> List[MethodInfo]:
    print(f"{LOG_PREFIX} Introspecting turtle.Turtle class...")
    introspector = get_introspector()
    introspector.introspect()
    print(f"{LOG_PREFIX} Found {len(introspector._detailed_methods)} methods (excluded {len(introspector._excluded_methods)} advanced/internal)")

    result = []
    for name, detail in introspector._detailed_methods.items():
        verb, obj, particle = decompose_method_name(name)

        verb_syns = list(get_synonyms(verb, "verb"))

        doc_verb = extract_docstring_verb(detail.docstring)
        if doc_verb and doc_verb != verb:
            verb_syns.append(doc_verb)
            verb_syns.extend(get_synonyms(doc_verb, "verb"))

        for alias in detail.aliases:
            if alias != name and alias != verb:
                verb_syns.append(alias)

        verb_syns = list(set(verb_syns))

        obj_syns = []
        obj_forms = []
        if obj:
            obj_syns = list(get_synonyms(obj, "noun"))
            obj_forms = get_inflections(obj, "noun")

        params = []
        for p in detail.params:
            params.append({
                "name": p,
                "type": infer_param_type(p, detail.docstring)
            })

        result.append(MethodInfo(
            name=name,
            verb=verb,
            verb_synonyms=verb_syns,
            verb_forms=get_inflections(verb, "verb"),
            object=obj,
            object_synonyms=obj_syns,
            object_forms=obj_forms,
            particle=particle,
            params=params
        ))

    # Show sample of synonyms for a few key methods
    sample_methods = ["forward", "left", "penup", "circle"]
    for m in result:
        if m.name in sample_methods:
            syns = m.verb_synonyms[:4] if m.verb_synonyms else []
            print(f"{LOG_PREFIX}   {m.name}: verb='{m.verb}' synonyms={syns}")

    return result
