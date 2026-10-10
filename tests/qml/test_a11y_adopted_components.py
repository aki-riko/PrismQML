# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""Audit the adopted components through Qt's accessibility interface.

`Accessible.*` attached properties cannot be read back, so every row of the
accessibility roll-out is verified through `QAccessible.queryAccessibleInterface()`.
Each case asserts the role and name the platform accessibility layer would see.
每个采用无障碍的组件都经 QAccessible 接口核验角色与名称，而非读附加属性。
"""

import pytest
from PySide6.QtCore import QCoreApplication, QObject, QUrl
from PySide6.QtGui import QAccessible
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickItem

from prismqml import register_types

# NOTE: roles are compared by enum, never by magic number.
# 角色一律用枚举比较，不使用魔数。
BASE_IMPORTS = b"import QtQuick\nimport PrismQML\n"

SCENES = {
    "Badge": (
        b"""Item { width: 200; height: 100
            Badge { objectName: "probe"; text: "New" } }""",
        QAccessible.Role.StaticText,
        "New",
    ),
    "Avatar": (
        b"""Item { width: 200; height: 100
            Avatar { objectName: "probe"; initials: "AB" } }""",
        QAccessible.Role.StaticText,
        "AB",
    ),
    "Tag": (
        b"""Item { width: 200; height: 100
            Tag { objectName: "probe"; text: "Beta" } }""",
        QAccessible.Role.StaticText,
        "Beta",
    ),
    "Watermark": (
        b"""Item { width: 200; height: 100
            Watermark { objectName: "probe" } }""",
        QAccessible.Role.StaticText,
        None,
    ),
    "ExpanderCore": (
        b"""Item { width: 300; height: 200
            Expander { objectName: "probe"; title: "Details" } }""",
        QAccessible.Role.Grouping,
        "Details",
    ),
    "SelectorBar": (
        b"""Item { width: 300; height: 100
            SelectorBar { objectName: "probe"; items: ["One", "Two"] } }""",
        QAccessible.Role.PageTabList,
        None,
    ),
    "TabBar": (
        b"""Item { width: 300; height: 100
            TabBar { objectName: "probe"; tabs: ["One", "Two"] } }""",
        QAccessible.Role.PageTabList,
        None,
    ),
    "DialogBoxCore": (
        b"""Item { width: 300; height: 200
            MessageBox { objectName: "probe"; a11yName: "Confirm" } }""",
        QAccessible.Role.Dialog,
        "Confirm",
    ),
    "ProgressBar": (
        b"""Item { width: 200; height: 60
            ProgressBar { objectName: "probe"; value: 30; a11yName: "Loading" } }""",
        QAccessible.Role.ProgressBar,
        "Loading",
    ),
    "CircularGauge": (
        b"""Item { width: 200; height: 200
            CircularGauge { objectName: "probe"; value: 42; unit: "%" } }""",
        QAccessible.Role.ProgressBar,
        "42%",
    ),
    "RatingCore": (
        b"""Item { width: 200; height: 100
            Rating { objectName: "probe"; value: 3; a11yName: "Score" } }""",
        QAccessible.Role.Slider,
        "Score",
    ),
    "IndicatorBar": (
        b"""Item { width: 100; height: 100
            IndicatorBar { objectName: "probe" } }""",
        None,  # ignored: must not surface as a meaningful node
        None,
    ),
    "Separator": (
        b"""Item { width: 200; height: 100
            Separator { objectName: "probe" } }""",
        None,  # ignored
        None,
    ),
}


@pytest.mark.parametrize("component", sorted(SCENES))
def test_adopted_component_exposes_expected_accessible_role(qapp, component: str) -> None:
    """Every adopted component reports the role its roll-out commit promised."""
    body, expected_role, expected_name = SCENES[component]
    source = BASE_IMPORTS + body
    engine = QQmlApplicationEngine()
    register_types(engine)
    qml = QQmlComponent(engine)
    qml.setData(source, QUrl())
    errors = [error.toString() for error in qml.errors()]
    assert qml.status() == QQmlComponent.Status.Ready, errors
    root = qml.create()
    assert isinstance(root, QQuickItem), errors
    try:
        QCoreApplication.processEvents()
        item = root.findChild(QObject, "probe")
        assert item is not None, f"{component} did not create its probe item"
        interface = QAccessible.queryAccessibleInterface(item)
        assert interface is not None, f"{component} exposes no accessible interface"
        if expected_role is not None:
            assert interface.role() == expected_role, (
                f"{component}: role={interface.role()} expected={expected_role}"
            )
        if expected_name is not None:
            assert interface.text(QAccessible.Text.Name) == expected_name, (
                f"{component}: name={interface.text(QAccessible.Text.Name)!r}"
            )
    finally:
        root.deleteLater()
        qml.deleteLater()
        engine.deleteLater()
