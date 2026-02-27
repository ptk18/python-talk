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


def load_turtle_domain_code() -> str:
    if not TURTLE_DOMAIN_PATH.exists():
        raise FileNotFoundError(f"Turtle domain file not found at {TURTLE_DOMAIN_PATH}")
    return TURTLE_DOMAIN_PATH.read_text(encoding="utf-8")


def initialize_turtle_session(conversation_id: int, domain_code: str):
    session_dir = BASE_EXEC_DIR / f"session_{conversation_id}"
    session_dir.mkdir(parents=True, exist_ok=True)

    # The domain file must be named exactly convo.file_name (we use turtle_app.py)
    (session_dir / "turtle_app.py").write_text(domain_code, encoding="utf-8")

    # Runner for your codespace/NLP pipeline (obj.<method> prints)
    (session_dir / "runner.py").write_text(
        "from turtle_app import TurtleApp\n\nobj = TurtleApp()\n\n",
        encoding="utf-8"
    )

    # Pending follow-up state for parser
    (session_dir / "state.json").write_text(json.dumps({}, indent=2), encoding="utf-8")


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

    if file_name == "turtle_app.py":
        (session_dir / "runner.py").write_text(
            "import turtle\n\n"
            "t = turtle.Turtle()\n\n",
            encoding="utf-8"
        )
        (session_dir / "state.json").write_text(
            json.dumps({"active_object": "t", "pending": None}, indent=2),
            encoding="utf-8"
        )
        return

    # normal upload
    module_name = file_name.replace(".py", "")

    # find first class name in uploaded code
    tree = ast.parse(code)
    class_name = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            break

    if not class_name:
        # fallback (still allow file, but runner won't work)
        class_name = "None"

    # default constructor args
    state = {
        "active_object": "obj",
        "pending": None,
        "constructor_args": ["Demo User"],
        "constructor_kwargs": {},
    }
    (session_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    args_str = ", ".join([repr(x) for x in state["constructor_args"]])  # ["Demo User"] -> 'Demo User'

    (session_dir / "runner.py").write_text(
        f"from {module_name} import {class_name}\n\n"
        f"obj = {class_name}({args_str})\n",
        encoding="utf-8"
    )

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
