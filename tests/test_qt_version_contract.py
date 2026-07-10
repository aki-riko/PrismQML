# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIN_QT_VERSION = (6, 9, 0)


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def _version_tuple(value: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in value.split("."))


def test_python_and_cmake_require_qt_69() -> None:
    pyproject = _read("pyproject.toml")
    cmake = _read("cpp/CMakeLists.txt")

    assert '"PySide6>=6.9.0"' in pyproject
    assert "set(PRISM_MIN_QT_VERSION 6.9)" in cmake
    assert "find_package(Qt6 ${PRISM_MIN_QT_VERSION} REQUIRED" in cmake


def test_ci_qt_versions_meet_the_minimum() -> None:
    workflows = (PROJECT_ROOT / ".github" / "workflows").glob("*.yml")
    versions = []
    for workflow in workflows:
        versions.extend(
            re.findall(
                r'(?m)^\s+version:\s*"(\d+\.\d+\.\d+)"',
                workflow.read_text(encoding="utf-8"),
            )
        )

    assert versions
    assert all(_version_tuple(version) >= MIN_QT_VERSION for version in versions)


def test_user_docs_publish_the_qt_69_contract() -> None:
    documents = (
        "README.md",
        "README.en.md",
        "docs/getting-started.zh.md",
        "docs/getting-started.en.md",
    )

    assert all("PySide6 6.9+" in _read(document) for document in documents)
