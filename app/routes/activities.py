from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import SessionLocal
from app.models import Activity, TerritoryInfluence, User
from app.utils.geo import polyline_to_h3

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
    user_id: str
    polyline: str


@router.post("/")
def create_activity(
    data: ActivityCreate,
    db: Session = Depends(get_db),
):
    # 1️⃣ Check user exists
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2️⃣ Create activity
    activity = Activity(
        user_id=data.user_id,
        polyline=data.polyline,
    )
    db.add(activity)

    # 3️⃣ Convert polyline → H3
    try:
        hexes = polyline_to_h3(data.polyline)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid polyline: {e}")

    if not hexes:
        raise HTTPException(status_code=400, detail="No territories generated")

    # 4️⃣ Update influence
    for hex_id in hexes:
        influence = (
            db.query(TerritoryInfluence)
            .filter_by(
                territory_id=hex_id,
                user_id=data.user_id,
            )
            .first()
        )

        if influence:
            influence.influence += 1
        else:
            influence = TerritoryInfluence(
                territory_id=hex_id,
                user_id=data.user_id,
                influence=1,
            )
            db.add(influence)

    db.commit()

    return {
        "activity_id": activity.id,
        "hexes_affected": len(hexes),
    }
