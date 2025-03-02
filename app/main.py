from fastapi import FastAPI
from endpoints import leads

app = FastAPI()

app.include_router(leads.router) # Include the leads router

@app.get("/")
async def root():
    return {"message": "HomeWiz Backend API is running"}