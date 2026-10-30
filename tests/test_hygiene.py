"""
tests/test_hygiene.py
Automated Test Hygiene and Integrity Enforcer.
Enforces:
1. Zero unmocked network calls (requests, urllib, yfinance, genai.Client).
2. Zero write operations outside temporary directories.
3. Zero long sleeps (>0.05s) in automated test files.
4. AST assertion scan: every test method must contain at least one assertion.
5. Discovery completeness: test_terminal_quality.py is collected and zero test_*.py exist outside tests/.
"""

import ast
import os
import re
import unittest
from pathlib import Path


class TestSuiteHygiene(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).parent.parent.resolve()
        self.tests_dir = self.repo_root / "tests"

    def test_01_no_unmocked_network_in_tests(self):
        """Rule 1: No unmocked network calls in test files."""
        forbidden_patterns = [
            re.compile(r'\brequests\.(get|post|put|delete|patch)\('),
            re.compile(r'\burllib\.request\.urlopen\('),
            re.compile(r'\byf\.download\('),
            re.compile(r'\byf\.Ticker\('),
            re.compile(r'\bgenai\.Client\(')
        ]

        violations = []
        for py_file in self.tests_dir.glob("test_*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_no, line in enumerate(lines, 1):
                if "# noqa: network" in line:
                    continue
                # Skip mock setups and patch decorators
                if "@patch" in line or "patch(" in line or "mock" in line.lower():
                    continue

                for pat in forbidden_patterns:
                    if pat.search(line):
                        violations.append(f"{py_file.name}:{line_no} -> {line.strip()}")

        self.assertEqual(
            len(violations), 0,
            f"Unmocked network calls detected in test suite:\n" + "\n".join(violations)
        )

    def test_02_no_writes_outside_temp_in_tests(self):
        """Rule 2: No write operations to literal non-temporary file paths."""
        write_mode_pattern = re.compile(r'open\([^)]*["\'](w|wb|a|a\+|w\+)["\']')
        literal_path_pattern = re.compile(r'open\(["\'][^"\']+["\']')

        violations = []
        for py_file in self.tests_dir.glob("test_*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for open(...) calls
                    func = node.func
                    is_open = (isinstance(func, ast.Name) and func.id == "open")
                    if is_open:
                        # Check if write mode is specified
                        has_write_mode = False
                        for arg in node.args[1:]:
                            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                if any(m in arg.value for m in ("w", "a")):
                                    has_write_mode = True
                        for kw in node.keywords:
                            if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                                if any(m in kw.value.value for m in ("w", "a")):
                                    has_write_mode = True

                        if has_write_mode:
                            # Verify target is variable (e.g. self.temp_dir, fpath) not a string literal
                            target_arg = node.args[0] if node.args else None
                            if isinstance(target_arg, ast.Constant) and isinstance(target_arg.value, str):
                                violations.append(f"{py_file.name}:{node.lineno} writes to literal path '{target_arg.value}'")

        self.assertEqual(
            len(violations), 0,
            f"Write operations to literal non-temp paths found in test suite:\n" + "\n".join(violations)
        )

    def test_03_no_long_sleeps_in_tests(self):
        """Rule 3: No time.sleep longer than 0.05s in test files."""
        violations = []
        for py_file in self.tests_dir.glob("test_*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute) and node.func.attr == "sleep":
                        if isinstance(node.func.value, ast.Name) and node.func.value.id == "time":
                            if node.args and isinstance(node.args[0], ast.Constant):
                                duration = float(node.args[0].value)
                                if duration > 0.05:
                                    violations.append(f"{py_file.name}:{node.lineno} sleeps for {duration}s > 0.05s")

        self.assertEqual(
            len(violations), 0,
            f"Sleep calls > 0.05s detected in test files:\n" + "\n".join(violations)
        )

    def test_04_no_tests_without_assertions(self):
        """Rule 4: Every def test_* method must contain at least one assertion or assertRaises."""
        empty_tests = []
        total_tests = 0

        for py_file in self.tests_dir.glob("test_*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    total_tests += 1
                    has_assertion = False
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Assert):
                            has_assertion = True
                            break
                        if isinstance(subnode, ast.Call):
                            func = subnode.func
                            func_name = ""
                            if isinstance(func, ast.Name):
                                func_name = func.id
                            elif isinstance(func, ast.Attribute):
                                func_name = func.attr
                            if func_name.startswith("assert") or "assertRaises" in func_name:
                                has_assertion = True
                                break

                    if not has_assertion:
                        empty_tests.append(f"{py_file.name}::{node.name}")

        self.assertGreater(total_tests, 140, "Expected at least 140 test methods scanned")
        self.assertEqual(
            len(empty_tests), 0,
            f"Test methods with zero assertions found:\n" + "\n".join(empty_tests)
        )

    def test_05_discovery_completeness(self):
        """Rule 5: tests/test_terminal_quality.py is present and no test_*.py exists outside tests/."""
        terminal_quality_path = self.tests_dir / "test_terminal_quality.py"
        self.assertTrue(
            terminal_quality_path.exists(),
            "tests/test_terminal_quality.py must exist and be discovered"
        )

        # Check for any rogue test_*.py files outside tests/
        rogue_tests = []
        for root, dirs, files in os.walk(self.repo_root):
            # Exclude virtual environments and hidden git/cache folders
            if any(part.startswith(".") or part in ("venv", ".venv", "tests", "node_modules") for part in Path(root).parts):
                continue
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), self.repo_root)
                    rogue_tests.append(rel_path)

        self.assertEqual(
            len(rogue_tests), 0,
            f"Found test_*.py files outside tests/ directory:\n" + "\n".join(rogue_tests)
        )


if __name__ == "__main__":
    unittest.main()
