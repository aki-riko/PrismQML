# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Metric token namespace references. 度量 token 命名空间引用回归。"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
QML_ROOT = ROOT / "prismqml" / "PrismQML"
METRICS_PATH = QML_ROOT / "PrismEnums" / "Metrics.qml"
EXTERNAL_METRIC_SOURCES = {
    "shadow": METRICS_PATH.parent / "_internal" / "MetricsShadow.qml",
}
METRIC_NAMESPACES = {
    "duration": "duration",
    "motion": "motion",
    "demoMetrics": "demoMetrics",
    "zIndex": "zIndex",
    "opacityLevel": "opacity",
    "mask": "mask",
    "border": "border",
    "neo": "neo",
    "iconSize": "iconSize",
    "spacing": "spacing",
    "radius": "radius",
    "controlSize": "controlSize",
    "window": "window",
    "popupMetrics": "popup",
    "infoBarMetrics": "infoBar",
    "comboBoxMetrics": "comboBox",
    "searchMetrics": "search",
    "skeletonMetrics": "skeletonMetrics",
    "imageCropperDialogMetrics": "imageCropperDialog",
    "splashScreenMetrics": "splashScreen",
    "progressRingMetrics": "progressRing",
    "colorPickerMetrics": "colorPicker",
    "typography": "typography",
    "shadow": "shadow",
    "listIndicator": "listIndicator",
}


def _metric_properties(source: str, namespace: str, root_object: bool = False) -> set[str]:
    pattern = (
        r"\bQtObject\s*\{"
        if root_object
        else rf"readonly\s+property\s+QtObject\s+{re.escape(namespace)}\s*:\s*QtObject\s*{{"
    )
    declaration = re.search(pattern, source)
    assert declaration is not None, namespace

    opening_brace = source.find("{", declaration.start())
    depth = 0
    for index in range(opening_brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                body = source[opening_brace + 1 : index]
                return set(
                    re.findall(
                        r"readonly\s+property\s+\w+\s+(\w+)\s*:",
                        body,
                    )
                )
    raise AssertionError(f"Unclosed metric namespace: {namespace}")


@pytest.mark.parametrize("namespace, metrics_object", METRIC_NAMESPACES.items())
def test_metric_token_references_resolve_in_declared_namespace(
    namespace: str, metrics_object: str
):
    """所有度量引用必须在实际命名空间内声明，避免 undefined 传播为 NaN。"""
    source_path = EXTERNAL_METRIC_SOURCES.get(metrics_object, METRICS_PATH)
    declared = _metric_properties(
        source_path.read_text(encoding="utf-8"),
        metrics_object,
        root_object=source_path != METRICS_PATH,
    )
    reference_pattern = re.compile(rf"\bEnums\.{re.escape(namespace)}\.(\w+)")
    unresolved = []

    for qml_path in QML_ROOT.rglob("*.qml"):
        source = qml_path.read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
        code = re.sub(r"//[^\n]*", "", code)
        for match in reference_pattern.finditer(code):
            if match.group(1) not in declared:
                unresolved.append(
                    f"{qml_path.relative_to(ROOT).as_posix()}:{code.count(chr(10), 0, match.start()) + 1} "
                    f"Enums.{namespace}.{match.group(1)}"
                )

    assert unresolved == []
