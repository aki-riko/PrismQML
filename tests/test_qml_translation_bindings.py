# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML translation binding contracts. QML 翻译绑定合同。"""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
TRANSLATION_BINDING = re.compile(
    r"^\s*(?:property\s+\w+\s+\w+|text|title|label|emptyText)\s*:\s*"
    r"(?P<value>.*Translator\.tr\()"
)


def test_translated_qml_bindings_subscribe_to_language_version():
    violations = []
    for source_path in sorted(QML_ROOT.rglob("*.qml")):
        relative_path = source_path.relative_to(ROOT).as_posix()
        for line_number, line in enumerate(
            source_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            match = TRANSLATION_BINDING.search(line)
            if match and not match.group("value").lstrip().startswith("{"):
                violations.append(f"{relative_path}:{line_number}: {line.strip()}")

    assert violations == []
