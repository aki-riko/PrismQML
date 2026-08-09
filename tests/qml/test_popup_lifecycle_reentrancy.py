# coding: utf-8
# SPDX-License-Identifier: MIT
# This file is part of PrismQML, licensed under MIT.
# 本文件是 PrismQML 的一部分，采用 MIT 许可证授权。
"""Popup lifecycle re-entrancy regressions. 弹层生命周期重入回归测试。"""

import pytest

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent
from PySide6.QtQuick import QQuickWindow

from prismqml import register_types

from _button_dropdown_prewarm_support import ROOT, _invoke, _pump, _wait_for


SCENE_URL = QUrl.fromLocalFile(
    str(ROOT / "tests" / "qml" / "popup-lifecycle-reentrancy.qml")
)
SCENE_SOURCE = b"""
import QtQuick
import PrismQML

Item {
    property bool closeDuringCaptureRelease: true
    property int closedCount: 0

    function openMenu() {
        popup.openAtControl(target)
    }

    width: 360
    height: 240

    Item {
        id: target
        x: 20
        y: 20
        width: 160
        height: 40
    }

    PopupWindowCore {
        id: popup
        objectName: "reentrantPopup"
        useQtPopupWindow: true

        function _releaseQtPopupCapture() {
            if (!closeDuringCaptureRelease) return
            closeDuringCaptureRelease = false
            popup.close()
        }

        onClosed: closedCount += 1
    }
}
"""


@pytest.fixture
def reentrant_scene(qapp):
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(error.toString() for error in errors)
    )
    engine.addImportPath(str(ROOT / "prismqml"))
    register_types(engine)
    component = QQmlComponent(engine)
    component.setData(SCENE_SOURCE, SCENE_URL)
    assert _wait_for(
        lambda: component.status() != QQmlComponent.Status.Loading
    )
    assert component.status() == QQmlComponent.Status.Ready, [
        error.toString() for error in component.errors()
    ]
    root = component.create(engine.rootContext())
    assert root is not None, [error.toString() for error in component.errors()]
    window = QQuickWindow()
    window.setWidth(360)
    window.setHeight(240)
    root.setParentItem(window.contentItem())
    window.show()
    window.requestActivate()
    _pump(30)
    try:
        yield root, window, warnings
    finally:
        root.setParentItem(None)
        window.hide()
        window.close()
        root.deleteLater()
        window.deleteLater()
        component.deleteLater()
        engine.deleteLater()
        _pump(20)


def test_reentrant_capture_release_cannot_publish_false_open(reentrant_scene):
    root, _window, warnings = reentrant_scene
    popup = root.findChild(type(root), "reentrantPopup")
    assert popup is not None

    _invoke(root, "openMenu")

    assert _wait_for(lambda: not popup.property("isOpen"))
    assert _wait_for(lambda: root.property("closedCount") == 1)
    assert not popup.property("_openRequested")
    assert _wait_for(lambda: not popup.property("isClosing"))
    assert not popup.property("_surfaceVisible")

    _invoke(root, "openMenu")
    assert _wait_for(
        lambda: popup.property("isOpen") and popup.property("_surfaceVisible")
    )
    # A delayed close callback from the previous surface must not close the
    # replacement surface. 旧 surface 的延迟关闭回调不能关闭已重开的新 surface。
    _invoke(popup, "_handleSurfaceClosed")
    assert popup.property("isOpen")
    assert popup.property("_surfaceVisible")
    assert root.property("closedCount") == 1
    assert warnings == []
