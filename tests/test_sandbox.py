from src.tools.file_ops import write_file, read_file
from src.graph.workflow import build_devin_graph

# 1. Setup: Let's plant a buggy calculator inside agent_workspace!
buggy_code = """def add(a, b):
    return a - b  # Bug 1: subtracting instead of adding!

def multiply(a, b):
    return a + b  # Bug 2: adding instead of multiplying!
"""
write_file.invoke({"file_path": "calc.py", "content": buggy_code})
print("💣 Planted buggy 'calc.py' inside agent_workspace!\n")

# 2. Build the Devin-Zero Brain
app = build_devin_graph()

# 3. Give Devin-Zero a natural language task (Notice we just ask it in plain English!)
initial_state = {
    "task": "Inspect calc.py, fix the bugs in add() and multiply(), and make sure test_calc.py passes all unit tests.",
    "messages": [],
}

print("🚀 Starting Devin-Zero Autonomous Loop...\n")

# 4. Stream each node step so we can watch the AI think in real time!
for step in app.stream(initial_state):
    for node_name, node_output in step.items():
        print(f"👉 Finished Node: [{node_name.upper()}]")
        if "plan" in node_output:
            print("📋 AI Plan:")
            for p in node_output["plan"]:
                print(f"   {p}")
        if "test_output" in node_output:
            print("🧪 Pytest Result:")
            print(node_output["test_output"])
        print("-" * 50)

# 5. Let's inspect calc.py at the end to verify the AI actually fixed the code!
print("\n✨ FINAL FIXED calc.py INSIDE WORKSPACE:")
print(read_file.invoke({"file_path": "calc.py"}))