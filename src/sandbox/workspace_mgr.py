import os
from pathlib import Path

# 1. Define where the AI's isolated playpen folder lives
# Path(__file__).resolve().parents[2] points to your main 'devin-zero/' folder
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = PROJECT_ROOT / "agent_workspace"

def init_workspace() -> Path:
    """Creates the agent_workspace folder if it doesn't exist yet."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    return WORKSPACE_DIR

def get_safe_path(relative_path: str) -> Path:
    """
    Converts a file path requested by the AI (e.g., 'app.py') into a full path 
    inside agent_workspace, and blocks any attempt to escape the folder.
    """
    init_workspace()
    
    # Combine WORKSPACE_DIR with the file name the AI asked for
    target_path = (WORKSPACE_DIR / relative_path).resolve()

    # Security Check: Does target_path still start with WORKSPACE_DIR?
    if not str(target_path).startswith(str(WORKSPACE_DIR.resolve())):
        raise ValueError(f"Security Alert! AI tried to access outside workspace: {relative_path}")

    return target_path