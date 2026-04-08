"""
Client for interacting with the Support Ticket Triage Environment.
"""

import httpx
from typing import Dict, Any, Optional


class SupportTicketEnvClient:
    """Client for the Support Ticket Triage Environment"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def reset(self, task_id: str = "categorize_ticket") -> Dict[str, Any]:
        """Reset the environment"""
        response = await self.client.post(
            f"{self.base_url}/reset",
            json={"task_id": task_id}
        )
        response.raise_for_status()
        return response.json()
    
    async def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a step in the environment"""
        response = await self.client.post(
            f"{self.base_url}/step",
            json=action
        )
        response.raise_for_status()
        return response.json()
    
    async def get_state(self) -> Dict[str, Any]:
        """Get current environment state"""
        response = await self.client.get(f"{self.base_url}/state")
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> bool:
        """Check if environment is healthy"""
        response = await self.client.get(f"{self.base_url}/health")
        return response.status_code == 200
    
    async def close(self):
        """Close the client"""
        await self.client.aclose()