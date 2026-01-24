from fastapi import FastAPI

app = FastAPI()

from app.routes import activities
app.include_router(activities.router)

@app.get("/")
def root():
    return {"status": "Dominion backend is running"}
