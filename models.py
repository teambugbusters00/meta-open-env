"""
Pydantic models for the Support Ticket Triage Environment.
"""

import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TicketCategory(str, Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    GENERAL = "general"
    SALES = "sales"
    URGENT = "urgent"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class ActionType(str, Enum):
    CATEGORIZE = "categorize"
    PRIORITIZE = "prioritize"
    RESPOND = "respond"
    ESCALATE = "escalate"
    REQUEST_INFO = "request_info"
    CLOSE = "close"


class Ticket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    customer_name: str
    customer_email: str
    subject: str
    content: str
    category: Optional[TicketCategory] = None
    priority: Optional[PriorityLevel] = None
    status: TicketStatus = TicketStatus.NEW
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    responses: List[str] = Field(default_factory=list)
    assigned_team: Optional[str] = None
    escalation_reason: Optional[str] = None


class SupportAction(BaseModel):
    action_type: ActionType
    ticket_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    category: Optional[TicketCategory] = None
    priority: Optional[PriorityLevel] = None
    response_text: Optional[str] = None
    escalation_reason: Optional[str] = None
    target_team: Optional[str] = None


class SupportObservation(BaseModel):
    tickets: List[Ticket] = Field(default_factory=list)
    current_step: int = 0
    max_steps: int = 10
    queue_status: Dict[str, int] = Field(default_factory=dict)
    available_actions: List[str] = Field(default_factory=list)
    instructions: str = ""
    last_action_result: Optional[str] = None


class SupportState(BaseModel):
    tickets: List[Ticket] = Field(default_factory=list)
    current_step: int = 0
    max_steps: int = 10
    task_id: str = "categorize_ticket"
    score: float = 0.0
    actions_taken: List[Dict] = Field(default_factory=list)
    correct_actions: int = 0
    total_actions: int = 0