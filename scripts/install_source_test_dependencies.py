# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Install source-test dependencies without building the editable package.

安装源码门禁依赖，但不构建 editable 包。
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROJECT_FILE = ROOT / "pyproject.toml"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cpp-requirements",
        type=Path,
        help="额外的 C++ 测试依赖文件",
    )
    return parser.parse_args(argv)


def _project_dependencies(project: dict[str, Any]) -> list[str]:
    metadata = project["project"]
    dependencies = list(metadata.get("dependencies", []))
    optional = metadata.get("optional-dependencies", {})
    dependencies.extend(optional.get("dev", []))
    result: list[str] = []
    for dependency in dependencies:
        normalized = dependency.split("#", 1)[0].strip()
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def _load_project() -> dict[str, Any]:
    import tomllib

    with PROJECT_FILE.open("rb") as stream:
        return tomllib.load(stream)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    dependencies = _project_dependencies(_load_project())
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        *dependencies,
    ]
    if args.cpp_requirements is not None:
        requirements = (ROOT / args.cpp_requirements).resolve()
        if not requirements.is_file():
            raise FileNotFoundError(f"requirements file not found: {requirements}")
        command.extend(["-r", str(requirements)])
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
