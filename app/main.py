from fastapi import FastAPI

app = FastAPI()

from app.routes import activities, users, territories
app.include_router(territories.router)
app.include_router(users.router)
app.include_router(activities.router)


@app.get("/")
def root():
    return {"status": "Dominion backend is running"}
