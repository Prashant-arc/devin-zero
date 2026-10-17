#  Devin-Zero: Autonomous Software Engineering Agent (Level 0)

**Devin-Zero** is a stateful, autonomous software engineering agent built with **LangGraph**, **Python AST**, and an isolated **Docker execution sandbox**. Inspired by [Devin AI](https://devin.ai/), it transforms natural language software specifications or bug reports into tested, working multi-file codebases through a closed-loop cycle.

---

## Project Scope (Level 0 Specification)

Unlike standard conversational coding assistants that only generate static code snippets, **Devin-Zero** operates inside an actual runtime environment with file-system and shell access:
1. **Multi-Step Task Decomposition:** Breaks complex user prompts into an ordered execution DAG/checklist.
2. **AST Repository Mapping:** Parses existing Python repositories via Abstract Syntax Trees (`ast`) to extract class/function signatures without overflowing LLM context windows.
3. **Surgical File Manipulation:** Reads, creates, and applies targeted search-and-replace diffs (`edit_file`) rather than rewriting entire files.
4. **Closed-Loop Self-Healing:** Automatically runs `pytest` / shell verification after every code edit, captures `stderr` tracebacks on failure, and iteratively patches bugs until tests pass.

---

##  System Architecture & LangGraph Workflow

Devin-Zero is modeled as a cyclical state machine using **LangGraph (`StateGraph`)**:

```mermaid
graph TD
    A[User Prompt / GitHub Issue] --> B[AST Repo Mapper]
    B --> C[Planner Node]
    C --> D[Coder Node: File Read/Write/Edit]
    D --> E[Sandbox Executor: Run Pytest / Bash]
    E --> F{Exit Code == 0?}
    F -- Yes --> G[Generate Git Diff & Final Summary]
    F -- No: stderr Captured --> H{Iterations < Max Retries?}
    H -- Yes --> I[Debugger / Reflection Node]
    I --> D
    H -- No --> J[Human-in-the-Loop Escalation]