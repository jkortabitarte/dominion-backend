from fastapi import Depends, HTTPException, Request
from jose import jwt, JWTError
from app.models import User
from app.database import SessionLocal
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


def get_current_user(request: Request):
    auth = request.headers.get("Authorization")

    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
