# backend/app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.models import User
from app.models.schemas import UserCreate, UserResponse
from app.models import crud, models, schemas

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    return crud.create_user(db, username=user.username, password=user.password, gender=user.gender)


@router.get("/", response_model=List[UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users with pagination"""
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserCreate, db: Session = Depends(get_db)):
    """Update a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    for field, value in user_update.dict().items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    return None

@router.post("/login")
def login_user(data: dict, db: Session = Depends(get_db)):
    username = data.get("username")
    password = data.get("password")

    user = db.query(models.User).filter(models.User.username == username, models.User.password == password).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"id": user.id, "username": user.username, "gender": user.gender.value}
