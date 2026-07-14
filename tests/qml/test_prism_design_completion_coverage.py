# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Prism Design public entry completion coverage tests."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QMLDIR_PATH = ROOT / "prismqml" / "PrismQML" / "qmldir"
EXAMPLES_MAIN = ROOT / "examples" / "main.qml"
PRISM_GALLERY_DIR = ROOT / "examples" / "pages"
PRISM_DOCS = (
    ROOT / "docs" / "index.zh.md",
    ROOT / "docs" / "guide" / "skins.zh.md",
    ROOT / "docs" / "guide" / "prism-design.zh.md",
    ROOT / "docs" / "guide" / "prism-design-implementation.zh.md",
)


def _registered_qml_types() -> list[str]:
    types = []
    for line in QMLDIR_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split()
        if parts[0] == "module":
            continue
        if parts[0] == "singleton":
            types.append(parts[1])
        else:
            types.append(parts[0])

    return types


def _prism_evidence_text() -> str:
    evidence_files = [
        *sorted((ROOT / "tests" / "qml").glob("test_prism_design*.py")),
        *sorted(PRISM_GALLERY_DIR.glob("Prism*.qml")),
        EXAMPLES_MAIN,
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in evidence_files)


def _contains_symbol(text: str, symbol: str) -> bool:
    pattern = rf"(?<![A-Za-z0-9_]){re.escape(symbol)}(?![A-Za-z0-9_])"
    return re.search(pattern, text) is not None


def test_prism_design_evidence_covers_every_public_qml_entry():
    registered_types = _registered_qml_types()
    assert len(registered_types) >= 170
    assert len(registered_types) == len(set(registered_types))

    evidence_text = _prism_evidence_text()
    missing = [
        type_name
        for type_name in registered_types
        if not _contains_symbol(evidence_text, type_name)
    ]

    assert missing == []


def test_prism_design_gallery_is_registered_in_gallery_shell():
    main_qml = EXAMPLES_MAIN.read_text(encoding="utf-8")
    assert '"Prism Design"' in main_qml
    assert "pages/PrismDesignPage.qml" in main_qml


def test_prism_design_chinese_docs_have_no_unresolved_todo():
    for path in PRISM_DOCS:
        doc = path.read_text(encoding="utf-8")
        assert "TODO" not in doc
