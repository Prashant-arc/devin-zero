from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from src.graph.state import DevinState
from src.graph.nodes import planner_node, coder_node, tester_node, CODER_TOOLS


def route_after_coder(state: DevinState) -> str:
    """
    Checks what the Coder node just did:
    - If the AI requested a file tool (read_file, write_file, edit_file), run the tool!
    - Once the AI is done editing files, send it to the Tester node to run pytest!
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "tester"


def route_after_tester(state: DevinState) -> str:
    """
    Checks the pytest result from Tester node:
    - If EXIT_CODE == 0 (all tests passed!), we are DONE -> END.
    - If we hit 5 failed attempts, stop so we don't loop forever -> END.
    - Otherwise, loop back to 'coder' node to fix the bug!
    """
    if state.get("last_exit_code") == 0:
        print("\n All pytest checks PASSED! Task complete.")
        return END
    if state.get("iterations", 0) >= 5:
        print("\n Reached max retries (5). Stopping loop.")
        return END
    print(f"\n Tests failed (Attempt {state.get('iterations')}/5). Sending traceback back to Coder...")
    return "coder"


def build_devin_graph():
    """Builds and compiles the cyclical Devin-Zero LangGraph state machine."""
    graph = StateGraph(DevinState)

    # 1. Add all nodes (workers)
    graph.add_node("planner", planner_node)
    graph.add_node("coder", coder_node)
    graph.add_node("tools", ToolNode(CODER_TOOLS))
    graph.add_node("tester", tester_node)

    # 2. Connect the arrows (edges)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "coder")

    # 3. Conditional arrow after Coder: either run file tools OR go to pytest tester
    graph.add_conditional_edges(
        "coder",
        route_after_coder,
        {
            "tools": "tools",
            "tester": "tester",
        },
    )

    # After a file tool runs (e.g. read_file or write_file), return output back to Coder
    graph.add_edge("tools", "coder")

    # 4. Conditional arrow after Tester: either END (if tests pass) OR loop back to Coder!
    graph.add_conditional_edges(
        "tester",
        route_after_tester,
        {
            "coder": "coder",
            END: END,
        },
    )

    return graph.compile()