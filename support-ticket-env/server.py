"""
FastAPI server for the Support Ticket Triage Environment.
This server exposes the OpenEnv API endpoints for reset, step, and state.
"""

import os
import json
import uvicorn
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from env import (
    SupportTicketEnv,
    SupportAction,
    SupportObservation,
    SupportState,
    get_task_metadata,
)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


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


class GraderMetadata(BaseModel):
    id: str
    name: str
    description: str


class TaskMetadata(BaseModel):
    id: str
    name: str
    description: str
    difficulty: Optional[str] = None
    max_steps: Optional[int] = None
    success_threshold: Optional[float] = None
    graders: list[GraderMetadata] = []


class MetadataResponse(BaseModel):
    name: str
    description: str
    version: str
    mode: str
    tasks: list[TaskMetadata]


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


@app.get("/metadata", response_model=MetadataResponse)
async def get_metadata():
    """Return OpenEnv runtime metadata required by validators."""
    return MetadataResponse(
        name="support-ticket-triage",
        description="A real-world customer support ticket management environment for AI agents",
        version="1.0.0",
        mode="simulation",
        tasks=[TaskMetadata(**task) for task in get_task_metadata()],
    )


@app.get("/tasks")
async def get_tasks():
    """Return list of tasks with grader information."""
    tasks_list = get_task_metadata()
    return {
        "tasks": [
            {
                "id": task["id"],
                "name": task["name"],
                "description": task["description"],
                "difficulty": task.get("difficulty"),
                "max_steps": task.get("max_steps"),
                "success_threshold": task.get("success_threshold"),
                "has_grader": True,
                "graders": task.get("graders", [])
            }
            for task in tasks_list
        ]
    }


@app.get("/graders")
async def get_graders():
    """Return grader metadata for all tasks."""
    tasks_list = get_task_metadata()
    graders_map = {}
    for task in tasks_list:
        task_graders = task.get("graders", [])
        for grader in task_graders:
            grader_id = grader.get("id")
            if grader_id:
                graders_map[grader_id] = {
                    "id": grader_id,
                    "name": grader.get("name"),
                    "description": grader.get("description"),
                    "task": task["id"]
                }
    return {"graders": list(graders_map.values())}


@app.get("/schema")
async def get_schema():
    """Return action/observation/state schemas required by validators."""
    return {
        "action": SupportAction.model_json_schema(),
        "observation": SupportObservation.model_json_schema(),
        "state": SupportState.model_json_schema(),
    }


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Minimal JSON-RPC compatible endpoint for validator reachability checks."""
    payload: dict[str, Any] = {}
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    request_id = payload.get("id")
    method = payload.get("method", "unknown")

    if method == "initialize":
        result: dict[str, Any] = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "support-ticket-triage",
                "version": "1.0.0",
            },
            "capabilities": {},
        }
    else:
        result = {
            "status": "ok",
            "message": "MCP endpoint is reachable",
        }

    return JSONResponse(
        content={
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result,
        },
        media_type="application/json",
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
        "tasks": get_task_metadata()
    }


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Run the FastAPI server."""
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting Support Ticket Triage Environment server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main()