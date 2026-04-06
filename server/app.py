"""FastAPI application for the Medical PA Environment."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import Body
from pydantic import BaseModel
from typing import Any, Dict, Optional

from models import PAAction, PAObservation, PAState
from server.environment import MedPAEnvironment

try:
    from openenv.core.env_server.http_server import create_app
except ImportError:
    from openenv.core.env_server.http_server import create_app

# create_app gives us /ws, /health, /schema, /metadata, /mcp + stateless /reset, /step, /state
app = create_app(MedPAEnvironment, PAAction, PAObservation, env_name="med_pa", max_concurrent_envs=4)


@app.get("/")
def root():
    return {"status": "ok", "env": "med_pa"}


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
