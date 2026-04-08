"""
Support Ticket Triage Environment
A real-world customer support ticket management environment for AI agents.
"""

from .env import SupportTicketEnv, SupportAction, SupportObservation, SupportState

__version__ = "1.0.0"
__all__ = ["SupportTicketEnv", "SupportAction", "SupportObservation", "SupportState"]