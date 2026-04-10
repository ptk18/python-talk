# backend/app/routers/codespace/conversations.py
import os
import shutil
import tempfile
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Conversation
from app.models.schemas import ConversationCreate, ConversationResponse, ConversationUpdate
import ast
import re

import ast
from pathlib import Path
import json

router = APIRouter(prefix="/conversations", tags=["Conversations"])

# This matches analyze_command.py (it uses parents[2] == backend/app)
BASE_EXEC_DIR = Path(__file__).resolve().parents[2] / "executions"
print("BASE_EXEC_DIR ", BASE_EXEC_DIR)

# backend/app/domains/turtle_app.py
APP_DIR = Path(__file__).resolve().parents[2]  # backend/app
print("APP_DIR ", APP_DIR)
TURTLE_DOMAIN_PATH = APP_DIR / "domains" / "turtle_app.py"

# backend/app/domains/smart_home_group.py
APP_DIR = Path(__file__).resolve().parents[2]  # backend/app
print("APP_DIR ", APP_DIR)
SMARTHOME_DOMAIN_PATH = APP_DIR / "domains" / "smart_home_group.py"


def load_turtle_domain_code() -> str:
    if not TURTLE_DOMAIN_PATH.exists():
        raise FileNotFoundError(f"Turtle domain file not found at {TURTLE_DOMAIN_PATH}")
    return TURTLE_DOMAIN_PATH.read_text(encoding="utf-8")

def load_smarthome_domain_code() -> str:
    if not SMARTHOME_DOMAIN_PATH.exists():
        raise FileNotFoundError(f"Turtle domain file not found at {SMARTHOME_DOMAIN_PATH}")
    return SMARTHOME_DOMAIN_PATH.read_text(encoding="utf-8")

def initialize_turtle_session(conversation_id: int, domain_code: str):
    session_dir = BASE_EXEC_DIR / f"session_{conversation_id}"
    session_dir.mkdir(parents=True, exist_ok=True)

    (session_dir / "turtle_app.py").write_text(domain_code, encoding="utf-8")

    # do NOT create obj
    (session_dir / "runner.py").write_text(
        "import turtle\n\n",
        encoding="utf-8"
    )

    # initialize turtle state
    (session_dir / "state.json").write_text(
        json.dumps({
        "active_object": None,
        "pending": None,
        "objects": {},
        "constructor_args": [],
        "constructor_kwargs": {}
    }, indent=2),
        encoding="utf-8"
    )

@router.post("/{user_id}", response_model=ConversationResponse)
def create_conversation(user_id: int, convo: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation with title + uploaded code or imported library"""
    
    if convo.app_type.value == "turtle":
        code = load_turtle_domain_code()
        file_name = "turtle_app.py"
    
    else:
        # Upload type requires code and file_name
        if not convo.code or not convo.file_name:
            raise HTTPException(status_code=400, detail="Upload apps require code and file_name")
        code = convo.code
        file_name = convo.file_name

    db_convo = Conversation(
        user_id=user_id,
        title=convo.title or "New App",
        file_name=file_name,
        code=code,
        app_type=convo.app_type.value,
        app_image=convo.app_image
    )
    db.add(db_convo)
    db.commit()
    db.refresh(db_convo)
    initialize_session(db_convo.id, file_name, code)
    return db_convo

def initialize_session(conversation_id: int, file_name: str, code: str):
    session_dir = BASE_EXEC_DIR / f"session_{conversation_id}"
    session_dir.mkdir(parents=True, exist_ok=True)

    (session_dir / file_name).write_text(code, encoding="utf-8")

    # -----------------------------
    # Turtle mode
    # -----------------------------
    if file_name == "turtle_app.py":
        (session_dir / "runner.py").write_text(
            "import turtle\n\n",
            encoding="utf-8"
        )
        (session_dir / "state.json").write_text(
            json.dumps(
                {
                    "active_object": None,
                    "pending": None,
                    "objects": {},
                    "constructor_args": [],
                    "constructor_kwargs": {}
                },
                indent=2
            ),
            encoding="utf-8"
        )
        return

    # -----------------------------
    # Non-turtle mode (NO auto object creation)
    # -----------------------------
    module_name = file_name.replace(".py", "")

    # find first class name in uploaded code (for reference only)
    try:
        tree = ast.parse(code)
    except Exception:
        tree = None

    class_name = None
    if tree:
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                break

    state = {
        "active_object": None,          # professor requirement: user creates objects
        "pending": None,
        "constructor_args": [],         # keep for later if you want followup for init
        "constructor_kwargs": {},
        "module_name": module_name,     # helpful for runner/imports
        "class_name": class_name,       # helpful for prompts / UI (optional)
        "objects": {},                  # optional: track many objects later
    }
    (session_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    # runner starts with imports only
    # (user commands will append object creation lines later)
    runner_lines = [
        # f"from {module_name} import {class_name}\n" if class_name else f"import {module_name}\n",
        f"from {module_name} import *\n" if class_name else f"import {module_name}\n",
        "\n",
    ]
    (session_dir / "runner.py").write_text("".join(runner_lines), encoding="utf-8")
@router.get("/{user_id}", response_model=List[ConversationResponse])
def get_conversations(user_id: int, db: Session = Depends(get_db)):
    """Get all conversations for a user"""
    return db.query(Conversation).filter(Conversation.user_id == user_id).all()

@router.get("/{conversation_id}/single", response_model=ConversationResponse)
def get_single_conversation(conversation_id: int, db: Session = Depends(get_db)):
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return convo

@router.put("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(conversation_id: int, update: ConversationUpdate, db: Session = Depends(get_db)):
    """Update conversation title and/or image"""
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if update.title is not None:
        convo.title = update.title
    if update.app_image is not None:
        convo.app_image = update.app_image

    db.commit()
    db.refresh(convo)
    return convo

@router.get("/{conversation_id}/available_methods")
def get_available_methods(conversation_id: int, db: Session = Depends(get_db)):
    """Extract and return all available methods from uploaded code (AST-based, no NLP)"""

    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not convo.code:
        raise HTTPException(status_code=400, detail="No code found in conversation")

    try:
        tree = ast.parse(convo.code)

        # Turtle apps: return flat method list with categories
        if convo.app_type.value == "turtle":
            # Parse comment-based category headers from raw source
            lines = convo.code.splitlines()
            category_at_line = {}
            current_category = "General"
            for i, line in enumerate(lines, start=1):
                stripped = line.strip()
                # Match category headers like "# Turtle management ..." but skip
                # separators (# ----, # ====) and non-category comments
                if (stripped.startswith("# ")
                        and not re.match(r'^#\s*[-=]+\s*$', stripped)
                        and re.search(r'[a-zA-Z]', stripped[2:])):
                    # Only use indented comments (inside class body) as categories
                    if line.startswith("    #"):
                        cat_text = stripped[2:].strip()
                        # Remove parenthetical notes like "(IMPORTANT: ...)"
                        paren_idx = cat_text.find("(")
                        if paren_idx > 0:
                            cat_text = cat_text[:paren_idx].strip()
                        current_category = cat_text
                category_at_line[i] = current_category

            methods = []
            for node in tree.body:
                if not isinstance(node, ast.ClassDef):
                    continue
                for item in node.body:
                    if not isinstance(item, ast.FunctionDef):
                        continue
                    if item.name.startswith("__") and item.name.endswith("__"):
                        continue
                    params = [arg.arg for arg in item.args.args[1:]]  # skip self
                    category = category_at_line.get(item.lineno, "General")
                    methods.append({
                        "name": item.name,
                        "params": params,
                        "category": category,
                        "docstring": ast.get_docstring(item)
                    })

            return {"success": True, "methods": methods}

        # Codespace apps: return methods grouped by class
        classes_info = {}

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                class_doc = ast.get_docstring(node)

                methods = []

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name.startswith("__") and item.name.endswith("__"):
                            continue

                        params = {}
                        required_params = []

                        for arg in item.args.args[1:]:  # skip self
                            params[arg.arg] = "Any"
                            required_params.append(arg.arg)

                        methods.append({
                            "name": item.name,
                            "parameters": params,
                            "required_parameters": required_params,
                            "return_type": None,
                            "docstring": ast.get_docstring(item)
                        })

                classes_info[class_name] = {
                    "docstring": class_doc,
                    "methods": methods
                }

        return {
            "success": True,
            "file_name": convo.file_name,
            "classes": classes_info,
            "total_classes": len(classes_info)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting methods: {str(e)}")

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete a conversation by ID and clean up associated session files"""
    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Clean up session directory
    session_dir = BASE_EXEC_DIR / f"session_{conversation_id}"

    if os.path.exists(session_dir):
        try:
            shutil.rmtree(session_dir)
        except Exception as e:
            print(f"Warning: Failed to delete session directory {session_dir}: {e}")

    db.delete(convo)
    db.commit()
    return {"message": "Conversation deleted successfully"}
