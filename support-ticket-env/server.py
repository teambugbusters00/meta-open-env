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
    GRADER_FUNCTIONS,
    TASK_CONFIGS,
    TicketCategory,
    PriorityLevel,
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


class GradeRequest(BaseModel):
    grader_id: str
    sample: dict[str, Any]


class TaskGradeRequest(BaseModel):
    task_id: str
    input: dict[str, Any]
    grader_id: Optional[str] = None  # Optional; uses first grader of task if not specified


class GradeResponse(BaseModel):
    grader_id: str
    score: float
    status: str = "success"
    message: str = ""
    task_id: Optional[str] = None


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


@app.post("/grade", response_model=GradeResponse)
async def grade_sample(request: dict[str, Any]):
    """
    Grade a sample using a grader. Supports two formats:
    
    Format 1 (Direct grader):
        {"grader_id": "categorization_accuracy", "sample": {...}}
    
    Format 2 (Task-based):
        {"task_id": "categorize_ticket", "input": {...}, "grader_id": "optional"}
    
    Returns:
        GradeResponse with score (0.0-1.0)
    """
    # Determine which format is being used
    if "grader_id" in request and "sample" in request:
        # Format 1: Direct grader format
        grader_id = request["grader_id"]
        sample = request["sample"]
        task_id = None
    elif "task_id" in request and "input" in request:
        # Format 2: Task-based format
        task_id = request["task_id"]
        input_data = request["input"]
        
        # Get task config to find graders
        if task_id not in TASK_CONFIGS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task: {task_id}. Available tasks: {', '.join(TASK_CONFIGS.keys())}"
            )
        
        task_config = TASK_CONFIGS[task_id]
        graders = task_config.get("graders", [])
        
        if not graders:
            raise HTTPException(
                status_code=400,
                detail=f"No graders available for task {task_id}"
            )
        
        # Use specified grader or first available
        requested_grader_id = request.get("grader_id")
        if requested_grader_id:
            grader_id = requested_grader_id
            # Verify it's valid for this task
            valid_grader_ids = [g["id"] for g in graders]
            if grader_id not in valid_grader_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Grader {grader_id} not available for task {task_id}. Valid graders: {valid_grader_ids}"
                )
        else:
            grader_id = graders[0]["id"]
        
        # Convert task input to grader sample format
        sample = _convert_input_to_sample(task_id, input_data, grader_id)
    else:
        raise HTTPException(
            status_code=400,
            detail="Request must include either (grader_id + sample) or (task_id + input)"
        )
    
    # Check grader exists
    if grader_id not in GRADER_FUNCTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown grader: {grader_id}. Available graders: {', '.join(GRADER_FUNCTIONS.keys())}"
        )
    
    try:
        grader_fn = GRADER_FUNCTIONS[grader_id]
        score = grader_fn(sample)
        
        # Ensure score is in valid range
        score = max(0.0, min(1.0, float(score)))
        
        return GradeResponse(
            grader_id=grader_id,
            score=score,
            status="success",
            message=f"Successfully graded sample with {grader_id}",
            task_id=task_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error running grader {grader_id}: {str(e)}"
        )


def _convert_input_to_sample(task_id: str, input_data: dict[str, Any], grader_id: str) -> dict[str, Any]:
    """Convert task input format to grader sample format."""
    sample = {}
    
    if task_id == "categorize_ticket":
        # For categorization task, extract ticket info and expected values
        if "ticket_text" in input_data:
            # This is raw input - use default expected values or parse
            sample["agent_category"] = input_data.get("agent_category", TicketCategory.GENERAL)
            sample["expected_category"] = input_data.get("expected_category", TicketCategory.GENERAL)
            sample["agent_priority"] = input_data.get("agent_priority", PriorityLevel.MEDIUM)
            sample["expected_priority"] = input_data.get("expected_priority", PriorityLevel.MEDIUM)
        else:
            # Structured input expected
            sample.update(input_data)
    
    elif task_id == "prioritize_and_route":
        # For prioritization task
        sample["priority_scores"] = input_data.get("priority_scores", [])
    
    elif task_id == "full_workflow":
        # For full workflow task
        sample["categorization_score"] = input_data.get("categorization_score", 0.0)
        sample["response_quality"] = input_data.get("response_quality", 0.0)
        sample["escalation_score"] = input_data.get("escalation_score", 0.0)
        sample["completion_ratio"] = input_data.get("completion_ratio", 0.0)
    
    elif task_id == "escalation_specialist":
        # For escalation task
        sample["expected_escalation"] = input_data.get("expected_escalation", False)
        sample["agent_escalated"] = input_data.get("agent_escalated", False)
        sample["expected_team"] = input_data.get("expected_team", "")
        sample["agent_team"] = input_data.get("agent_team", "")
    
    return sample


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