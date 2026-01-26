from sqlalchemy import Column, String, Integer, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy import ForeignKey
import uuid

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # conexiones externas
    # 🔴 STRAVA
    strava_athlete_id = Column(Integer, unique=True, nullable=True)
    strava_access_token = Column(String, nullable=True)
    strava_refresh_token = Column(String, nullable=True)
    strava_expires_at = Column(Integer, nullable=True)

    # strava_id = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Activity(Base):
    __tablename__ = "activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"))

    # 🔴 STRAVA
    strava_activity_id = Column(Integer, unique=True, index=True)

    polyline = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TerritoryInfluence(Base):
    __tablename__ = "territory_influence"
    territory_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    influence = Column(Float)

