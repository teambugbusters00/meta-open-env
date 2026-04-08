"""Root-level ASGI/CLI entrypoint for multi-mode deployment."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import uvicorn


def _load_support_server_module():
    repo_root = Path(__file__).resolve().parent.parent
    support_env_dir = repo_root / "support-ticket-env"
    target = support_env_dir / "server.py"

    if str(support_env_dir) not in sys.path:
        sys.path.insert(0, str(support_env_dir))

    spec = importlib.util.spec_from_file_location("support_ticket_env_server", target)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load server module from {target}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_server_module = _load_support_server_module()
app = _server_module.app


def main() -> None:
    """Run the wrapped FastAPI application."""
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()