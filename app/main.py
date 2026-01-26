from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.routes import activities, users, territories, auth, strava, strava_webhook

app = FastAPI()

# 🌍 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jkortabitarte.github.io",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧱 Create tables (DEV ONLY)
Base.metadata.create_all(bind=engine)

# 🚏 Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(activities.router)
app.include_router(territories.router)
app.include_router(strava.router)
app.include_router(strava_webhook.router)


@app.get("/")
def root():
    return {"status": "Dominion backend is running"}
