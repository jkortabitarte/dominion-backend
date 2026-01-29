import os
import requests
from datetime import datetime

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")


def ensure_valid_strava_token(user, db):
    if not user.strava_expires_at:
        return

    now = int(datetime.utcnow().timestamp())

    # ⏰ token aún válido
    if user.strava_expires_at > now + 60:
        return

    # 🔁 refrescar token
    res = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": user.strava_refresh_token,
        },
    ).json()

    if "access_token" not in res:
        raise Exception("Failed to refresh Strava token")

    user.strava_access_token = res["access_token"]
    user.strava_refresh_token = res["refresh_token"]
    user.strava_expires_at = res["expires_at"]

    db.commit()
