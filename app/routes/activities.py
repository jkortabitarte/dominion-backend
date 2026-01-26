from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models import Activity, TerritoryInfluence, User
from app.utils.geo import polyline_to_h3
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/activities", tags=["activities"])


# --- DB dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Request schema ---
class ActivityCreate(BaseModel):
    polyline: str


@router.post("/")
def create_activity(
    data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 1️⃣ Create activity
    activity = Activity(
        user_id=current_user.id,
        polyline=data.polyline,
    )
    db.add(activity)

    # 2️⃣ Convert polyline → H3
    try:
        hexes = polyline_to_h3(data.polyline)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid polyline: {e}")

    if not hexes:
        raise HTTPException(status_code=400, detail="No territories generated")

    # 3️⃣ Update territory influence
    for hex_id in hexes:
        influence = (
            db.query(TerritoryInfluence)
            .filter_by(
                territory_id=hex_id,
                user_id=current_user.id,
            )
            .first()
        )

        if influence:
            influence.influence += 1
        else:
            influence = TerritoryInfluence(
                territory_id=hex_id,
                user_id=current_user.id,
                influence=1,
            )
            db.add(influence)

    # 4️⃣ Commit once
    db.commit()
    db.refresh(activity)

    return {
        "activity_id": activity.id,
        "hexes_affected": len(hexes),
    }


@router.get("/")
def list_activities(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Activity)
        .filter(Activity.user_id == current_user.id)
        .all()
    )
