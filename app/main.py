from fastapi import FastAPI
from app.endpoints import leads, rooms, tenants

app = FastAPI()

app.include_router(leads.router)
app.include_router(rooms.router)
app.include_router(tenants.router)


@app.get("/")
async def root():
    return {"message": "HomeWiz Backend API is running"}