"""
FastAPI server for the Support Ticket Triage Environment.
This server exposes the OpenEnv API endpoints for reset, step, and state.
"""

import os
import json
import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from env import SupportTicketEnv, SupportAction


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="Support Ticket Triage Environment",
    description="A real-world customer support ticket management environment for AI agents",
    version="1.0.0"
)

# Enable CORS for all origins (needed for HF Spaces)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize environment
env = SupportTicketEnv()


# ============================================================================
# Request/Response Models
# ============================================================================

class ResetRequest(BaseModel):
    task_id: Optional[str] = "categorize_ticket"


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        environment="support-ticket-triage",
        version="1.0.0"
    )


@app.post("/reset")
async def reset_environment(request: ResetRequest = ResetRequest()):
    """
    Reset the environment to initial state.
    
    Args:
        task_id: The task to run (categorize_ticket, prioritize_and_route, full_workflow)
    
    Returns:
        EnvResult with initial observation
    """
    try:
        result = await env.reset(request.task_id if request.task_id else "categorize_ticket")
        return JSONResponse(content=result, media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step")
async def step_environment(action: SupportAction):
    """
    Execute an action in the environment.
    
    Args:
        action: The action to execute (SupportAction model)
    
    Returns:
        EnvResult with observation, reward, done flag, and info
    """
    try:
        result = await env.step(action)
        return JSONResponse(content=result, media_type="application/json")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state")
async def get_state():
    """
    Get the current environment state.
    
    Returns:
        Current SupportState
    """
    state = env.get_state()
    if state is None:
        raise HTTPException(status_code=404, detail="Environment not initialized. Call /reset first.")
    return JSONResponse(content=state.model_dump())


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Support Ticket Triage Environment",
        "version": "1.0.0",
        "description": "A real-world customer support ticket management environment for AI agents",
        "endpoints": {
            "health": "GET /health",
            "reset": "POST /reset",
            "step": "POST /step",
            "state": "GET /state"
        },
        "tasks": [
            {
                "id": "categorize_ticket",
                "name": "Ticket Categorization (Easy)",
                "description": "Categorize incoming support tickets into correct department and priority"
            },
            {
                "id": "prioritize_and_route",
                "name": "Prioritize and Route (Medium)",
                "description": "Handle multiple tickets by prioritizing and routing to appropriate teams"
            },
            {
                "id": "full_workflow",
                "name": "Full Support Workflow (Hard)",
                "description": "Complete end-to-end support workflow with responses and escalations"
            }
        ]
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting Support Ticket Triage Environment server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)