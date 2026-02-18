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

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.post("/{user_id}", response_model=ConversationResponse)
def create_conversation(user_id: int, convo: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation with title + uploaded code or imported library"""

    # Handle turtle app type - generate default code
    if convo.app_type.value == "turtle":
        code = convo.code or """import turtle

t = turtle.Turtle()
"""
        file_name = convo.file_name or "turtle_app.py"
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
    return db_convo


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
    BASE_EXEC_DIR = os.path.join(os.path.dirname(__file__), "..", "executions")
    session_dir = os.path.join(BASE_EXEC_DIR, f"session_{conversation_id}")

    if os.path.exists(session_dir):
        try:
            shutil.rmtree(session_dir)
        except Exception as e:
            print(f"Warning: Failed to delete session directory {session_dir}: {e}")

    db.delete(convo)
    db.commit()
    return {"message": "Conversation deleted successfully"}
