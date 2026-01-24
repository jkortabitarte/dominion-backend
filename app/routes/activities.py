from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Activity, TerritoryInfluence
from app.utils.geo import polyline_to_h3
import uuid

router = APIRouter(prefix="/activities")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def fake_polyline_to_territory(polyline: str) -> str:
    # MVP: hash simple → luego H3
    return str(abs(hash(polyline)) % 1000)

@router.post("/")
def create_activity(user_id: str, polyline: str, db: Session = Depends(get_db)):
    activity = Activity(
        user_id=user_id,
        polyline=polyline,
    )
    db.add(activity)

    territory_id = fake_polyline_to_territory(polyline)

    influence = (
        db.query(TerritoryInfluence)
        .filter_by(territory_id=territory_id, user_id=user_id)
        .first()
    )

    if influence:
        influence.influence += 1
    else:
        influence = TerritoryInfluence(
            territory_id=territory_id,
            user_id=user_id,
            influence=1,
        )
        db.add(influence)

    db.commit()
    return {
        "activity_id": activity.id,
        "territory_id": territory_id,
        "influence": influence.influence,
    }
