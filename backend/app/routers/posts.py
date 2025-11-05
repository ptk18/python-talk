from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.models.models import Post
from app.models.schemas import PostCreate, PostResponse

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    """Create a new post"""
    db_post = Post(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


@router.get("/", response_model=List[PostResponse])
def get_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all posts with pagination"""
    posts = db.query(Post).offset(skip).limit(limit).all()
    return posts


@router.get("/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific post by ID"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post


@router.put("/{post_id}", response_model=PostResponse)
def update_post(post_id: int, post_update: PostCreate, db: Session = Depends(get_db)):
    """Update a post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    for field, value in post_update.dict().items():
        setattr(post, field, value)
    
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    """Delete a post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    db.delete(post)
    db.commit()
    return None
