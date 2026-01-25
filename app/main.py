from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.root_path = ""

# 🌍 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jkortabitarte.github.io",
        "http://localhost:8000",  # por si pruebas en local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routes import activities, users, territories
app.include_router(territories.router)
app.include_router(users.router)
app.include_router(activities.router)


@app.get("/")
def root():
    return {"status": "Dominion backend is running"}
