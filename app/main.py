from fastapi import FastAPI
from app.endpoints import (
    leads, rooms, tenants, buildings, operators, query,
    # New endpoints
    notifications, scheduling, maintenance, checklists, documents,
    messages, announcements, analytics
)

app = FastAPI()

# Existing routers
app.include_router(leads.router)
app.include_router(rooms.router)
app.include_router(tenants.router)
app.include_router(buildings.router)
app.include_router(operators.router)
app.include_router(query.router)

# New routers
app.include_router(notifications.router)
app.include_router(scheduling.router)
app.include_router(maintenance.router)
app.include_router(checklists.router)
app.include_router(documents.router)
app.include_router(messages.router)
app.include_router(announcements.router)
app.include_router(analytics.router)

@app.get("/")
async def root():
    return {"message": "HomeWiz Backend API is running"}