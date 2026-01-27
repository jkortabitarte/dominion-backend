from fastapi import APIRouter, HTTPException, Query, Request
from app.database import SessionLocal
from app.models import User, Activity, TerritoryInfluence
from app.utils.geo import polyline_to_h3
import os
import requests
import time

router = APIRouter(prefix="/strava", tags=["strava-webhook"])

STRAVA_VERIFY_TOKEN = os.getenv("STRAVA_VERIFY_TOKEN")
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")


# 🔐 1) Webhook verification (GET)
@router.get("/webhook")
@router.get("/webhook/")
def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
):
    if hub_verify_token != STRAVA_VERIFY_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid verify token")

    return {"hub.challenge": hub_challenge}


# 📩 2) Receive events (POST)
@router.post("/webhook")
@router.post("/webhook/")
async def receive_event(payload: dict):
    if payload.get("object_type") != "activity":
        return {"status": "ignored"}

    if payload.get("aspect_type") != "create":
        return {"status": "ignored"}

    athlete_id = payload["owner_id"]
    activity_id = payload["object_id"]

    db = SessionLocal()

    user = db.query(User).filter(
        User.strava_athlete_id == athlete_id
    ).first()

    if not user:
        return {"status": "user not found"}

    # 🔄 Refresh token if needed
    if user.strava_expires_at < int(time.time()):
        refresh = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": STRAVA_CLIENT_ID,
                "client_secret": STRAVA_CLIENT_SECRET,
                "grant_type": "refresh_token",
                "refresh_token": user.strava_refresh_token,
            },
        ).json()

        user.strava_access_token = refresh["access_token"]
        user.strava_refresh_token = refresh["refresh_token"]
        user.strava_expires_at = refresh["expires_at"]
        db.commit()

    # 📥 Get full activity
    res = requests.get(
        f"https://www.strava.com/api/v3/activities/{activity_id}",
        headers={
            "Authorization": f"Bearer {user.strava_access_token}"
        },
    )

    activity_data = res.json()

    polyline = activity_data.get("map", {}).get("summary_polyline")
    if not polyline:
        return {"status": "no polyline"}

    # 💾 Save activity
    activity = Activity(
        user_id=user.id,
        polyline=polyline,
    )
    db.add(activity)

    # 🌍 Territories
    hexes = polyline_to_h3(polyline)

    for hex_id in hexes:
        influence = db.query(TerritoryInfluence).filter_by(
            territory_id=hex_id,
            user_id=user.id,
        ).first()

        if influence:
            influence.influence += 1
        else:
            db.add(TerritoryInfluence(
                territory_id=hex_id,
                user_id=user.id,
                influence=1,
            ))

    db.commit()

    return {"status": "activity imported"}
