"""Import boundary test: control/ must NOT import forbidden modules.

AGENTS.md §2 rule 1: src/lanerush/control/ MUST NOT import traci, libsumo,
redis, psycopg, sqlalchemy, ultralytics, or anything from perception/,
store/, or sim/.
"""

from __future__ import annotations

import ast
import pathlib

FORBIDDEN_MODULES = {"traci", "libsumo", "redis", "psycopg", "sqlalchemy", "ultralytics"}
FORBIDDEN_PACKAGES = {"perception", "store", "sim"}

CONTROL_DIR = pathlib.Path("src/lanerush/control")


def test_no_forbidden_imports_in_control() -> None:
    """Every .py file in control/ must not import any forbidden module."""
    if not CONTROL_DIR.exists():
        # In some CI environments the cwd might differ
        alt = pathlib.Path(__file__).resolve().parents[2] / "src" / "lanerush" / "control"
        if alt.exists():
            control_dir = alt
        else:
            return  # skip if dir not found
    else:
        control_dir = CONTROL_DIR

    violations: list[str] = []

    for py_file in sorted(control_dir.glob("*.py")):
        source = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            violations.append(f"{py_file.name}: could not parse (syntax error)")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base = alias.name.split(".")[0]
                    if base in FORBIDDEN_MODULES:
                        violations.append(f"{py_file.name}: forbidden import '{alias.name}'")
                    for pkg in FORBIDDEN_PACKAGES:
                        if pkg in alias.name.split("."):
                            violations.append(
                                f"{py_file.name}: forbidden package import '{alias.name}'"
                            )

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                base = module.split(".")[0]
                if base in FORBIDDEN_MODULES:
                    violations.append(f"{py_file.name}: forbidden from-import '{module}'")
                parts = module.split(".")
                for pkg in FORBIDDEN_PACKAGES:
                    # Check if any part of the dotted name is a forbidden package
                    # but allow 'lanerush.models' etc. Only forbid lanerush.perception, etc.
                    if pkg in parts:
                        violations.append(
                            f"{py_file.name}: forbidden package from-import '{module}'"
                        )

    assert not violations, "Forbidden imports in control/:\n" + "\n".join(violations)
