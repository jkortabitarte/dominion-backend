from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import TerritoryInfluence

router = APIRouter(prefix="/territories", tags=["territories"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_territories(db: Session = Depends(get_db)):
    territories = (
        db.query(TerritoryInfluence)
        .all()
    )

    return [
        {
            "territory_id": t.territory_id,
            "user_id": t.user_id,
            "influence": t.influence,
        }
        for t in territories
    ]
