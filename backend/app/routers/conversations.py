from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import tempfile
import os
from app.database.connection import get_db
from app.models.models import Conversation
from app.models.schemas import ConversationCreate, ConversationResponse
from app.nlp_v3.catalog import extract_from_file

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.post("/{user_id}", response_model=ConversationResponse)
def create_conversation(user_id: int, convo: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation with title + uploaded code"""
    db_convo = Conversation(
        user_id=user_id,
        title=convo.title or "New Conversation",
        file_name=convo.file_name,
        code=convo.code
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

@router.get("/{conversation_id}/available_methods")
def get_available_methods(conversation_id: int, db: Session = Depends(get_db)):
    """Extract and return all available methods from the conversation's uploaded code"""

    convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not convo.code:
        raise HTTPException(status_code=400, detail="No code found in conversation")

    try:
        # Create a temporary file with the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(convo.code)
            temp_file_path = temp_file.name

        try:
            # Extract catalog from the file
            catalog = extract_from_file(temp_file_path)

            all_methods = {}

            # Process each class in the catalog
            for class_name, class_info in catalog.classes.items():
                methods_list = []

                for method in class_info.methods:
                    methods_list.append({
                        "name": method.name,
                        "parameters": {
                            param_name: str(param_type)
                            for param_name, param_type in method.parameters.items()
                        },
                        "required_parameters": method.required_parameters,
                        "return_type": str(method.return_type) if method.return_type else None,
                        "docstring": method.docstring
                    })

                all_methods[class_name] = {
                    "docstring": class_info.docstring,
                    "methods": methods_list
                }

            return {
                "success": True,
                "file_name": convo.file_name,
                "classes": all_methods,
                "total_classes": len(all_methods)
            }

        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting methods: {str(e)}")

@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete a conversation by ID and clean up associated session files"""
    import shutil

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
