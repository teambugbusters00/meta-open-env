"""Root-level OpenEnv entrypoint wrapping the nested support-ticket environment."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_support_env_module():
    repo_root = Path(__file__).resolve().parent
    support_env_dir = repo_root / "support-ticket-env"
    target = support_env_dir / "env.py"

    if str(support_env_dir) not in sys.path:
        sys.path.insert(0, str(support_env_dir))

    spec = importlib.util.spec_from_file_location("support_ticket_env_env", target)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load environment module from {target}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_env_module = _load_support_env_module()

SupportTicketEnv = _env_module.SupportTicketEnv
SupportAction = _env_module.SupportAction
SupportObservation = _env_module.SupportObservation
SupportState = _env_module.SupportState

__all__ = [
    "SupportTicketEnv",
    "SupportAction",
    "SupportObservation",
    "SupportState",
]