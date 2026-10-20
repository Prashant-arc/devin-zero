import ast
from langchain_core.tools import tool
from src.sandbox.workspace_mgr import WORKSPACE_DIR, init_workspace


def _parse_python_skeleton(file_path) -> list[str]:
    """Reads a .py file using AST and extracts only classes and function names with line numbers."""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as e:
        return [f"  [SyntaxError / Unparseable: {e}]"]

    lines = []
    for node in tree.body:
        # 1. If it's a Class, grab the class name and its methods
        if isinstance(node, ast.ClassDef):
            lines.append(f"  class {node.name} (line {node.lineno}):")
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    args = [a.arg for a in sub.args.args]
                    lines.append(f"    def {sub.name}({', '.join(args)}) [line {sub.lineno}]")

        # 2. If it's a standalone Function, grab the function name and its arguments
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args]
            lines.append(f"  def {node.name}({', '.join(args)}) [line {node.lineno}]")

    return lines if lines else ["  (no top-level classes or functions)"]


@tool
def get_repo_map() -> str:
    """
    Generates an AST-based structural map (classes, functions, line numbers) 
    of all files in the agent_workspace.
    """
    init_workspace()
    output = []

    for p in sorted(WORKSPACE_DIR.rglob("*")):
        if p.is_file() and "__pycache__" not in str(p) and ".pytest_cache" not in str(p):
            rel_path = p.relative_to(WORKSPACE_DIR)
            output.append(f" {rel_path}")
            if p.suffix == ".py":
                output.extend(_parse_python_skeleton(p))

    if not output:
        return "Workspace is currently empty."

    return "=== REPOSITORY AST MAP ===\n" + "\n".join(output)