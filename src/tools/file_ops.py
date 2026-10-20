import ast
from langchain_core.tools import tool
from src.sandbox.workspace_mgr import WORKSPACE_DIR, init_workspace, get_safe_path


@tool
def list_workspace_files() -> str:
    """Lists all files currently inside the agent_workspace folder."""
    init_workspace()
    files = []
    for p in WORKSPACE_DIR.rglob("*"):
        if p.is_file() and "__pycache__" not in str(p) and ".pytest_cache" not in str(p):
            # Show clean relative path like 'src/app.py' instead of full C:\Users\...
            files.append(str(p.relative_to(WORKSPACE_DIR)))
    
    if not files:
        return "Workspace is currently empty."
    return "Files in workspace:\n" + "\n".join(sorted(files))


@tool
def read_file(file_path: str, start_line: int = 1, end_line: int = 200) -> str:
    """
    Reads a file from the workspace with line numbers.
    Args:
        file_path: Relative path to the file (e.g., 'app.py').
        start_line: Line number to start reading from (1-indexed).
        end_line: Line number to stop reading at.
    """
    try:
        safe_path = get_safe_path(file_path)
        if not safe_path.exists():
            return f"Error: File '{file_path}' does not exist."

        lines = safe_path.read_text(encoding="utf-8").splitlines() #list of my code
        selected = lines[max(0, start_line - 1) : end_line] #slicing

        # Add line numbers (e.g., "1 | def add(a, b):")
        numbered_lines = [  
            f"{i} | {line}" for i, line in enumerate(selected, start=max(1, start_line))
        ]
        return "\n".join(numbered_lines) if numbered_lines else "(File is empty)"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(file_path: str, content: str) -> str:
    """
    Creates a new file or overwrites an existing file in the workspace.
    Checks Python syntax automatically if it's a .py file!
    """
    try:
        # Bonus Devin feature: Check if the AI wrote broken Python syntax BEFORE saving!
        if file_path.endswith(".py"):
            try:
                ast.parse(content)
            except SyntaxError as se:
                return f"SyntaxError rejected! Fix your Python syntax at line {se.lineno}: {se.msg}"

        safe_path = get_safe_path(file_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content.splitlines())} lines to '{file_path}'."
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def edit_file(file_path: str, target_code: str, replacement_code: str) -> str:
    """
    Surgically replaces a specific block of code (target_code) with replacement_code.
    """
    try:
        safe_path = get_safe_path(file_path)
        if not safe_path.exists():
            return f"Error: File '{file_path}' does not exist."

        content = safe_path.read_text(encoding="utf-8")
        if target_code not in content:
            return (
                f"Error: Exact 'target_code' block not found in '{file_path}'. "
                "Call read_file() first to see the exact lines and indentation."
            )

        updated_content = content.replace(target_code, replacement_code, 1)

        # Syntax check for Python files before saving
        if file_path.endswith(".py"):
            try:
                ast.parse(updated_content)
            except SyntaxError as se:
                return f"Edit rejected due to SyntaxError at line {se.lineno}: {se.msg}"

        safe_path.write_text(updated_content, encoding="utf-8")
        return f"Successfully updated '{file_path}'."
    except Exception as e:
        return f"Error editing file: {e}"