"""
Web UI for AgentPress Enhancement
"""
from fastapi import FastAPI

app = FastAPI(title="AgentPress Enhanced UI")

@app.get("/")
async def root():
    return {"message": "AgentPress Enhanced Web UI"}