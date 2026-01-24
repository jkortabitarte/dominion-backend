from fastapi import FastAPI

from app.create_tables_endpoint import router as init_db_router
app.include_router(init_db_router)
app = FastAPI()

@app.get("/")
def root():
    return {"status": "Dominion backend is running"}
