from fastapi import APIRouter
from app.database import engine, Base
from app.models import User, Activity, TerritoryInfluence

router = APIRouter()

@router.get("/init-db")
def init_db():
    Base.metadata.create_all(bind=engine)
    return {"status": "Tables created successfully!"}
