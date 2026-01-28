from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.models import Favorite
from app.models.schemas import FavoriteResponse, FavoriteToggleRequest, FavoriteToggleResponse

router = APIRouter(prefix="/favorites", tags=["Favorites"])


@router.get("/{user_id}", response_model=List[FavoriteResponse])
def get_user_favorites(user_id: int, db: Session = Depends(get_db)):
    """Get all favorites for a user"""
    return db.query(Favorite).filter(Favorite.user_id == user_id).all()


@router.post("/{user_id}/toggle", response_model=FavoriteToggleResponse)
def toggle_favorite(user_id: int, request: FavoriteToggleRequest, db: Session = Depends(get_db)):
    """Toggle favorite status for an app"""
    if not request.conversation_id and not request.builtin_app_id:
        raise HTTPException(status_code=400, detail="Either conversation_id or builtin_app_id is required")

    # Build query to find existing favorite
    query = db.query(Favorite).filter(Favorite.user_id == user_id)

    if request.conversation_id:
        query = query.filter(Favorite.conversation_id == request.conversation_id)
    else:
        query = query.filter(Favorite.builtin_app_id == request.builtin_app_id)

    existing = query.first()

    if existing:
        # Remove favorite
        db.delete(existing)
        db.commit()
        return FavoriteToggleResponse(is_favorited=False, message="Removed from favorites")
    else:
        # Add favorite
        new_favorite = Favorite(
            user_id=user_id,
            conversation_id=request.conversation_id,
            builtin_app_id=request.builtin_app_id
        )
        db.add(new_favorite)
        db.commit()
        return FavoriteToggleResponse(is_favorited=True, message="Added to favorites")
