# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""QML translation binding contracts. QML 翻译绑定合同。"""

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
TRANSLATION_BINDING = re.compile(
    r"^\s*(?:property\s+\w+\s+\w+|text|title|label|emptyText)\s*:\s*"
    r"(?P<value>.*Translator\.tr\()"
)
TRANSLATION_CALL = re.compile(r'Translator\.tr\(["\']([^"\']+)["\']\)')
SUPPORTED_LANGUAGE_CODE = re.compile(r'\{\s*code:\s*"([^"]+)"')
TRANSLATION_PLACEHOLDER = re.compile(r"\{[^{}]+\}")
VISIBLE_TEXT_ASSIGNMENT = re.compile(
    r"(?:property\s+string\s+)?"
    r"(?:text|title|placeholderText|label|message|description|emptyText|"
    r"retryText|changeText|automaticText|themeColorsText|standardColorsText|"
    r"moreColorsText|loadingText|buttonText|confirmText|cancelText)\s*:"
    r"(?P<value>.*)"
)
STRING_LITERAL = re.compile(r'(["\'])(?P<value>(?:\\.|(?!\1).)*)\1')
HAN_CHARACTER = re.compile(r"[\u4e00-\u9fff]")
ALLOWED_HAN_PREFIXES = (
    "AutoUpdater:",
    "AutoUpdaterToastPresenter:",
    "[启动剖析]",
    "[懒加载诊断]",
)
ALLOWED_VISIBLE_LITERALS = {"RGB"}
NON_VISIBLE_EXPRESSION_MARKERS = (
    "typeof ",
    "Enums.trCount(",
    "role:",
    ".replace(",
    "_stepValue(",
)


def _qml_without_comments(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"//.*", "", source)


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


def test_public_qml_uses_external_translator_instead_of_qstr():
    violations = []
    for source_path in sorted(QML_ROOT.rglob("*.qml")):
        source = _qml_without_comments(source_path.read_text(encoding="utf-8"))
        if "qsTr(" in source:
            violations.append(source_path.relative_to(ROOT).as_posix())

    assert violations == []


def test_all_literal_translation_keys_exist_in_every_supported_language():
    used_keys = set()
    for source_path in sorted(QML_ROOT.rglob("*.qml")):
        if source_path.name == "Translator.qml":
            continue
        used_keys.update(
            TRANSLATION_CALL.findall(source_path.read_text(encoding="utf-8"))
        )

    translator_source = (QML_ROOT / "Translator.qml").read_text(encoding="utf-8")
    supported_languages = set(SUPPORTED_LANGUAGE_CODE.findall(translator_source))
    supported_languages.remove("auto")
    dictionary_paths = sorted((QML_ROOT / "i18n").glob("*.json"))

    assert {path.stem for path in dictionary_paths} == supported_languages

    english_dictionary = json.loads(
        (QML_ROOT / "i18n" / "en.json").read_text(encoding="utf-8")
    )
    for dictionary_path in dictionary_paths:
        dictionary = json.loads(dictionary_path.read_text(encoding="utf-8"))
        assert sorted(used_keys - set(dictionary)) == []
        assert set(dictionary) == set(english_dictionary)
        for key, value in dictionary.items():
            assert Counter(TRANSLATION_PLACEHOLDER.findall(value)) == Counter(
                TRANSLATION_PLACEHOLDER.findall(english_dictionary[key])
            ), f"{dictionary_path.name}:{key}"


def test_public_controls_have_no_hardcoded_visible_text_literals():
    violations = []
    controls_root = QML_ROOT / "controls"
    for source_path in sorted(controls_root.rglob("*.qml")):
        relative_path = source_path.relative_to(ROOT).as_posix()
        source = _qml_without_comments(source_path.read_text(encoding="utf-8"))
        for line_number, line in enumerate(source.splitlines(), start=1):
            for literal in STRING_LITERAL.finditer(line):
                value = literal.group("value")
                if HAN_CHARACTER.search(value) and not value.startswith(
                    ALLOWED_HAN_PREFIXES
                ):
                    violations.append(f"{relative_path}:{line_number}: {value}")

            assignment = VISIBLE_TEXT_ASSIGNMENT.search(line)
            if not assignment or "Translator.tr(" in line:
                continue
            if any(marker in line for marker in NON_VISIBLE_EXPRESSION_MARKERS):
                continue
            for literal in STRING_LITERAL.finditer(assignment.group("value")):
                value = literal.group("value")
                if (
                    value not in ALLOWED_VISIBLE_LITERALS
                    and len(re.findall(r"[A-Za-z]", value)) >= 2
                ):
                    violations.append(f"{relative_path}:{line_number}: {value}")

    assert violations == []
