from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


# --- DB dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 🔐 PRIVATE: current user profile
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "strava_connected": bool(current_user.strava_access_token),
        "created_at": current_user.created_at,
    }


# 🌍 PUBLIC: get user by id (limited info)
@router.get("/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        # ❗ Nada sensible aquí
    }
