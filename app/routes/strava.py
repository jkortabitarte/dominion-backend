from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os
import requests

from app.dependencies.auth import get_current_user
from app.database import SessionLocal
from app.models import User

from app.utils.strava_import import process_strava_activity
from datetime import datetime

router = APIRouter(prefix="/strava", tags=["strava"])

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_REDIRECT_URI = os.getenv("STRAVA_REDIRECT_URI")
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "https://jkortabitarte.github.io/dominion-map"
)


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
    return {"auth_url": url}


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

    # ✅ REDIRECT AL PERFIL
    return RedirectResponse(
        url=f"{FRONTEND_URL}/profile.html?strava=connected"
    )

# --- Step 3: Import activities ---
@router.post("/import")
def import_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.strava_access_token:
        raise HTTPException(
            status_code=400,
            detail="Strava not connected",
        )
    try:

      headers = {
          "Authorization": f"Bearer {current_user.strava_access_token}"
      }

      res = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers=headers,
        params={
            "per_page": 50,
            "page": 1,
        },
      )

      if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Strava API error")

      activities = res.json()

      imported = 0
      skipped = 0

      for act in activities:
        ok = process_strava_activity(db, current_user, act)
        if ok:
            imported += 1
        else:
            skipped += 1

      db.commit()

      return {
        "imported": imported,
        "skipped": skipped,
        "total_seen": len(activities),
      }
    except Exception as e:
        print("❌ Strava import error:", e)
        raise HTTPException(
            status_code=500,
            detail="Internal Strava import error",
        )

@router.post("/import/all")
def import_all_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    page = 1
    imported = 0

    while True:
        res = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={
                "Authorization": f"Bearer {current_user.strava_access_token}"
            },
            params={
                "per_page": 50,
                "page": page,
            },
        )

        activities = res.json()
        if not activities:
            break

        for a in activities:
            polyline = a.get("map", {}).get("summary_polyline")
            if not polyline:
                continue

            exists = db.query(Activity).filter(
                Activity.strava_activity_id == a["id"]
            ).first()

            if exists:
                continue

            activity = Activity(
                user_id=current_user.id,
                strava_activity_id=a["id"],
                polyline=polyline,
            )
            db.add(activity)

            hexes = polyline_to_h3(polyline)
            for hex_id in hexes:
                influence = db.query(TerritoryInfluence).filter_by(
                    territory_id=hex_id,
                    user_id=current_user.id,
                ).first()

                if influence:
                    influence.influence += 1
                else:
                    db.add(TerritoryInfluence(
                        territory_id=hex_id,
                        user_id=current_user.id,
                        influence=1,
                    ))

            imported += 1

        db.commit()
        page += 1

    return {
        "status": "ok",
        "imported": imported,
    }
