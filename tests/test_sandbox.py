from src.tools.file_ops import write_file, edit_file
from src.tools.shell_exec import run_bash_sandbox

# 1. AI writes a buggy calculator (a - b instead of a + b)
write_file.invoke({"file_path": "calc.py", "content": "def add(a, b):\n    return a - b\n"})

# 2. AI writes a pytest file to test add(2, 3) == 5
test_code = """from calc import add

def test_add():
    assert add(2, 3) == 5
"""
write_file.invoke({"file_path": "test_calc.py", "content": test_code})

# 3. Run pytest on the buggy code (Should FAIL with EXIT_CODE: 1 and show the exact bug!)
print("=== FIRST RUN (WITH BUG) ===")
print(run_bash_sandbox.invoke({"command": "pytest test_calc.py"}))

# 4. Now fix the bug using edit_file and run pytest again (Should PASS with EXIT_CODE: 0!)
edit_file.invoke({"file_path": "calc.py", "target_code": "return a - b", "replacement_code": "return a + b"})

print("\n=== SECOND RUN (AFTER FIX) ===")
print(run_bash_sandbox.invoke({"command": "pytest test_calc.py"}))

from src.tools.repo_map import get_repo_map
print("\n" + get_repo_map.invoke({}))