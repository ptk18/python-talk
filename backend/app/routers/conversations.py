from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Conversation, User

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.post("/{user_id}")
def create_conversation(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    conv = Conversation(user_id=user_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("/{user_id}")
def get_conversations(user_id: int, db: Session = Depends(get_db)):
    return db.query(Conversation).filter(Conversation.user_id == user_id).all()
