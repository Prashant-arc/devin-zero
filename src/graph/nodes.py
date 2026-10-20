import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.graph.state import DevinState
from src.tools.file_ops import list_workspace_files, read_file, write_file, edit_file
from src.tools.repo_map import get_repo_map
from src.tools.shell_exec import run_bash_sandbox

# 1. Load your secret GOOGLE_API_KEY from the .env file
load_dotenv()

# 2. Initialize Gemini with automatic built-in retries for 429 rate limits
llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0.1,
    max_retries=6,
)

# 3. Give the Coder brain access to your file tools ("The Hands")
CODER_TOOLS = [list_workspace_files, read_file, write_file, edit_file]
llm_with_tools = llm.bind_tools(CODER_TOOLS)


def _invoke_with_rate_limit_guard(runnable, messages):
    """Automatically waits and retries if the Free Tier 5-RPM limit is hit."""
    for attempt in range(5):
        try:
            return runnable.invoke(messages)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait_sec = 20
                print(f" Hit Free-Tier Rate Limit (5 req/min). Cooling down for {wait_sec}s...")
                time.sleep(wait_sec)
            else:
                raise e
    return runnable.invoke(messages)


def planner_node(state: DevinState) -> dict:
    """Node 1: Scans the workspace AST map and creates a step-by-step coding plan."""
    repo_map = get_repo_map.invoke({})

    prompt = (
        f"You are Devin-Zero, an autonomous software engineering planner.\n"
        f"Current Workspace Structure:\n{repo_map}\n\n"
        f"User Task: {state['task']}\n\n"
        "Create a concise 3-step implementation plan (including writing a pytest unit test file "
        "named test_*.py to verify the solution). Return each step on a new line."
    )
    response = _invoke_with_rate_limit_guard(llm, [HumanMessage(content=prompt)])

    raw_content = response.content
    if isinstance(raw_content, list):
        raw_text = "\n".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in raw_content
        )
    else:
        raw_text = str(raw_content)

    plan_steps = [line.strip() for line in raw_text.splitlines() if line.strip()]

    return {
        "repo_map": repo_map,
        "plan": plan_steps,
        "iterations": 0,
        "messages": [
            SystemMessage(
                content=(
                    "You are Devin-Zero, an autonomous coding agent. "
                    "IMPORTANT EFFICIENCY RULE: Minimize API turns by calling multiple tools in parallel "
                    "in a single response whenever possible (e.g., read all needed files at once, then "
                    "write/edit both the code file and the test_*.py file in one turn). "
                    "Once you have updated the code and tests, stop calling tools so the Tester node can run pytest."
                )
            ),
            HumanMessage(content=f"Task: {state['task']}\n\nPlan:\n" + "\n".join(plan_steps)),
        ],
    }


def coder_node(state: DevinState) -> dict:
    """Node 2: Writes new code or fixes bugs using file tools."""
    response = _invoke_with_rate_limit_guard(llm_with_tools, state["messages"])
    return {"messages": [response]}


def tester_node(state: DevinState) -> dict:
    """Node 3: Runs pytest inside the sandbox to verify if the code actually works."""
    test_result = run_bash_sandbox.invoke({"command": "pytest"})

    exit_code = 0 if "EXIT_CODE: 0" in test_result else 1
    current_iter = state.get("iterations", 0) + 1

    feedback_messages = []
    if exit_code != 0:
        feedback_messages.append(
            HumanMessage(
                content=(
                    f"Pytest failed (Iteration {current_iter}/5)!\n"
                    f"{test_result}\n\n"
                    "Analyze the traceback above and use edit_file or write_file to fix the bug in ONE turn."
                )
            )
        )

    return {
        "last_exit_code": exit_code,
        "test_output": test_result,
        "iterations": current_iter,
        "messages": feedback_messages,
    }