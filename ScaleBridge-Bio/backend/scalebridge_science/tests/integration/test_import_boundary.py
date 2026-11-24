"""Import-boundary test: `scalebridge_science` must import only allowed dependencies."""

from __future__ import annotations

import ast
from pathlib import Path

ALLOWED = {
    "scalebridge_science",
    "__future__",
    "typing",
    "enum",
    "importlib",
    "math",
    "collections",
    "dataclasses",
    "json",
    "re",
    "warnings",
    "numbers",
    "decimal",
    "fractions",
    "functools",
    "itertools",
    "operator",
    "types",
    "numpy",
    "np",
    "scipy",
    "pandas",
    "pd",
    "pint",
    "pydantic",
}


def _top_level(module: str) -> str:
    return module.split(".")[0]


def test_import_boundary() -> None:
    root = Path(__file__).resolve().parents[2]  # scalebridge_science/
    bad: list[str] = []
    for py_file in root.rglob("*.py"):
        if "tests" in py_file.parts:
            continue
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = _top_level(alias.name)
                    if top not in ALLOWED:
                        bad.append(f"{py_file.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                if node.level and node.level > 0:
                    continue  # relative import inside package
                top = _top_level(node.module)
                if top not in ALLOWED:
                    bad.append(f"{py_file.name}: from {node.module} import ...")
    assert not bad, "Disallowed imports found:\n" + "\n".join(bad)
