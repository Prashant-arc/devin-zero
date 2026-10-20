import subprocess
import sys
from langchain_core.tools import tool
from src.sandbox.workspace_mgr import WORKSPACE_DIR, init_workspace

# Dangerous commands the AI is never allowed to run
BLOCKED_KEYWORDS = ["rm -rf", "del /f", "format ", "shutdown", "reboot"]


@tool
def run_bash_sandbox(command: str, timeout: int = 15) -> str:
    """
    Executes a terminal command (like 'pytest' or 'python app.py') inside the isolated agent_workspace.
    Returns the exit_code, stdout, and stderr so the agent can verify its code or debug errors.
    """
    init_workspace()

    # 1. Security Check: Block destructive commands
    cmd_lower = command.lower()
    for bad_word in BLOCKED_KEYWORDS:
        if bad_word in cmd_lower:
            return f"Security Error: Command blocked because it contains '{bad_word}'."

    # 2. Ensure 'python' or 'pytest' uses our active (venv) Python environment!
    if command.startswith("python "):
        command = command.replace("python ", f'"{sys.executable}" ', 1)
    elif command.startswith("pytest"):
        command = command.replace("pytest", f'"{sys.executable}" -m pytest', 1)

    try:
        # 3. Run the command strictly inside WORKSPACE_DIR with a timeout
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(WORKSPACE_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        # 4. Format the output clearly for the AI brain
        output = (
            f"COMMAND: {command}\n"
            f"EXIT_CODE: {result.returncode}\n"
            f"--- STDOUT ---\n{result.stdout.strip() or '(empty)'}\n"
            f"--- STDERR ---\n{result.stderr.strip() or '(empty)'}"
        )
        return output

    except subprocess.TimeoutExpired:
        return (
            f"TIMEOUT ERROR: Command '{command}' took longer than {timeout} seconds and was killed. "
            "Check your code for infinite loops or blocking input() calls!"
        )
    except Exception as e:
        return f"Execution Error: {e}"