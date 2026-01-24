from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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


# --- Create activity and update territory influence ---
@router.post("/")
def create_activity(
    user_id: str,
    polyline: str,
    db: Session = Depends(get_db),
):
    # 1️⃣ Check user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2️⃣ Create activity
    activity = Activity(
        user_id=user_id,
        polyline=polyline,
    )
    db.add(activity)

    # 3️⃣ Convert polyline → H3 hexes
    try:
        hexes = polyline_to_h3(polyline)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid polyline")

    if not hexes:
        raise HTTPException(status_code=400, detail="No territories generated")

    # 4️⃣ Update influence per hex
    for hex_id in hexes:
        influence = (
            db.query(TerritoryInfluence)
            .filter(
                TerritoryInfluence.territory_id == hex_id,
                TerritoryInfluence.user_id == user_id,
            )
            .first()
        )

        if influence:
            influence.influence += 1
        else:
            influence = TerritoryInfluence(
                territory_id=hex_id,
                user_id=user_id,
                influence=1,
            )
            db.add(influence)

    # 5️⃣ Commit once
    db.commit()

    return {
        "activity_id": activity.id,
        "hexes_affected": len(hexes),
    }
