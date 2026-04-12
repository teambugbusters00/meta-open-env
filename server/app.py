"""ASGI/CLI entrypoint required for multi-mode deployment validators."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import uvicorn


def _load_legacy_server_module():
    base_dir = Path(__file__).resolve().parent.parent
    legacy_server = base_dir / "server.py"

    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    spec = importlib.util.spec_from_file_location("support_ticket_env_legacy_server", legacy_server)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load server module from {legacy_server}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_legacy_server = _load_legacy_server_module()
app = _legacy_server.app


def main() -> None:
    """Run the FastAPI application."""
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
