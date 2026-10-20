from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages


class DevinState(TypedDict):
    """
    The shared memory clipboard passed between all LangGraph nodes.
    """
    # 1. Conversation & tool-call history (add_messages appends new messages instead of overwriting)
    messages: Annotated[List, add_messages]

    # 2. The original user goal (e.g., "Build a palindrome checker with unit tests")
    task: str

    # 3. AST blueprint of the workspace so the AI knows what files/functions exist
    repo_map: str

    # 4. Step-by-step checklist created by the Planner node
    plan: List[str]

    # 5. Terminal test results from the most recent pytest run
    last_exit_code: int
    test_output: str

    # 6. Loop counter so the AI stops after 5 tries instead of looping forever
    iterations: int