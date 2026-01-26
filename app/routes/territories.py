from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import SessionLocal
from app.models import TerritoryInfluence

router = APIRouter(prefix="/territories", tags=["territories"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def get_territories(db: Session = Depends(get_db)):
    rows = (
        db.query(
            TerritoryInfluence.territory_id,
            TerritoryInfluence.user_id,
            TerritoryInfluence.influence,
        )
        .order_by(
            TerritoryInfluence.territory_id,
            TerritoryInfluence.influence.desc(),
        )
        .all()
    )

    territories = {}
    for r in rows:
        if r.territory_id not in territories:
            territories[r.territory_id] = {
                "territory_id": r.territory_id,
                "owner": r.user_id,
                "influence": r.influence,
            }

    return list(territories.values())
