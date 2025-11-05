from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.models import Conversation
from app.models.schemas import ConversationCreate, ConversationResponse

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
