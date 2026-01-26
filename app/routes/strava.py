from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os
import requests

from app.dependencies.auth import get_current_user
from app.database import SessionLocal
from app.models import User

router = APIRouter(prefix="/strava", tags=["strava"])

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI")


# --- DB dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Step 1: Redirect user to Strava ---
@router.get("/connect")
def connect_strava(current_user: User = Depends(get_current_user)):
    url = (
        "https://www.strava.com/oauth/authorize"
        f"?client_id={STRAVA_CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={STRAVA_REDIRECT_URI}"
        "&approval_prompt=force"
        "&scope=activity:read_all"
        f"&state={current_user.id}"
    )
    return RedirectResponse(url)


# --- Step 2: Strava callback ---
@router.get("/callback")
def strava_callback(code: str, state: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == state).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid state")

    token_res = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        },
    ).json()

    if "access_token" not in token_res:
        raise HTTPException(
            status_code=400,
            detail="Failed to authenticate with Strava",
        )

    user.strava_athlete_id = token_res["athlete"]["id"]
    user.strava_access_token = token_res["access_token"]
    user.strava_refresh_token = token_res["refresh_token"]
    user.strava_expires_at = token_res["expires_at"]

    db.commit()

    return {
        "status": "Strava connected",
        "athlete_id": user.strava_athlete_id,
    }


# --- Step 3: Import activities (preview for now) ---
@router.post("/import")
def import_activities(
    current_user: User = Depends(get_current_user),
):
    if not current_user.strava_access_token:
        raise HTTPException(
            status_code=400,
            detail="Strava not connected",
        )

    headers = {
        "Authorization": f"Bearer {current_user.strava_access_token}"
    }

    res = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers=headers,
        params={"per_page": 50},
    )

    if res.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Failed to fetch activities from Strava",
        )

    activities = res.json()

    return {
        "imported": len(activities),
        "preview": activities[:2],
    }
