# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。

"""High-contrast palette fallback in the token layer. 令牌层的高对比度回退。

Windows high-contrast themes maximise luminance separation, so the shared token
layer swaps strokes and text to absolute endpoints. These cases pin that branch
and prove the normal path is restored when the flag goes off.
"""

from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlApplicationEngine

from prismqml import register_types

PROBE = b"""import QtQuick
import PrismQML
Item {
    property bool highContrast: Enums.highContrast
    property color border: Enums.borderColor
    property color borderStrong: Enums.borderStrongColor
    property color divider: Enums.dividerColor
    property color foreground: Enums.foregroundColor
    property color disabledForeground: Enums.disabledForeground
}
"""


def _create(engine, source: bytes):
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent
    from PySide6.QtQuick import QQuickItem

    component = QQmlComponent(engine)
    component.setData(source, QUrl())
    errors = [error.toString() for error in component.errors()]
    assert component.status() == QQmlComponent.Status.Ready, errors
    instance = component.create()
    assert isinstance(instance, QQuickItem), errors
    return component, instance


def test_high_contrast_swaps_strokes_and_text_to_endpoints(qapp) -> None:
    """With the flag on, strokes reach white and text stops being faded."""
    from PySide6.QtCore import QCoreApplication

    from prismqml.python.core.theme import ThemeManager

    engine = QQmlApplicationEngine()
    register_types(engine)
    component, instance = _create(engine, PROBE)
    manager = ThemeManager()
    original = manager.highContrast
    try:
        manager.set_high_contrast(False)
        for _ in range(3):
            QCoreApplication.processEvents()

        assert instance.property("highContrast") is False
        # Baseline: the normal palette must not use the endpoint values.
        # 基线：常规调色板不得使用端点值。
        assert QColor(instance.property("border")) != QColor("#ffffff")

        manager.set_high_contrast(True)
        for _ in range(3):
            QCoreApplication.processEvents()

        assert instance.property("highContrast") is True
        assert QColor(instance.property("border")) == QColor("#ffffff")
        assert QColor(instance.property("borderStrong")) == QColor("#ffffff")
        assert QColor(instance.property("divider")) == QColor("#ffffff")
        assert QColor(instance.property("foreground")) == QColor("#ffffff")
        assert QColor(instance.property("disabledForeground")) == QColor("#c0c0c0")

        manager.set_high_contrast(False)
        for _ in range(3):
            QCoreApplication.processEvents()
        assert instance.property("highContrast") is False
        assert QColor(instance.property("border")) != QColor("#ffffff")
    finally:
        manager.set_high_contrast(original)
        instance.deleteLater()
