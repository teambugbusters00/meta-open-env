"""
Support Ticket Triage Environment
A real-world customer support ticket management environment for AI agents.
"""

import uuid
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# ============================================================================
# Domain Models
# ============================================================================

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


# ============================================================================
# Ticket Templates
# ============================================================================

TICKET_TEMPLATES = {
    "technical": [
        {
            "subject": "Application crashes on startup",
            "content": "Hi, I've been trying to use your software but it crashes immediately when I open it. I've tried reinstalling but the problem persists. This is very frustrating as I need it for my work. Please help!",
            "expected_category": TicketCategory.TECHNICAL,
            "expected_priority": PriorityLevel.HIGH
        },
        {
            "subject": "API returning 500 errors",
            "content": "Our integration with your API has been failing for the past 2 hours. We're getting 500 Internal Server Error responses on all endpoints. This is affecting our production system.",
            "expected_category": TicketCategory.TECHNICAL,
            "expected_priority": PriorityLevel.CRITICAL
        },
        {
            "subject": "Feature request: Dark mode",
            "content": "Would love to see a dark mode option in the application. Many of us work late nights and the bright interface is hard on the eyes.",
            "expected_category": TicketCategory.GENERAL,
            "expected_priority": PriorityLevel.LOW
        }
    ],
    "billing": [
        {
            "subject": "Charged twice for subscription",
            "content": "I was charged $99.99 twice this month for my premium subscription. I only have one active subscription. Please refund the duplicate charge immediately.",
            "expected_category": TicketCategory.BILLING,
            "expected_priority": PriorityLevel.HIGH
        },
        {
            "subject": "Invoice not received",
            "content": "I need a copy of my invoice from last month for tax purposes. I've checked my email but can't find it anywhere.",
            "expected_category": TicketCategory.BILLING,
            "expected_priority": PriorityLevel.MEDIUM
        },
        {
            "subject": "Want to upgrade plan",
            "content": "Our team has grown and we need to upgrade from the basic plan to enterprise. What's the process and pricing?",
            "expected_category": TicketCategory.SALES,
            "expected_priority": PriorityLevel.MEDIUM
        }
    ],
    "account": [
        {
            "subject": "Cannot reset password",
            "content": "I've tried to reset my password multiple times but I'm not receiving the reset email. I've checked spam folder too. My account email is user@example.com",
            "expected_category": TicketCategory.ACCOUNT,
            "expected_priority": PriorityLevel.HIGH
        },
        {
            "subject": "Account locked after too many attempts",
            "content": "My account got locked after I entered the wrong password too many times. I need access urgently for a client presentation.",
            "expected_category": TicketCategory.ACCOUNT,
            "expected_priority": PriorityLevel.HIGH
        }
    ]
}


TASK_CONFIGS = {
    "categorize_ticket": {
        "name": "Ticket Categorization (Easy)",
        "description": "Categorize incoming support tickets correctly.",
        "difficulty": "easy",
        "max_steps": 5,
        "ticket_count": 3,
        "success_threshold": 0.7,
        "graders": [
            {
                "id": "categorization_accuracy",
                "name": "Categorization Accuracy",
                "description": "Scores whether the selected category and priority match the expected labels for each ticket.",
            }
        ],
    },
    "prioritize_and_route": {
        "name": "Prioritize and Route (Medium)",
        "description": "Categorize and prioritize multiple tickets.",
        "difficulty": "medium",
        "max_steps": 10,
        "ticket_count": 5,
        "success_threshold": 0.6,
        "graders": [
            {
                "id": "queue_prioritization",
                "name": "Queue Prioritization",
                "description": "Evaluates whether tickets are assigned appropriate priority levels based on urgency and routed through the workflow correctly.",
            }
        ],
    },
    "full_workflow": {
        "name": "Full Support Workflow (Hard)",
        "description": "Complete end-to-end support workflow.",
        "difficulty": "hard",
        "max_steps": 15,
        "ticket_count": 4,
        "success_threshold": 0.5,
        "graders": [
            {
                "id": "workflow_resolution_quality",
                "name": "Workflow Resolution Quality",
                "description": "Grades the full workflow including categorization, prioritization, response quality, escalation judgment, and ticket completion.",
            },
            {
                "id": "response_professionalism",
                "name": "Response Professionalism",
                "description": "Specific evaluation of the tone, politeness, and professional formatting of agent responses.",
            }
        ],
    },
    "escalation_specialist": {
        "name": "Escalation Specialist (Medium)",
        "description": "Evaluate and route high-priority tickets to the correct specialized teams based on technical depth.",
        "difficulty": "medium",
        "max_steps": 8,
        "ticket_count": 4,
        "success_threshold": 0.65,
        "graders": [
            {
                "id": "escalation_precision",
                "name": "Escalation Precision",
                "description": "Measures the accuracy of escalation decisions and the appropriateness of the target team selection.",
            }
        ],
    },
}


def get_task_metadata() -> List[Dict[str, Any]]:
    """Return task metadata, including explicit grader declarations for validators."""
    tasks: List[Dict[str, Any]] = []
    for task_id, config in TASK_CONFIGS.items():
        tasks.append(
            {
                "id": task_id,
                "name": config["name"],
                "description": config["description"],
                "difficulty": config["difficulty"],
                "max_steps": config["max_steps"],
                "success_threshold": config["success_threshold"],
                "graders": config["graders"],
            }
        )
    return tasks


# ============================================================================
# Grader Registry - Callable graders for validator integration
# ============================================================================

class GraderRegistry:
    """Registry of callable graders that can be invoked by validators"""
    
    @staticmethod
    def grade_categorization_accuracy(sample: Dict[str, Any]) -> float:
        """
        Grader: Categorization Accuracy
        Scores 0.0-1.0 whether ticket categories and priorities were correctly assigned.
        """
        if "expected_category" not in sample or "agent_category" not in sample:
            return 0.0
        
        grader = TicketGrader()
        return grader.grade_categorization(
            sample.get("agent_category"),
            sample.get("expected_category"),
            sample.get("agent_priority", PriorityLevel.MEDIUM),
            sample.get("expected_priority", PriorityLevel.MEDIUM)
        )
    
    @staticmethod
    def grade_queue_prioritization(sample: Dict[str, Any]) -> float:
        """
        Grader: Queue Prioritization
        Evaluates whether multiple tickets were prioritized correctly relative to each other.
        """
        if "priority_scores" not in sample:
            return 0.0
        
        scores = sample.get("priority_scores", [])
        if not scores:
            return 0.0
        
        # Average of all prioritization decisions
        avg_score = sum(scores) / len(scores)
        return max(0.0, min(1.0, avg_score))
    
    @staticmethod
    def grade_workflow_resolution_quality(sample: Dict[str, Any]) -> float:
        """
        Grader: Workflow Resolution Quality
        Grades the full workflow including categorization, prioritization, responses, and escalation.
        """
        components = []
        
        # Categorization component
        if "categorization_score" in sample:
            components.append(sample["categorization_score"] * 0.3)
        
        # Response quality component
        if "response_quality" in sample:
            components.append(sample["response_quality"] * 0.3)
        
        # Escalation correctness component
        if "escalation_score" in sample:
            components.append(sample["escalation_score"] * 0.2)
        
        # Completion component
        if "completion_ratio" in sample:
            components.append(sample["completion_ratio"] * 0.2)
        
        if not components:
            return 0.0
        
        return max(0.0, min(1.0, sum(components)))
    
    @staticmethod
    def grade_escalation_precision(sample: Dict[str, Any]) -> float:
        """
        Grader: Escalation Precision
        Measures accuracy of escalation decisions and appropriateness of team selection.
        """
        expected_escalation = sample.get("expected_escalation", False)
        agent_escalation = sample.get("agent_escalated", False)
        
        if expected_escalation == agent_escalation:
            base_score = 0.8
        else:
            base_score = 0.2
        
        # Bonus for correct team selection when escalated
        if agent_escalation and expected_escalation:
            expected_team = sample.get("expected_team", "")
            agent_team = sample.get("agent_team", "")
            if expected_team == agent_team:
                return 1.0
            else:
                return base_score + 0.15
        
        return base_score
    
    @staticmethod
    def grade_response_professionalism(sample: Dict[str, Any]) -> float:
        """
        Grader: Response Professionalism
        Evaluates the tone, politeness, and professional formatting of agent responses.
        """
        return min(1.0, sample.get("response_length", 0) / 100.0)


# Map grader IDs to callable functions
GRADER_FUNCTIONS = {
    "categorization_accuracy": GraderRegistry.grade_categorization_accuracy,
    "queue_prioritization": GraderRegistry.grade_queue_prioritization,
    "workflow_resolution_quality": GraderRegistry.grade_workflow_resolution_quality,
    "escalation_precision": GraderRegistry.grade_escalation_precision,
    "response_professionalism": GraderRegistry.grade_response_professionalism,
}


# ============================================================================
# Grading Logic
# ============================================================================


class TicketGrader:
    @staticmethod
    def grade_categorization(agent_category, expected_category, agent_priority, expected_priority) -> float:
        category_score = 0.0
        priority_score = 0.0
        
        if agent_category == expected_category:
            category_score = 0.6
        elif agent_category is not None:
            related = {
                TicketCategory.TECHNICAL: [TicketCategory.URGENT],
                TicketCategory.BILLING: [TicketCategory.SALES],
                TicketCategory.ACCOUNT: [TicketCategory.TECHNICAL],
            }
            if expected_category in related.get(agent_category, []):
                category_score = 0.3
            else:
                category_score = 0.1
        
        priority_levels = {
            PriorityLevel.LOW: 0,
            PriorityLevel.MEDIUM: 1,
            PriorityLevel.HIGH: 2,
            PriorityLevel.CRITICAL: 3
        }
        
        if agent_priority == expected_priority:
            priority_score = 0.4
        elif agent_priority is not None:
            agent_level = priority_levels.get(agent_priority, 0)
            expected_level = priority_levels.get(expected_priority, 0)
            diff = abs(agent_level - expected_level)
            if diff == 1:
                priority_score = 0.2
            else:
                priority_score = 0.05
        
        return category_score + priority_score
    
    @staticmethod
    def grade_response(response_text: str, ticket_category: TicketCategory) -> float:
        if not response_text or len(response_text.strip()) < 10:
            return 0.0
        
        response_lower = response_text.lower()
        
        relevant_keywords = {
            TicketCategory.TECHNICAL: ["troubleshoot", "debug", "error", "fix", "solution", "steps", "restart", "update"],
            TicketCategory.BILLING: ["refund", "charge", "invoice", "payment", "billing", "amount"],
            TicketCategory.ACCOUNT: ["password", "reset", "unlock", "access", "login", "account"],
            TicketCategory.GENERAL: ["help", "support", "assist", "information"],
            TicketCategory.SALES: ["pricing", "plan", "upgrade", "enterprise", "demo"],
            TicketCategory.URGENT: ["immediately", "urgent", "asap", "priority"]
        }
        
        keywords = relevant_keywords.get(ticket_category, [])
        keyword_matches = sum(1 for kw in keywords if kw in response_lower)
        keyword_score = min(keyword_matches / max(len(keywords) * 0.5, 1), 1.0) * 0.6
        
        professionalism_indicators = ["thank", "please", "regards", "sincerely", "appreciate"]
        prof_matches = sum(1 for ind in professionalism_indicators if ind in response_lower)
        prof_score = min(prof_matches / 2, 1.0) * 0.2
        
        word_count = len(response_text.split())
        if 20 <= word_count <= 150:
            length_score = 0.2
        elif 10 <= word_count < 20 or 150 < word_count <= 200:
            length_score = 0.1
        else:
            length_score = 0.0
        
        return keyword_score + prof_score + length_score
    
    @staticmethod
    def grade_escalation(ticket_priority: PriorityLevel, escalation_reason: str, target_team: str) -> float:
        score = 0.0
        
        if ticket_priority == PriorityLevel.CRITICAL:
            if target_team in ["senior_support", "engineering", "management"]:
                score = 0.7
            else:
                score = 0.3
        elif ticket_priority == PriorityLevel.HIGH:
            if escalation_reason and len(escalation_reason) > 20:
                score = 0.5
            else:
                score = 0.2
        else:
            if target_team in ["senior_support", "engineering"]:
                score = 0.1
            else:
                score = 0.4
        
        return score


# ============================================================================
# Environment Implementation
# ============================================================================

class SupportTicketEnv:
    """
    Customer Support Ticket Triage Environment
    
    An AI agent learns to handle customer support tickets by:
    1. Categorizing tickets into correct departments
    2. Assigning appropriate priority levels
    3. Drafting professional responses
    4. Making escalation decisions when needed
    
    Tasks progress from easy (single categorization) to hard (full workflow).
    """
    
    def __init__(self):
        self._state: Optional[SupportState] = None
        self.grader = TicketGrader()
    
    async def reset(self, task_id: str = "categorize_ticket") -> dict:
        """Reset environment to initial state"""
        
        config = TASK_CONFIGS.get(task_id, TASK_CONFIGS["categorize_ticket"])
        tickets = self._generate_tickets(config["ticket_count"], task_id)
        
        self._state = SupportState(
            tickets=tickets,
            current_step=0,
            max_steps=config["max_steps"],
            task_id=task_id,
            score=0.0,
            actions_taken=[],
            correct_actions=0,
            total_actions=0
        )
        
        observation = self._create_observation()
        observation.instructions = config["description"]
        
        return {
            "observation": observation.model_dump(),
            "reward": 0.0,
            "done": False,
            "info": {"task_id": task_id, "message": "Environment reset successfully"}
        }
    
    async def step(self, action: SupportAction) -> dict:
        """Execute agent action and return result"""
        
        if self._state is None:
            raise ValueError("Environment not initialized. Call reset() first.")
        
        if self._state.current_step >= self._state.max_steps:
            return {
                "observation": self._create_observation().model_dump(),
                "reward": 0.0,
                "done": True,
                "info": {"error": "Maximum steps reached"}
            }
        
        # Execute action
        reward = 0.0
        action_result = ""
        
        try:
            if action.action_type == ActionType.CATEGORIZE:
                reward, action_result = self._handle_categorize(action)
            elif action.action_type == ActionType.PRIORITIZE:
                reward, action_result = self._handle_prioritize(action)
            elif action.action_type == ActionType.RESPOND:
                reward, action_result = self._handle_respond(action)
            elif action.action_type == ActionType.ESCALATE:
                reward, action_result = self._handle_escalate(action)
            elif action.action_type == ActionType.REQUEST_INFO:
                reward, action_result = self._handle_request_info(action)
            elif action.action_type == ActionType.CLOSE:
                reward, action_result = self._handle_close(action)
            else:
                reward = -0.1
                action_result = f"Unknown action type: {action.action_type}"
        
        except Exception as e:
            reward = -0.1
            action_result = f"Error executing action: {str(e)}"
        
        # Update state
        self._state.current_step += 1
        self._state.total_actions += 1
        if reward > 0.5:
            self._state.correct_actions += 1
        self._state.actions_taken.append({
            "step": self._state.current_step,
            "action": action.model_dump(),
            "reward": reward,
            "result": action_result
        })
        
        # Calculate cumulative score
        self._state.score = self._calculate_score()
        
        # Check if done
        done = self._check_done()
        
        # Create observation
        observation = self._create_observation()
        observation.last_action_result = action_result
        
        return {
            "observation": observation.model_dump(),
            "reward": reward,
            "done": done,
            "info": {
                "action_result": action_result,
                "current_score": self._state.score
            }
        }
    
    def get_state(self) -> Optional[SupportState]:
        """Return current environment state"""
        return self._state
    
    def _generate_tickets(self, count: int, task_id: str) -> List[Ticket]:
        """Generate realistic support tickets"""
        tickets = []
        
        if task_id == "categorize_ticket":
            template_pool = TICKET_TEMPLATES["technical"][:2] + TICKET_TEMPLATES["billing"][:1]
        elif task_id == "escalation_specialist":
            template_pool = TICKET_TEMPLATES["technical"] + TICKET_TEMPLATES["account"]
        else:
            template_pool = (TICKET_TEMPLATES["technical"] + 
                           TICKET_TEMPLATES["billing"] + 
                           TICKET_TEMPLATES["account"])
        
        for i in range(min(count, len(template_pool))):
            template = template_pool[i % len(template_pool)]
            ticket = Ticket(
                customer_name=f"Customer_{i+1}",
                customer_email=f"customer{i+1}@example.com",
                subject=template["subject"],
                content=template["content"]
            )
            tickets.append(ticket)
        
        return tickets
    
    def _create_observation(self) -> SupportObservation:
        """Create observation for the agent"""
        if self._state is None:
            return SupportObservation()
        
        # Calculate queue status
        queue_status = {
            "new": sum(1 for t in self._state.tickets if t.status == TicketStatus.NEW),
            "in_progress": sum(1 for t in self._state.tickets if t.status == TicketStatus.IN_PROGRESS),
            "resolved": sum(1 for t in self._state.tickets if t.status == TicketStatus.RESOLVED),
            "escalated": sum(1 for t in self._state.tickets if t.status == TicketStatus.ESCALATED)
        }
        
        # Determine available actions based on task
        available_actions = ["categorize", "prioritize"]
        if self._state.task_id in ["prioritize_and_route", "full_workflow", "escalation_specialist"]:
            available_actions.extend(["respond", "escalate", "request_info", "close"])
        
        return SupportObservation(
            tickets=self._state.tickets,
            current_step=self._state.current_step,
            max_steps=self._state.max_steps,
            queue_status=queue_status,
            available_actions=available_actions,
            instructions=f"Task: {self._state.task_id}. Handle tickets appropriately."
        )
    
    def _handle_categorize(self, action: SupportAction) -> tuple:
        """Handle ticket categorization action"""
        ticket = self._find_ticket(action.ticket_id)
        if not ticket:
            return 0.0, "Ticket not found"
        
        if not action.category:
            return 0.0, "No category specified"
        
        # Find expected category from template
        expected_category = None
        expected_priority = None
        for category_tickets in TICKET_TEMPLATES.values():
            for template in category_tickets:
                if template["subject"] == ticket.subject:
                    expected_category = template["expected_category"]
                    expected_priority = template["expected_priority"]
                    break
        
        if expected_category is None:
            expected_category = TicketCategory.GENERAL
            expected_priority = PriorityLevel.MEDIUM
        
        # Grade the categorization
        reward = self.grader.grade_categorization(
            action.category, expected_category,
            action.priority if action.priority else PriorityLevel.MEDIUM, expected_priority
        )
        
        # Update ticket
        ticket.category = action.category
        if action.priority:
            ticket.priority = action.priority
        ticket.status = TicketStatus.IN_PROGRESS
        
        result = (f"Categorized ticket {ticket.id} as {action.category.value} "
                 f"with priority {ticket.priority.value if ticket.priority else 'unassigned'}")
        
        return reward, result
    
    def _handle_prioritize(self, action: SupportAction) -> tuple:
        """Handle ticket prioritization action"""
        ticket = self._find_ticket(action.ticket_id)
        if not ticket:
            return 0.0, "Ticket not found"
        
        if not action.priority:
            return 0.0, "No priority specified"
        
        # Base reward on ticket content urgency
        content_lower = ticket.content.lower()
        urgency_indicators = ["urgent", "immediately", "asap", "critical", "emergency"]
        has_urgency = any(ind in content_lower for ind in urgency_indicators)
        
        expected_priority = PriorityLevel.HIGH if has_urgency else PriorityLevel.MEDIUM
        
        # Grade prioritization
        priority_levels = {
            PriorityLevel.LOW: 0,
            PriorityLevel.MEDIUM: 1,
            PriorityLevel.HIGH: 2,
            PriorityLevel.CRITICAL: 3
        }
        
        agent_level = priority_levels.get(action.priority, 1)
        expected_level = priority_levels.get(expected_priority, 1)
        
        if agent_level == expected_level:
            reward = 0.8
        elif abs(agent_level - expected_level) == 1:
            reward = 0.5
        else:
            reward = 0.2
        
        ticket.priority = action.priority
        
        result = f"Prioritized ticket {ticket.id} as {action.priority.value}"
        return reward, result
    
    def _handle_respond(self, action: SupportAction) -> tuple:
        """Handle response action"""
        ticket = self._find_ticket(action.ticket_id)
        if not ticket:
            return 0.0, "Ticket not found"
        
        if not action.response_text:
            return 0.0, "No response text provided"
        
        if not ticket.category:
            return 0.0, "Ticket must be categorized before responding"
        
        # Grade response quality
        reward = self.grader.grade_response(action.response_text, ticket.category)
        
        ticket.responses.append(action.response_text)
        ticket.status = TicketStatus.WAITING_CUSTOMER
        
        result = f"Responded to ticket {ticket.id} ({len(action.response_text)} chars)"
        return reward, result
    
    def _handle_escalate(self, action: SupportAction) -> tuple:
        """Handle escalation action"""
        ticket = self._find_ticket(action.ticket_id)
        if not ticket:
            return 0.0, "Ticket not found"
        
        if not action.escalation_reason:
            return 0.0, "No escalation reason provided"
        
        # Grade escalation decision
        priority = ticket.priority if ticket.priority else PriorityLevel.MEDIUM
        reward = self.grader.grade_escalation(
            priority,
            action.escalation_reason if action.escalation_reason else "",
            action.target_team if action.target_team else "general"
        )
        
        ticket.status = TicketStatus.ESCALATED
        ticket.escalation_reason = action.escalation_reason
        ticket.assigned_team = action.target_team
        
        result = f"Escalated ticket {ticket.id}: {action.escalation_reason}"
        return reward, result
    
    def _handle_request_info(self, action: SupportAction) -> tuple:
        """Handle request for information action"""
        ticket = self._find_ticket(action.ticket_id)
        if not ticket:
            return 0.0, "Ticket not found"
        
        if not action.response_text:
            return 0.0, "No message provided"
        
        ticket.responses.append(f"[INFO_REQUEST] {action.response_text}")
        ticket.status = TicketStatus.WAITING_CUSTOMER
        
        result = f"Requested information from customer for ticket {ticket.id}"
        return 0.4, result
    
    def _handle_close(self, action: SupportAction) -> tuple:
        """Handle ticket closure"""
        ticket = self._find_ticket(action.ticket_id)
        if not ticket:
            return 0.0, "Ticket not found"
        
        # Can transition from various states to closure
        if ticket.status not in [TicketStatus.NEW, TicketStatus.IN_PROGRESS, TicketStatus.WAITING_CUSTOMER, TicketStatus.RESOLVED]:
            return 0.0, "Ticket cannot be closed in current state"
        
        # First mark as resolved if it has been handled
        if ticket.status == TicketStatus.WAITING_CUSTOMER and ticket.responses:
            ticket.status = TicketStatus.RESOLVED
            # Bonus for resolving through proper workflow
            return 0.6, f"Resolved ticket {ticket.id}"
        
        # Then close it
        if ticket.status in [TicketStatus.RESOLVED, TicketStatus.WAITING_CUSTOMER]:
            ticket.status = TicketStatus.CLOSED
            reward = 0.4 if ticket.responses else 0.1
        elif ticket.status in [TicketStatus.NEW, TicketStatus.IN_PROGRESS]:
            # Can close unhandled tickets but with penalty
            ticket.status = TicketStatus.CLOSED
            reward = 0.0
        else:
            ticket.status = TicketStatus.CLOSED
            reward = 0.1
        
        result = f"Closed ticket {ticket.id}"
        return reward, result
    
    def _find_ticket(self, ticket_id) -> Optional[Ticket]:
        """Find ticket by ID"""
        if not ticket_id or self._state is None:
            return None
        for ticket in self._state.tickets:
            if ticket.id == ticket_id:
                return ticket
        return None
    
    def _calculate_score(self) -> float:
        """Calculate overall performance score"""
        if self._state is None or self._state.total_actions == 0:
            return 0.0
        
        # Weighted score based on action correctness
        correctness_ratio = self._state.correct_actions / self._state.total_actions
        
        # Bonus for completing all tickets
        completed_tickets = sum(1 for t in self._state.tickets 
                              if t.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED])
        completion_ratio = completed_tickets / max(len(self._state.tickets), 1)
        
        # Penalty for unresolved tickets at end
        unresolved = sum(1 for t in self._state.tickets if t.status == TicketStatus.NEW)
        unresolved_penalty = unresolved * 0.1
        
        score = (correctness_ratio * 0.6 + completion_ratio * 0.4) - unresolved_penalty
        return max(0.0, min(1.0, score))
    
    def _check_done(self) -> bool:
        """Check if episode is complete"""
        if self._state is None:
            return True
        
        # Max steps reached
        if self._state.current_step >= self._state.max_steps:
            return True
        
        # All tickets handled
        all_handled = all(
            t.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED, TicketStatus.ESCALATED]
            for t in self._state.tickets
        )
        
        return all_handled and self._state.current_step > 0